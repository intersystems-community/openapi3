
import json
import argparse
from pathlib import Path
from typing import Any
from importlib.metadata import version, PackageNotFoundError

from ._templates import templates
from ._object_parameter import (generate_params_for_method_definition, generate_param_string_for_method_call, 
                            split_parameters, merge_parameters, generate_parameter_stubs)
from ._object_requestBody_response import generate_request_body_handling, response_media_types
from ._sanitize import sanitize_names, sanitize_comments
from ._regenerate_impl import regenerate_impl


def get_version() -> str:
    try:
        return version("intersystems_openapi3")
    except PackageNotFoundError:
        return "unknown"


# __________________________________________________________________________________________ helpers

def generate_impl_method(summary: str,description: str,operation_id: str,path_params: list[dict[str,Any]]) -> str:
    method_def_params = generate_params_for_method_definition(path_params)
    impl_method_template = templates.get("impl_method_template")
    body_param = ", body" if method_def_params else "body"

    return impl_method_template.format(
                            description = description,
                            summary = summary,
                            operation_id = operation_id,
                            method_def_params = method_def_params,
                            body_param = body_param
                            )
# __________________________________________________________________________________________ implementation method


def generate_disp_method(operation_details: dict[str, Any],summary: str, description: str,operation_id: str,path_params: list[dict[str, Any]],all_params: list[dict[str, Any]],app_name: str,is_put_post_patch: bool) -> str:
    path_param_string = generate_param_string_for_method_call(path_params)
    method_def_params = generate_params_for_method_definition(path_params)
    consumes_os = generate_request_body_handling(operation_details, app_name, is_put_post_patch)
    produces_os = response_media_types(operation_details, app_name)
    parameter_check = generate_parameter_stubs(all_params)
    disp_method_template = templates.get("disp_method_template")
    
    body_param = ", .body" if (is_put_post_patch or (operation_details.get("requestBody",None))) else ""
    if path_param_string == "":
        if body_param != "":
            body_param = ".body"

    return disp_method_template.format(
                            description = description,
                            summary = summary,
                            operation_id = operation_id,
                            method_def_params = method_def_params,
                            consumes_os = consumes_os,
                            produces_os = produces_os,
                            parameter_check = parameter_check,
                            app_name = app_name,
                            path_param_string = path_param_string,
                            body_param = body_param
                            )





def generate_routes_and_methods(json_obj: dict[str, Any], app_name: str) -> tuple[list[str], list[str], list[str]]:
    path_item_objects = json_obj.get("paths")
    routes=[]
    disp_methods = []
    impl_methods = []
    operation_id_counter = 1 
    for path_item, path_item_details in path_item_objects.items():
        path_level_params = path_item_details.get("parameters", [])

        if path_level_summary:= sanitize_comments(path_item_details.get("summary", "")):
            path_level_summary += "\n/// "
        if path_level_description:= sanitize_comments(path_item_details.get("description", "")):
            path_level_description += "\n/// "

        for operation, operation_details in path_item_details.items():
            if operation in ["head","get","put","post","patch","delete"]:
                try:
                    if operation_id:= operation_details.get("operationId"):
                        operation_id = sanitize_names(operation_id).strip()
                        if not operation_id:
                            return f"missing operation ID in {path_item_details} "
                    else:
                        operation_id = f"Operation{operation_id_counter}"
                        operation_id_counter += 1 
                    route_url = path_item.replace("{", ":").replace("}", "") # for path/query parameter

                    ## _____________________________________________________________________________________________
                    ## create a route item for the route map 
                    route = f'  <Route Url="{route_url}" Method="{operation}" Call="{operation_id}" />'
                    routes.append(route)

                    ## _____________________________________________________________________________________________
                    ## create the disp and impl methods 

                    description = path_level_description + sanitize_comments(operation_details.get("description",""))
                    summary = path_level_summary +  sanitize_comments(operation_details.get("summary",""))

                    ## Handle parameters. Merge from different locations and split by path, query, cookie, header
                    operation_level_params = operation_details.get("parameters", [])
                    all_params = merge_parameters(path_level_params,operation_level_params)
                    path_params, query_params, header_params, cookie_params = split_parameters(all_params)


                    for p in all_params:
                        if not p.get("schema", {}).get("type"):
                            print(f"WARNING: No schema associated with parameter {p.get('name')} or it is not a dictionary")

                    ## Generate method for dispatch class
                    is_put_post_patch = operation in {"put", "post", "patch"}
                    dispatch_method= generate_disp_method(operation_details,summary, description,operation_id,path_params,all_params,app_name,is_put_post_patch)
                    disp_methods.append(dispatch_method)
                    
                    ## Generate method for implementation class
                    impl_method = generate_impl_method(summary,description,operation_id,path_params)
                    impl_methods.append(impl_method)
                except Exception as e:
                    raise RuntimeError(f"Error processing {operation.upper()} {path_item}: {e}") from e


    return routes, disp_methods, impl_methods


