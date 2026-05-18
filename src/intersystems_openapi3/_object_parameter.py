from typing import Any

from ._handle_datatypes import DATATYPE_MAP, generate_string_parameter_template, generate_integer_parameter_template


def check_schema(param: dict[str, Any]) -> str:

    if param_type:= param.get("schema", {}).get("type"):
        return " As " + DATATYPE_MAP.get(param_type, "%String")    
    print(f"WARNING: No schema associated with parameter {param['name']} or it is not a dictionary")
    return ""

def generate_params_for_method_definition(all_params: list[dict[str, Any]]) -> str:
    return (" " + ",".join(
        p["name"] + check_schema(p)
        for p in all_params
    )).strip()

def generate_param_string_for_method_call(all_params: list[dict[str, Any]]) -> str:
    return ", ".join(p["name"] for p in all_params)

def split_parameters(params: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    path_params = [p for p in params if p.get("in") == "path"]
    query_params = [p for p in params if p.get("in") == "query"]
    header_params = [p for p in params if p.get("in") == "header"]
    cookie_params = [p for p in params if p.get("in") == "cookie"]
    return path_params, query_params, header_params, cookie_params


def merge_parameters(path_level_params: list[dict[str, Any]], operation_level_params: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merges parameters defined at path_item_level and operation_level: operation-level overrides by (name,in)."""
    def key(p): return (p.get("name"), p.get("in"))
    merged = {}
    for p in path_level_params or []:
        merged[key(p)] = p
    for p in operation_level_params or []:
        merged[key(p)] = p  # override
    return list(merged.values())


def generate_parameter_stubs(all_params: list[dict[str, Any]]) -> str:
    parameter_text = []
    for parameter in all_params:
        if parameter.get("schema", {}).get("type") == "string":
            text = generate_string_parameter_template(parameter)
        elif parameter.get("schema", {}).get("type") == "integer":
            text = generate_integer_parameter_template(parameter)
        else:
            text = ""

        parameter_text.append(text)

    return "\n".join(parameter_text) if parameter_text else ""