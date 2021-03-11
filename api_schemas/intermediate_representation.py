import re
from dataclasses import dataclass
from typing import List, Union

__all__ = ["ObjectType", "IntType", "FloatType", "StringType", "BooleanType", "EnumType", "ReferenceType", "AnyType",
           "TypeDefinition", "Body", "File", "Attribute", "SimpleAttribute", "Communication", "Constant", "Request",
           "Response"]


@dataclass
class ObjectType:
    body: 'Body'


@dataclass
class IntType:
    minimum: int = None
    maximum: int = None


@dataclass
class FloatType:
    minimum: float = None
    maximum: float = None


@dataclass
class StringType:
    pass


@dataclass
class BooleanType:
    pass


@dataclass
class EnumType:
    values: List[str]


@dataclass
class AnyType:
    pass


@dataclass
class ReferenceType:
    name: str


@dataclass
class TypeDefinition:
    type_type: type
    data: Union[ObjectType, IntType, FloatType, StringType, BooleanType, EnumType, ReferenceType]
    name: str = None


@dataclass
class Attribute:
    name: str
    type_definition: TypeDefinition
    is_optional: bool = False
    is_array: bool = False
    is_wildcard: bool = False


@dataclass
class Body:
    attributes: List[Attribute]


@dataclass
class Response:
    code: int
    body: Body


@dataclass
class Request:
    method: str
    parameters: Body
    responses: List[Response]
    attributes: List["SimpleAttribute"]


@dataclass
class Communication:
    name: str
    attributes: List["SimpleAttribute"]
    requests: List[Request]


@dataclass
class Constant:
    name: str
    value: str  # For now only string constants


@dataclass
class File:
    communications: List[Communication]
    global_types: List[TypeDefinition]
    constants: List[Constant]


@dataclass
class SimpleAttribute:
    key: str
    value: str


def get_simple_attribute(attributes: List[SimpleAttribute], name: str, default=None):
    for a in attributes:
        if a.key == name:
            return a.value
    return default


def url_params_from_uri(uri: str) -> List[str]:
    return re.findall("<([^>]+)>", uri)