def compile_classes(json_obj: dict[str, Any], routes: list[str], disp_methods: list[str], impl_methods: list[str], spec_file_path: Path, app_name: str) -> tuple[str, str]:

    class_level_description = sanitize_comments(json_obj.get("info").get("description",""))
    class_level_summary = sanitize_comments(json_obj.get("info").get("summary",""))

    all_routes = "\n".join(routes)
    all_disp_methods = "\n".join(disp_methods)
    disp_class_template = templates.get("disp_class_template")
    disp_str = disp_class_template.format(
                                description = class_level_description,
                                summary = class_level_summary,
                                spec_file_path = spec_file_path,
                                app_name = app_name,
                                routes = all_routes,
                                methods = all_disp_methods
                                )


    all_impl_methods = "\n".join(impl_methods)
    impl_class_template = templates.get("impl_class_template")
    impl_str = impl_class_template.format(
                                description = class_level_description,
                                summary = class_level_summary,
                                app_name = app_name, 
                                methods = all_impl_methods
                              )
 
   
    return disp_str, impl_str

def _write_atomic(target: Path, content: str) -> None:
    """
     Write via a temp file in the same directory, then replace the target.
    """
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    tmp.replace(target)


def generate_from_spec(spec_file_path: Path, out_path: Path, app_name: str) -> None:

    with open(spec_file_path,'r', encoding="utf-8") as f:
        json_object = json.load(f)

    if "openapi" in json_object:
        if json_object["openapi"][:3] != "3.1":
            print(f"Error: Please enter a spec file which is version 3.1.x as the correct backend generation for any other version cannot be guaranteed \nYour OpenAPI Specification is version {json_object['openapi']}")
            return
    else:
        print("Error: Invalid specification file. Please make sure that the 'openapi' key is present in the json spec")
        return

    routes, disp_methods, impl_methods = generate_routes_and_methods(json_object, app_name)
    disp_str,impl_str = compile_classes(json_object, routes, disp_methods, impl_methods, spec_file_path, app_name)

    disp_class = out_path / f"{app_name}.disp.cls"
    _write_atomic(disp_class, disp_str)

    # The implementation class is merged, not overwritten
    impl_class = out_path / f"{app_name}.impl.cls"
    existing_impl = impl_class.read_text(encoding="utf-8") if impl_class.exists() else None

    if existing_impl is None:
        _write_atomic(impl_class, impl_str)

    else:
        try:
            print(" An implementation file with the same name already exists at the output location.")
            print(" You will have to connect to your IRIS instance to make sure any modifications are not overwritten.")
            print(" If you do not wish to connect to IRIS, delete the existing implementaion file or generate the files in a new folder")
            merged_impl = regenerate_impl(impl_str, existing_impl, f"{app_name}.impl")
        except ValueError as e:
            print(f"Error: could not merge into existing {impl_class} ({e}).")
            print("The existing implementation file was left unchanged.")
            return

        _write_atomic(impl_class, merged_impl)



def main():

    print("\nWARNING: This tool assumes the input specification file is a valid OpenAPI 3.1.x document encoded as JSON. This tool does not validate the input specification.\n")
    
    parser = argparse.ArgumentParser(description = "Pass the path to your valid openapi 3.1.x json specification file to get the dispatch and implementation .cls files at the same location. use the -o flag to direct the output to another location")
    parser.add_argument("file", help="The first argument to the intersystems_openapi3 command should be the file path of the valid json spec file in 3.1.x format")
    parser.add_argument("-o", "--output", help="Location of generated dispatch and implementation files")
    parser.add_argument("-n", "--name", help="Custom name for dispatch and implementation files. If this is not provided, the generated files would be named spec_file_name.disp.cls and spec_file_name.impl.cls")
    parser.add_argument("--version",action="version",version=f"intersystems_openapi3   {get_version()}")
    args = parser.parse_args()

    spec_file_path = Path(args.file)

    if args.name:
        app_name = sanitize_names(args.name).strip()
        
    else:
        app_name = sanitize_names(spec_file_path.stem).strip()
    
    if args.output:
        out_path = Path(args.output)
        if out_path.exists() and not out_path.is_dir():
            raise ValueError("You entered a file path instead of a directory path for the generated files.")
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = spec_file_path.parent

    generate_from_spec(spec_file_path, out_path, app_name)


if __name__ == "__main__":
    main()

