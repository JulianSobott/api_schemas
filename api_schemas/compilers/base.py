import re
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union

from mako.template import Template

from api_schemas import Primitive, PrimitiveType, parse, ObjectType, EnumType, ReferenceType

__all__ = ["NameTypes", "CaseConverter", "BaseCompiler", "NameFormat"]

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

    def _get_array_format(self) -> str:
        raise NotImplementedError()

    def compile_dataclasses(self, schema: str, template: Template, *args, **kwargs) -> str:
        ir = parse(schema)
        classes = []
        enums = []
        objects: List[Union[ObjectType, EnumType]] = []
        reference_types_map = {}
        for t in ir.global_types:
            if type(t.type) == ObjectType:
                objects.append(t.type)
                _type = self.format_name(t.name, NameTypes.CLASS)
            elif type(t.type) == PrimitiveType:
                _type = self._get_primitive_map()[t.type.primitive]
            elif type(t.type) == EnumType:
                objects.append(t.type)
                _type = self.format_name(t.name, NameTypes.ENUM_NAME)
            elif type(t.type) == ReferenceType:
                # TODO handle reference before declaration
                _type = reference_types_map[t.type.name]
            else:
                raise Exception(f"Unknown type of attribute {type(t.type)}")
            reference_types_map[t.name] = _type

        # get all not globally defined classes
        # TODO: Should they be global then?
        for event in ir.ws_events.client + ir.ws_events.server:
            queue = event.data
            while queue:
                e = queue.pop()
                if type(e.type) == ObjectType:
                    queue.extend(e.type.attributes)
                    objects.append(e.type)
                if type(e.type) == EnumType:
                    objects.append(e.type)

        while objects:
            t = objects.pop()
            if type(t) == ObjectType:
                class_name = self.format_name(t.name, NameTypes.CLASS)
                req_attributes: List[Attribute] = []
                opt_attributes: List[Attribute] = []
                for a in t.attributes:
                    name = self.format_name(a.name, NameTypes.ATTRIBUTE)
                    if type(a.type) == PrimitiveType:
                        _type = self._get_primitive_map()[a.type.primitive]
                    elif type(a.type) == EnumType:
                        _type = self.format_name(a.type.name, NameTypes.ENUM_NAME)
                        objects.append(a.type)
                    elif type(a.type) == ObjectType:
                        _type = self.format_name(a.type.name, NameTypes.CLASS)
                        objects.append(a.type)
                    elif type(a.type) == ReferenceType:
                        _type = reference_types_map[a.type.name]
                    else:
                        raise Exception(f"Unknown type of attribute {type(a)}")

                    if a.is_array:
                        _type = self._get_array_format().format(_type)
                    java_attribute = Attribute(name, _type)
                    if a.is_optional:
                        opt_attributes.append(java_attribute)
                    else:
                        req_attributes.append(java_attribute)
                java_class = Class(class_name, req_attributes, opt_attributes)
                classes.append(java_class)
            elif type(t) == EnumType:
                name = self.format_name(t.name, NameTypes.ENUM_NAME)
                enums.append(Enum(name, t.values))
        imports = []

        file_content = template.render(classes=classes, enums=enums, imports=imports)
        return file_content


@dataclass
class Class:
    name: str
    req_attributes: List['Attribute']
    opt_attributes: List['Attribute']


@dataclass
class Attribute:
    name: str
    type: str


@dataclass
class Enum:
    name: str
    values: List[str]
