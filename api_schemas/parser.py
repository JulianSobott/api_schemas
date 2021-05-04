from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Tuple, Any, Dict
import difflib

from lark import Lark, Tree, Token, Visitor, Transformer
from lark.indenter import Indenter

from .error_handling import on_syntax_error, Context, Position, error, ErrorLevel
from .intermediate_representation import *

global_types: Dict[str, Type] = {}   # store all objects for resolving
reference_types: List['TempReferenceType'] = []    # references that must be resolved after parsing


def parse(text: str) -> File:
    global global_types, reference_types
    global_types = {}
    reference_types = []

    if text[-1] != "\n":
        text += "\n"
    grammar_file = Path(__file__).parent.joinpath("grammar.lark")
    parser = Lark.open(grammar_file, parser="lalr", postlex=GrammarIndenter())
    ctx = Context("TODO: FILENAME", text, None)
    parse_tree = parser.parse(text, on_error=lambda err: on_syntax_error(err, ctx))
    transformer = TransformToIR()
    res = transformer.transform(parse_tree)
    resolve_types(ctx)
    return res


primitive_type_mapping = {
    "int": Primitive.Int,
    "str": Primitive.Str,
    "float": Primitive.Float,
    "bool": Primitive.Bool,
    "any": Primitive.Any
}

Child = Union[Token, Any]
Children = List[Child]


class TransformToIR(Transformer):

    @staticmethod
    def file(children: Children):
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
    def block(children: Children):
        check_type(children[0], [Communication, Typedef, Constant, WSEvents])
        return children[0]

    @staticmethod
    def constant(children: Children):
        check_type(children[0], "IDENTIFIER")
        check_type(children[1], "CONST_VALUE")
        return Constant(children[0].value, children[1].value)

    @staticmethod
    def communication(children: Children):
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
    def request(children: Children):
        method = children[0].value
        parameters = children[1]
        responses = children[2]
        return Request(method, parameters, responses)

    @staticmethod
    def request_def(children: Children):
        if len(children) == 2:
            return children[1]
        return []   # no body

    @staticmethod
    def response_def(children: Children):
        return children[1:]

    @staticmethod
    def response(children: Children):
        code = int(children[0].value)   # TODO: check + error message if fail
        attributes = children[1] if len(children) == 2 else []
        return Response(code, attributes)

    @staticmethod
    def body(children: Children):
        check_children(children, [Constant, TypeAttribute])
        return children

    @staticmethod
    def attribute(children: Children):
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
        check_type(children[token_idx], [ObjectType, EnumType, ReferenceType, PrimitiveType])
        return TypeAttribute(name, children[token_idx], is_optional, is_array, is_wildcard)

    @staticmethod
    def type(children: Children):
        check_type(children[0], [PrimitiveType, EnumType, ReferenceType, ObjectType])
        return children[0]

    @staticmethod
    def primitive(children: Children):
        check_type(children[0], "PRIMITIVE")
        check_children(children[1:], Constant)
        return PrimitiveType(primitive_type_mapping[children[0].value], children[1:])

    @staticmethod
    def enum(children: Children):
        check_type(children[0], "IDENTIFIER")
        check_children(children[1:], "IDENTIFIER")
        name = children[0].value
        values = [c.value for c in children[1:]]
        return EnumType(name, values)

    @staticmethod
    def object(children: Children):
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
    def global_type(children: Children):
        check_type(children[0], "IDENTIFIER")
        name = children[0].value
        # reference is resolved after everything is parsed
        # this way the order of declaration is irrelevant
        t = children[0]

        reference_type = ReferenceType(name, None)
        reference_types.append(
            TempReferenceType(reference_type, Position(t.line, t.column, t.line, t.column + len(t.value))))
        return reference_type

    @staticmethod
    def typedef_primitive(children: Children):
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], PrimitiveType)
        global_types[children[1].value] = children[2]
        return Typedef(children[1].value, children[2])

    @staticmethod
    def alias(children: Children):
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], ReferenceType)
        return Typedef(children[1].value, children[2])

    @staticmethod
    def typedef_enum(children: Children):
        check_type(children[1], EnumType)
        global_types[children[1].name] = children[1]
        return Typedef(children[1].name, children[1])

    @staticmethod
    def typedef_object(children: Children):
        check_type(children[1], ObjectType)
        global_types[children[1].name] = children[1]
        return Typedef(children[1].name, children[1])

    @staticmethod
    def ws_events(children: Children):
        check_children(children[2], WSEvent)
        check_children(children[4], WSEvent)
        client_events = children[2]
        server_events = children[4]
        return WSEvents(client_events, server_events)

    @staticmethod
    def ws_events_list(children: Children):
        check_children(children, WSEvent)
        return children

    @staticmethod
    def ws_event(children: Children):
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
    if not type(type_) == list:
        type_ = [type_]
    if isinstance(child, Token):
        assert child.type in type_, f"Expected: '{type_}' got '{child.type}'"
    else:
        assert type(child) in type_, f"Expected: '{type_}' got '{type(child)}'"


def check_children(children: Children, type_: Union[Union[str, type], List[Union[str, type]]]):
    """Helper method for assertions"""
    _ = [check_type(c, type_) for c in children]


def resolve_types(ctx: Context):
    for ref in reference_types:
        if ref.ref.name not in global_types:
            matches = difflib.get_close_matches(ref.ref.name, global_types.keys(), 1)
            help_msg = "A type must be defined to reference it."
            if matches:
                help_msg = f"Did you mean: {matches[0]}"
            error(ErrorLevel.ERROR, ctx.with_pos(ref.pos), f"NameError: name '{ref.ref.name} is not defined", help_msg)
        ref.ref.reference = global_types[ref.ref.name]


@dataclass
class TempReferenceType:
    ref: ReferenceType
    pos: Position
