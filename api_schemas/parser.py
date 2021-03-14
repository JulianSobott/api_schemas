from pathlib import Path
from typing import Union, List, Tuple

from lark import Lark, Tree, Token, Visitor, Transformer
from lark.indenter import Indenter

from .intermediate_representation import *


def parse(text: str) -> File:
    if text[-1] != "\n":
        text += "\n"
    grammar_file = Path(__file__).parent.joinpath("grammar.lark")
    parser = Lark.open(grammar_file, parser="lalr", postlex=GrammarIndenter())
    parse_tree = parser.parse(text)
    transformer = TransformToIR()
    res = transformer.transform(parse_tree)
    return res


type_mapping = {
    "int": IntType,
    "str": StringType,
    "float": FloatType,
    "bool": BooleanType,
    "object": ObjectType,
    "enum": EnumType,
    "any": AnyType
}

Child = Union[_ALL_CLASSES, Token]
Children = List[Child]


def build_type(type_: Union[Token, EnumType, ReferenceType], body: List[TypeAttribute]) -> Tuple[type, Type]:
    if body:
        body = body[0]
    if type(type_) == EnumType:
        return EnumType, type_
    if type(type_) == ReferenceType:
        return ReferenceType, type_
    ir_type = type_mapping[type_.value]
    if ir_type == ObjectType:
        return ir_type, ObjectType(body)
    elif ir_type in [StringType, BooleanType, AnyType, IntType, FloatType]:
        return ir_type, ir_type()
    else:
        raise ValueError(f"Unknown type: {ir_type}")


class TransformToIR(Transformer):

    @staticmethod
    def file(children: Children):
        communications = []
        typedefs = []
        constants = []
        for c in children:
            if type(c) == Communication:
                communications.append(c)
            elif type(c) == TypeDefinition:
                typedefs.append(c)
            elif type(c) == Constant:
                constants.append(c)
            else:
                raise ValueError(f"Unknown type: {type(c)}")
        return File(communications, typedefs, constants)

    @staticmethod
    def block(children: Children):
        check_type(children[0], [Communication, TypeDefinition, Constant])
        return children[0]

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
                attributes.append(c)
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
        check_children(children, TypeAttribute)
        return children

    @staticmethod
    def attribute(children: Children):
        is_optional = False
        is_array = False
        token_idx = 0
        if isinstance(children[token_idx], Token) and children[token_idx].type == "OPTIONAL":
            is_optional = True
            token_idx += 1
        check_type(children[token_idx], ["IDENTIFIER", "WILDCARD"])
        name = children[token_idx].value
        is_wildcard = children[token_idx].type == "WILDCARD"
        token_idx += 1
        if isinstance(children[token_idx], Token) and children[token_idx].type == "ARRAY":
            is_array = True
            token_idx += 1
        token_idx += 1  # SEPARATOR
        check_type(children[token_idx], TypeDefinition)
        return TypeAttribute(name, children[token_idx], is_optional, is_array, is_wildcard)

    @staticmethod
    def type_definition(children: Children):
        check_type(children[0], ["PRIMITIVE", EnumType, ReferenceType])
        idx = 1
        name = None
        if len(children) > idx and isinstance(children[idx], Token) and children[idx].type == "IDENTIFIER":
            name = children[idx].value
            idx += 1
        ir_type, data = build_type(children[0], children[idx:])
        return TypeDefinition(ir_type, data, name)

    @staticmethod
    def typedef(children: Children):
        check_type(children[1], "PRIMITIVE")
        check_type(children[2], "IDENTIFIER")
        check_type(children[3], list)    # List[TypeAttribute]
        ir_type, data = build_type(children[1], children[3:])
        return TypeDefinition(ir_type, data, children[2].value)

    @staticmethod
    def type(children: Children):
        return children[0]

    @staticmethod
    def enum(children: Children):
        values = [c.value for c in children]
        return EnumType(values)

    @staticmethod
    def global_type(children: Children):
        return ReferenceType(children[0].value)

    @staticmethod
    def constant(children: Children):
        check_type(children[0], "IDENTIFIER")
        check_type(children[1], "CONST_VALUE")
        return Constant(children[0].value, children[1].value)


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
