from pathlib import Path
from typing import Union

from lark import Lark, Tree, Token, Visitor
from lark.indenter import Indenter

from .intermediate_representation import *


class GrammarIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_BEGIN"
    DEDENT_type = "_END"
    tab_len = 4


class ChildStream:
    EOF = "EOF"

    def __init__(self, node: Tree):
        self.children = node.children
        self.next_idx = 0

    def peek(self) -> Union[Token, str]:
        if self.next_idx >= len(self.children):
            return self.EOF
        return self.children[self.next_idx]

    def next(self) -> Union[Token, str]:
        if self.next_idx >= len(self.children):
            return self.EOF
        self.next_idx += 1
        return self.children[self.next_idx - 1]

    def skip(self, n=1):
        self.next_idx += n


type_mapping = {
    "int": IntType,
    "str": StringType,
    "float": FloatType,
    "bool": BooleanType,
    "object": ObjectType,
    "enum": EnumType,
    "any": AnyType
}


class MyTransformer(Visitor):

    def __init__(self):
        self.stack = []

    def file(self, node: Tree):
        communications = []
        global_types = []
        constants = []
        for n in node.children:
            if isinstance(n.transformed, Communication):
                communications.append(n.transformed)
            elif isinstance(n.transformed, TypeDefinition):
                global_types.append(n.transformed)
            elif isinstance(n.transformed, Constant):
                constants.append(n.transformed)
        node.transformed = File(communications, global_types, constants)

    def block(self, node: Tree):
        node.transformed = node.children[0].transformed

    def constant(self, node: Tree):
        node.transformed = Constant(node.children[0].value, node.children[1].value)

    def communication(self, node: Tree):
        name = node.children[0].value
        attributes = node.children[1].transformed
        requests = node.children[2].transformed
        node.transformed = Communication(name, attributes, requests)

    def const_attributes(self, node: Tree):
        attributes = []
        for n in node.children:
            attributes.append(n.transformed)
        node.transformed = attributes

    def requests(self, node: Tree):
        reqs = []
        for r in node.children:
            reqs.append(r.transformed)
        node.transformed = reqs

    def request(self, node: Tree):
        method = node.children[0].value
        attributes = node.children[1].transformed
        parameters = node.children[2].transformed
        responses = node.children[3].transformed
        node.transformed = Request(method, parameters, responses, attributes)

    def request_def(self, node: Tree):
        body = None
        if len(node.children) == 2:
            body = node.children[1].transformed
        node.transformed = body

    def response_def(self, node: Tree):
        responses = []
        for n in node.children[1:]:
            responses.append(n.transformed)
        node.transformed = responses

    def response(self, node: Tree):
        status_code = int(node.children[0].value)
        body = None
        if len(node.children) == 2:
            body = node.children[1].transformed
        node.transformed = Response(status_code, body)

    def body(self, node: Tree):
        attributes = []
        for n in node.children:
            attributes.append(n.transformed)
        node.transformed = Body(attributes)

    def attribute(self, node: Tree):
        tokens = ChildStream(node)
        is_optional = False
        if tokens.peek().type == "OPTIONAL":
            is_optional = True
            tokens.next()
        is_wildcard = False
        if tokens.peek().type == "WILDCARD":
            is_wildcard = True
        name = tokens.next().value
        is_array = False
        if tokens.peek().type == "ARRAY":
            is_array = True
            tokens.next()
        tokens.skip()  # skip separator
        type_definition = tokens.next().transformed
        node.transformed = Attribute(name, type_definition, is_optional, is_array, is_wildcard)

    def type_definition(self, node: Tree):
        tokens = ChildStream(node)
        type_type = tokens.next().transformed
        name = None
        token = tokens.peek()
        if token != ChildStream.EOF and token.type == "IDENTIFIER":
            name = tokens.next().value
        data = None
        if tokens.peek() != ChildStream.EOF:
            body = tokens.next().transformed
            data = self._body_to_type(body, type_type)
        if type_type == EnumType:
            data = node.children[0].inline_data
        if type_type == ReferenceType:
            data = node.children[0].inline_data
        node.transformed = TypeDefinition(type_type, data, name)

    def type(self, node):
        token = node.children[0]
        if isinstance(token, Token):  # PRIMITIVE
            type_type = type_mapping[token.value]
            node.transformed = type_type
        elif token.data == "enum":
            node.transformed = EnumType
            node.inline_data = token.transformed
        elif token.data == "global_type":
            node.transformed = ReferenceType
            node.inline_data = token.transformed

    def enum(self, node):
        values = []
        for n in node.children:
            values.append(n.value)
        node.transformed = EnumType(values)

    def global_type(self, node):
        node.transformed = ReferenceType(node.children[0].value)

    def typedef(self, node: Tree):
        type_type = type_mapping[node.children[1].value]
        name = node.children[2].value
        data = self._body_to_type(node.children[3].transformed, type_type)
        node.transformed = TypeDefinition(type_type, data, name)

    def simple_attribute(self, node: Tree):
        key = node.children[0].value
        value = node.children[2].value
        node.transformed = SimpleAttribute(key, value)

    def _body_to_type(self, body: Body, type_type: type):
        return ObjectType(body)  # TODO


def parse(text: str) -> File:
    if text[-1] != "\n":
        text += "\n"
    grammar_file = Path(__file__).parent.joinpath("grammar.lark")
    parser = Lark.open(grammar_file, parser="lalr", postlex=GrammarIndenter())
    parse_tree = parser.parse(text)
    transformer = MyTransformer()
    res = transformer.visit(parse_tree)
    return res.transformed
