from typing import Dict

from mako.template import Template

from api_schemas import *
from api_schemas.compilers.base import *

file_template = Template("""\
/*
 *
 * Auto generated Code by python tool.
 * Changes in this file will be overwritten, when the script is executed again.
 *
*/
<%
    imports_str = "\\n".join([f"import {i};" for i in imports]) 
%>
${imports_str}

// Enunms
% for enum in enums:
enum ${enum.name} {
<% values = ",\\n  ".join(enum.values) %>\
  ${values}
}
% endfor

// Data Classes
% for cls in classes:
class ${cls.name} {
    % for attr in cls.req_attributes:
  ${attr.type} ${attr.native_name};
    % endfor
    % for attr in cls.opt_attributes:
  ${attr.type} ${attr.native_name};
    % endfor

  ${cls.name}(
    % for attr in cls.req_attributes:
    this.${attr.native_name},
    % endfor
    % if cls.opt_attributes:
    {
        % for attr in cls.opt_attributes:
    this.${attr.native_name},
        % endfor
    }
    % endif
  );

  ${cls.name}.fromJson(Map<String, dynamic> json) {
    % for attr in cls.req_attributes:
    ${attr.native_name} = ${attr.from_json};
    % endfor
     % for attr in cls.opt_attributes:
    if (json.containsKey("${attr.original_name}")) {
      ${attr.native_name} = ${attr.from_json};
    }
    % endfor
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = new Map<String, dynamic>();
    % for attr in cls.req_attributes:
    json["${attr.original_name}"] = ${attr.to_json};
    % endfor
    % for attr in cls.opt_attributes:
    if (${attr.native_name} != null) {
      json["${attr.original_name}"] = ${attr.to_json};
    }
    % endfor
    return json;
  }
}
%endfor 
""")


class DartCompiler(BaseCompiler):

    def format_from_json(self, t: Type, original_name: str, is_array: bool):
        if is_array:
            native_type = self.get_native_type(t, is_array)
            s = f"{native_type} tmp__ = [];\n" \
                f"for "
        if type(t) == ObjectType:
            native_type = self.get_native_type(t)
            return f"{native_type}.fromJson(json[\"{original_name}\"])"
        elif type(t) == PrimitiveType:
            return f"json[\"{original_name}\"]"
        elif type(t) == EnumType:
            native_type = self.get_native_type(t)
            return f"{native_type}.values.firstWhere(" \
                   f"(e) => e.toString() == \"{native_type}.\" + json[\"{original_name}\"])"

    def format_to_json(self, t: Type, native_name: str, is_array: bool):
        if type(t) == ObjectType:
            return f"{native_name}.toJson()"
        elif type(t) == PrimitiveType:
            return native_name
        elif type(t) == EnumType:
            native_type = self.get_native_type(t)
            return f"{native_name}.toString().replaceFirst(\"{native_type}.\", \"\")"

    def _get_array_format(self) -> str:
        return "List<{}>"

    def _get_name_format_map(self) -> Dict[NameTypes, NameFormat]:
        return {
            NameTypes.ENUM_NAME: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.CLASS: NameFormat(CaseConverter.PASCAL, "API{}"),
            NameTypes.METHOD: NameFormat(CaseConverter.CAMEL, "{}"),
            NameTypes.CONSTANT: NameFormat(CaseConverter.CAMEL, "{}"),
            NameTypes.ATTRIBUTE: NameFormat(CaseConverter.CAMEL, "{}"),
        }

    def _get_primitive_map(self) -> Dict[Primitive, str]:
        return {Primitive.Any: "dynamic", Primitive.Bool: "bool", Primitive.Str: "String",
                Primitive.Int: "int", Primitive.Float: "double"}


def convert(schema) -> str:
    f = DartCompiler().compile_dataclasses(schema, file_template)
    return f
