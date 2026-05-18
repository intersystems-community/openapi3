from typing import Any

from ._templates import templates
from ._sanitize import validate_media_type

def generate_request_body_handling(operation_details: dict[str, Any],app_name: str,is_put_post_patch: bool) -> str:
    """
        Also known as Consumes list in older specifications. 
        Generate the ObjectScript 'consumes' guard using OAS3 operation.
        Note: This is the replacement for "in":"body" parameter from openapi2.0
        1. Checks for a body in put post and patch by default
        2. Enforces presence of body in request when required = true for requestBody object
    """
    if requestBody:=operation_details.get("requestBody",None):
        content = requestBody.get("content",{})
        request_content_keys = sorted(validate_media_type(k) for k in content.keys())
        if not request_content_keys:
            request_content_check = ""
        else:
            all_req_mime_type = ','.join([f'"{ctype}":0' for ctype in request_content_keys])
            request_content_check = templates.get("request_content_check")
            request_content_check = request_content_check.format(
                all_consumes = all_req_mime_type,
                app_name = app_name)

        if str(requestBody.get("required", False)).lower() == "true":
            return templates.get("request_handling_required").format(request_content_check = request_content_check)
        else:
            return templates.get("request_handling_not_required").format(request_content_check = request_content_check)
    else:
        if is_put_post_patch:
            return templates.get("request_handling_not_required").format(request_content_check = "")
        else:
            return ""
 


def response_media_types(operation: dict[str, Any], app_name: str) -> str:
    """
    Also known as Produces list in older specifications.
    Generate the ObjectScript 'produces' guard using OAS3 operation.
    In OAS3 it is: Responses object -> content. The key is the media type
    and the value is the associated schema. 

    If no response content types are present, returns an empty string.
    """
    mts = set()
    for resp in (operation.get("responses") or {}).values():
        content = (resp or {}).get("content", {})
        mts.update(validate_media_type(k) for k in content.keys())
    produces = sorted(mts)
    if not produces:
        return ""  # nothing to enforce
    all_produces = ','.join(produces)
    produces_template = templates.get("produces_template")
    final_produces = produces_template.format(
        all_produces = all_produces,
        app_name = app_name)
    return final_produces


