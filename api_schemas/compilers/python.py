from typing import Dict

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

    def _get_array_format(self) -> str:
        return "List[{}]"

    def _get_name_format_map(self) -> Dict[NameTypes, NameFormat]:
        return {
            NameTypes.ENUM_NAME: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.CLASS: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.METHOD: NameFormat(CaseConverter.SNAKE, "{}"),
            NameTypes.CONSTANT: NameFormat(CaseConverter.UPPER, "{}"),
            NameTypes.ATTRIBUTE: NameFormat(CaseConverter.SNAKE, "{}"),
        }

    def _get_primitive_map(self) -> Dict[Primitive, str]:
        return {Primitive.Any: "Any", Primitive.Bool: "bool", Primitive.Str: "str",
                Primitive.Int: "int", Primitive.Float: "float"}


def convert(schema: str) -> str:
    f = PythonCompiler().compile_dataclasses(schema, file_template)
    f = autopep8.fix_code(f)
    return f
