import re
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union

from mako.template import Template

from api_schemas import Primitive, PrimitiveType, parse, ObjectType, EnumType, Type

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
                comp = name.split("_")
                return comp[0].lower() + ''.join(word.title() for word in comp[1:])
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

    def format_from_json(self, t: Type, native_name: str, original_name: str, is_array: bool):
        raise NotImplementedError()

    def format_to_json(self, t: Type, native_name: str, original_name: str, is_array: bool):
        raise NotImplementedError()

    def get_native_type(self, t: Type, is_array: bool = False, is_optional: bool = False):
        """Returns the Type for formatted for the specific language.
        This type can be used for attributes, parameters, ...

        e.g.
        ```java
        List<String> names; // 'List<String>' would be returned
        ```
        """
        if type(t) == ObjectType:
            _type = self.format_name(t.name, NameTypes.CLASS)
        elif type(t) == PrimitiveType:
            _type = self._get_primitive_map()[t.primitive]
        elif type(t) == EnumType:
            _type = self.format_name(t.name, NameTypes.ENUM_NAME)
        else:
            raise Exception(f"Unknown type {type(t)}")
        if is_array:
            _type = self._get_array_format().format(_type)
        # TODO: maybe optional
        return _type

    def compile_dataclasses(self, schema: str, template: Template, *args, **kwargs) -> str:
        ir = parse(schema)
        classes = []
        enums = []
        objects: List[Union[ObjectType, EnumType]] = []
        for obj in ir.global_types:
            if type(obj.type) in [ObjectType, EnumType]:
                objects.append(obj.type)

        # get all not globally defined classes
        # TODO: Should they be global then?
        for event in ir.ws_events.client + ir.ws_events.server:
            queue = event.data
            while queue and isinstance(queue, list):
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
                    native_name = self.format_name(a.name, NameTypes.ATTRIBUTE)
                    original_name = a.name
                    if type(a.type) in [ObjectType, EnumType]:
                        objects.append(a.type)
                    _type = self.get_native_type(a.type, a.is_array, a.is_optional)
                    from_json = self.format_from_json(a.type, native_name, original_name, a.is_array)
                    to_json = self.format_to_json(a.type, native_name, original_name, a.is_array)
                    java_attribute = Attribute(a.name, native_name, _type, from_json, to_json)
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
    original_name: str
    native_name: str
    type: str
    from_json: str
    to_json: str


@dataclass
class Enum:
    name: str
    values: List[str]
