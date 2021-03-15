from pathlib import Path
from typing import Union, List, Tuple, Any

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
        for c in children:
            if type(c) == Communication:
                communications.append(c)
            elif type(c) == Typedef:
                typedefs.append(c)
            elif type(c) == Constant:
                constants.append(c)
            else:
                raise ValueError(f"Unknown type: {type(c)}")
        return File(communications, typedefs, constants)

    @staticmethod
    def block(children: Children):
        check_type(children[0], [Communication, Typedef, Constant])
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
        check_type(children[token_idx], ["IDENTIFIER", "WILDCARD"])
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
        return ReferenceType(children[0].value)

    @staticmethod
    def typedef_primitive(children: Children):
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], PrimitiveType)
        return Typedef(children[1].value, children[2])

    @staticmethod
    def alias(children: Children):
        check_type(children[1], "IDENTIFIER")
        check_type(children[2], ReferenceType)
        return Typedef(children[0].value, children[1])

    @staticmethod
    def typedef_enum(children: Children):
        check_type(children[1], EnumType)
        return Typedef(children[1].name, children[1])

    @staticmethod
    def typedef_object(children: Children):
        check_type(children[1], ObjectType)
        return Typedef(children[1].name, children[1])


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
