from typing import Dict

from mako.template import Template

from api_schemas import Primitive
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
  ${attr.type} ${attr.name};
    % endfor
    % for attr in cls.opt_attributes:
  ${attr.type} ${attr.name};
    % endfor

  ${cls.name}(
    % for attr in cls.req_attributes:
    this.${attr.name},
    % endfor
    % if cls.opt_attributes:
    {
        % for attr in cls.opt_attributes:
    this.${attr.name},
        % endfor
    }
    % endif
  );

  ${cls.name}.fromJson(Map<String, dynamic> json) {
    % for attr in cls.req_attributes:
    ${attr.name} = json["${attr.name}"];
    % endfor
     % for attr in cls.opt_attributes:
    if (json.containsKey("${attr.name}")) {
      ${attr.name} = json["${attr.name}"];
    }
    % endfor
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = new Map<String, dynamic>();
    % for attr in cls.req_attributes:
    json["${attr.name}"] = ${attr.name};
    % endfor
    % for attr in cls.opt_attributes:
    if (${attr.name} != null) {
      json["${attr.name}"] = ${attr.name};
    }
    % endfor
    return json;
  }
}


%endfor 
""")


class DartCompiler(BaseCompiler):

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
