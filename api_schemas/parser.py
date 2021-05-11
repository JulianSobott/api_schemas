from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Tuple, Any, Dict
import difflib

from lark import Lark, Tree, Token, Visitor, Transformer
from lark.indenter import Indenter

from .error_handling import on_syntax_error, Context, Position, error, ErrorLevel
from .intermediate_representation import *

# globals
sym_table: Dict[str, Type]
ctx: Context

# types
AllTypes = Type.__args__
Child = Union[Token, Any]
Children = List[Child]


def parse(text: str) -> File:
    global sym_table, ctx
    sym_table = {}

    if text[-1] != "\n":
        text += "\n"
    grammar_file = Path(__file__).parent.joinpath("grammar.lark")
    parser = Lark.open(grammar_file, parser="lalr", postlex=GrammarIndenter())
    ctx = Context("TODO: FILENAME", text, None)
    parse_tree = parser.parse(text, on_error=lambda err: on_syntax_error(err, ctx))
    transformer = TransformToIR()
    res = transformer.transform(parse_tree)
    return res


primitive_type_mapping = {
    "int": Primitive.Int,
    "str": Primitive.Str,
    "float": Primitive.Float,
    "bool": Primitive.Bool,
    "any": Primitive.Any
}


class TransformToIR(Transformer):

    @staticmethod
    def file(children: Children) -> File:
        communications = []
        typedefs = []
        constants = []
        ws_events = None
        for c in children:
            if type(c) == Communication:
                communications.append(c)
            elif type(c) == Typedef:
                typedefs.append(c)
            elif type(c) == Constant:
                constants.append(c)
            elif type(c) == WSEvents:
                ws_events = c
            else:
                raise ValueError(f"Unknown type: {type(c)}")
        return File(communications, typedefs, constants, ws_events)

    @staticmethod
    def block(children: Children) -> Union[Communication, Typedef, Constant, WSEvents]:
        check_type(children[0], [Communication, Typedef, Constant, WSEvents])
        return children[0]

    @staticmethod
    def constant(children: Children) -> Constant:
        check_type(children[0], "IDENTIFIER")
        check_type(children[1], "CONST_VALUE")
        return Constant(children[0].value, children[1].value)

    @staticmethod
    def communication(children: Children) -> Communication:
        name = children[0].value
        attributes = []
        requests = []
        for c in children[1:]:
            if type(c) == Constant:
                attributes.append(c)
            else:
                check_type(c, Request)
                requests.append(c)
        return Communication(name, attributes, requests)

    @staticmethod
    def request(children: Children) -> Request:
        method = children[0].value
        parameters = children[1]
        responses = children[2]
        return Request(method, parameters, responses)

    @staticmethod
    def request_def(children: Children) -> List[Union[Constant, TypeAttribute]]:
        if len(children) == 2:
            return children[1]
        return []   # no body

    @staticmethod
    def response_def(children: Children) -> List[Response]:
        return children[1:]

    @staticmethod
    def response(children: Children) -> Response:
        code = int(children[0].value)   # TODO: check + error message if fail
        attributes = children[1] if len(children) == 2 else []
        return Response(code, attributes)

    @staticmethod
    def body(children: Children) -> List[Union[Constant, TypeAttribute]]:
        check_children(children, [Constant, TypeAttribute])
        return children

    @staticmethod
    def attribute(children: Children) -> TypeAttribute:
        is_optional = False
        is_array = False
        token_idx = 0
        if isinstance(children[token_idx], Token) and children[token_idx].type == "OPTIONAL":
            is_optional = True
            token_idx += 1
        check_type(children[token_idx], ["IDENTIFIER", "WILDCARD", "ARRAY"])
        if children[token_idx].type == "ARRAY":
            name = ""   # json is an array
            is_wildcard = False
        else:
            name = children[token_idx].value
            is_wildcard = children[token_idx].type == "WILDCARD"
            token_idx += 1
        if isinstance(children[token_idx], Token) and children[token_idx].type == "ARRAY":
            is_array = True
            token_idx += 1
        token_idx += 1  # SEPARATOR
        check_type(children[token_idx], AllTypes)
        return TypeAttribute(name, children[token_idx], is_optional, is_array, is_wildcard)

    @staticmethod
    def type(children: Children) -> Type:
        check_type(children[0], AllTypes)
        return children[0]

    @staticmethod
    def primitive(children: Children) -> PrimitiveType:
        check_type(children[0], "PRIMITIVE")
        check_children(children[1:], Constant)
        return PrimitiveType(primitive_type_mapping[children[0].value], children[1:])

    @staticmethod
    def enum(children: Children) -> EnumType:
        check_type(children[0], "IDENTIFIER")
        check_children(children[1:], "IDENTIFIER")
        name = children[0].value
        values = [c.value for c in children[1:]]
        return EnumType(name, values)

    @staticmethod
    def object(children: Children) -> ObjectType:
        check_type(children[0], "IDENTIFIER")
        name = children[0].value
        values: List[Constant] = []
        attributes: List[TypeAttribute] = []
        for c in children[1]:
            if isinstance(c, Constant):
                values.append(c)
            else:
                check_type(c, TypeAttribute)
                attributes.append(c)
        return ObjectType(name, values, attributes)

    @staticmethod
    def global_type(children: Children) -> Type:
        check_type(children[0], "IDENTIFIER")
        name = children[0].value
        if name not in sym_table:
            t = children[0]
            matches = difflib.get_close_matches(name, sym_table.keys(), 1)
            help_msg = "A type must be defined before it can be referenced."
            if matches:
                help_msg = f"Did you mean: {matches[0]}"
            pos = Position(t.line, t.column, t.line, t.column + len(t.value))
            error(ErrorLevel.ERROR, ctx.with_pos(pos), f"NameError: name '{name} is not defined", help_msg)
        return sym_table[name]

    @staticmethod
    def typedef_primitive(children: Children) -> Typedef:
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], PrimitiveType)
        sym_table[children[1].value] = children[2]
        return Typedef(children[1].value, children[2])

    @staticmethod
    def alias(children: Children) -> Typedef:
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], AllTypes)
        name = children[1].value
        # TODO: new child with new name?
        sym_table[name] = children[2]
        return Typedef(name, sym_table[name])

    @staticmethod
    def typedef_enum(children: Children) -> Typedef:
        check_type(children[1], EnumType)
        sym_table[children[1].name] = children[1]
        return Typedef(children[1].name, children[1])

    @staticmethod
    def typedef_object(children: Children) -> Typedef:
        check_type(children[1], ObjectType)
        sym_table[children[1].name] = children[1]
        return Typedef(children[1].name, children[1])

    @staticmethod
    def ws_events(children: Children) -> WSEvents:
        check_children(children[2], WSEvent)
        check_children(children[4], WSEvent)
        client_events = children[2]
        server_events = children[4]
        return WSEvents(client_events, server_events)

    @staticmethod
    def ws_events_list(children: Children) -> List[WSEvent]:
        check_children(children, WSEvent)
        return children

    @staticmethod
    def ws_event(children: Children) -> WSEvent:
        check_type(children[0], "IDENTIFIER")
        check_type(children[1], list)
        return WSEvent(children[0].value, children[1])


class GrammarIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_BEGIN"
    DEDENT_type = "_END"
    tab_len = 4


def check_type(child: Child, type_: Union[Union[str, type], List[Union[str, type]]]):
    """Helper method for assertions"""
    try:
        0 in type_  # check if is iterable
    except TypeError:
        type_ = [type_]
    if isinstance(child, Token):
        assert child.type in type_, f"Expected: '{type_}' got '{child.type}'"
    else:
        assert type(child) in type_, f"Expected: '{type_}' got '{type(child)}'"


def check_children(children: Children, type_: Union[Union[str, type], List[Union[str, type]]]):
    """Helper method for assertions"""
    _ = [check_type(c, type_) for c in children]
