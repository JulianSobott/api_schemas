import re
from dataclasses import dataclass
from typing import List, Union

__all__ = ["ObjectType", "IntType", "FloatType", "StringType", "BooleanType", "EnumType", "ReferenceType", "AnyType",
           "TypeDefinition", "File", "TypeAttribute", "SimpleAttribute", "Communication", "Constant", "Request",
           "Response"]


@dataclass
class ObjectType:
    attributes: List["TypeAttribute"]


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


Type = Union[ObjectType, IntType, FloatType, StringType, BooleanType, EnumType, ReferenceType, AnyType]


@dataclass
class TypeDefinition:
    type: type
    data: Type
    name: str = None


@dataclass
class TypeAttribute:
    name: str
    type_definition: TypeDefinition
    is_optional: bool = False
    is_array: bool = False
    is_wildcard: bool = False


@dataclass
class SimpleAttribute:
    name: str
    value: str


@dataclass
class Response:
    code: int
    attributes: List[TypeAttribute]


@dataclass
class Request:
    method: str
    parameters: List[TypeAttribute]
    responses: List[Response]


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


def get_simple_attribute(attributes: List[SimpleAttribute], name: str, default=None):
    for a in attributes:
        if a.key == name:
            return a.value
    return default


def url_params_from_uri(uri: str) -> List[str]:
    return re.findall("<([^>]+)>", uri)
