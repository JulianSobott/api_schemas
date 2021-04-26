import re
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from api_schemas import Primitive, PrimitiveType


class NameTypes(Enum):
    ATTRIBUTE = 0
    CLASS = 1
    METHOD = 2
    CONSTANT = 3
    ENUM_VALUE = 4
    ENUM_NAME = 5


class CaseConverter:

    CAMEL = 0   # camelCase
    SNAKE = 1   # snake_case
    PASCAL = 2  # PascalCase
    UPPER = 3

    @staticmethod
    def convert_unknown(name: str, target: int) -> str:
        return CaseConverter.convert(name, CaseConverter.basic_match(name), target)

    @staticmethod
    def convert(name: str, source: int, target: int):
        if target == source:
            return name
        if len(name) == 1:
            if target in [CaseConverter.CAMEL, CaseConverter.SNAKE]:
                return name.lower()
            else:
                return name.upper()

        if source == CaseConverter.SNAKE:
            if target == CaseConverter.PASCAL:
                return ''.join(word.title() for word in name.split('_'))
            elif target == CaseConverter.CAMEL:
                return name[0].lower() + ''.join(word.title() for word in name[1:].split('_'))
            elif target == CaseConverter.UPPER:
                return name.upper()
        elif source == CaseConverter.CAMEL:
            if target == CaseConverter.PASCAL:
                return name[0].upper() + name[1:]
            elif target == CaseConverter.SNAKE:
                return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            elif target == CaseConverter.UPPER:
                return CaseConverter.convert(name, source, CaseConverter.SNAKE).upper()
        elif source == CaseConverter.PASCAL:
            if target == CaseConverter.CAMEL:
                return name[0].lower() + name[1:]
            elif target == CaseConverter.SNAKE:
                return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            elif target == CaseConverter.UPPER:
                return CaseConverter.convert(name, source, CaseConverter.SNAKE).upper()
        elif source == CaseConverter.UPPER:
            if target == CaseConverter.PASCAL:
                return ''.join(word.title() for word in name.split('_'))
            elif target == CaseConverter.CAMEL:
                return name[0].lower() + ''.join(word.title() for word in name[1:].split('_'))
            elif target == CaseConverter.SNAKE:
                return name.lower()

    @staticmethod
    def basic_match(name: str) -> int:
        if "_" in name:
            return CaseConverter.SNAKE
        elif name[0].isupper():
            return CaseConverter.PASCAL
        else:
            return CaseConverter.CAMEL


@dataclass
class NameFormat:
    case: int
    format: str = "{}"


class BaseCompiler(ABC):

    def format_name(self, name: str, name_type: NameTypes) -> str:
        name_format = self._get_name_format_map()[name_type]
        name = CaseConverter.convert_unknown(name, name_format.case)
        name = name_format.format.format(name)
        return name

    def _get_name_format_map(self) -> Dict[NameTypes, NameFormat]:
        raise NotImplementedError()

    def _get_primitive_map(self) -> Dict[Primitive, str]:
        raise NotImplementedError()

    def _parse_primitive(self, p: PrimitiveType):
        return self._get_primitive_map()[p.primitive]

    def run(self, schema: str, *args, **kwargs) -> str:
        raise NotImplementedError()
