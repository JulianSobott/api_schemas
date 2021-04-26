from dataclasses import dataclass
from typing import List, Union, Dict

import autopep8 as autopep8

from api_schemas import *
from mako.template import Template

from api_schemas.compilers.base import BaseCompiler, NameTypes, CaseConverter, NameFormat

file_template = Template("""\
#
#
# Auto generated Code by python tool.
# Changes in this file will be overwritten, when the script is executed again.
#
#
<%
    imports_str = "\\n".join([f"import {i}" for i in imports]) 
%>
${imports_str}
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Dict, Optional, Any
import enum

# Communication classes
# TODO

# Enums
% for enum in enums:
class ${enum.name}(enum.Enum):
    % for i, value in enumerate(enum.values):
    ${value} = ${i},
    % endfor 
% endfor

# Data Classes
% for cls in classes:
@dataclass_json
@dataclass
class ${cls.name}:
    % for attr in cls.req_attributes:
  ${attr.name}: '${attr.type}'
    % endfor
   % for attr in cls.opt_attributes:
  ${attr.name}: 'Optional[${attr.type}]' = None
    % endfor
%endfor
""")


class PythonCompiler(BaseCompiler):

    def _get_name_format_map(self) -> Dict[NameTypes, NameFormat]:
        return {
            NameTypes.ENUM_NAME: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.CLASS: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.METHOD: NameFormat(CaseConverter.SNAKE, "{}"),
            NameTypes.CONSTANT: NameFormat(CaseConverter.UPPER, "{}"),
            NameTypes.ATTRIBUTE: NameFormat(CaseConverter.SNAKE, "{}"),
        }

    def run(self, schema: str, *args, **kwargs) -> str:
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
                        _type = f"List[{_type}]"
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

        file_content = file_template.render(classes=classes, enums=enums, imports=imports)
        file_content = autopep8.fix_code(file_content)
        return file_content

    def _get_primitive_map(self) -> Dict[Primitive, str]:
        return {Primitive.Any: "Any", Primitive.Bool: "bool", Primitive.Str: "str",
                Primitive.Int: "int", Primitive.Float: "float"}


def convert(schema) -> str:
    return PythonCompiler().run(schema)


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
