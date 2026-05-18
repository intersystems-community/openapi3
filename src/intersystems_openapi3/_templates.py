
templates = {

# ------------------------------------------------------------------------------------- dispatch class
#disp_class_template
"disp_class_template" : """
/// {description}
/// {summary}
/// Generated using intersystems_openapi3 library and OpenAPI3 specification file:  {spec_file_path}
/// DO NOT EDIT. Will get overwritten on regeneration.
Class {app_name}.disp Extends %CSP.REST [ ProcedureBlock ]
    {{

/// Ignore any writes done directly by the REST method.
Parameter IgnoreWrites = 1;

/// By default convert the input stream to Unicode
Parameter CONVERTINPUTSTREAM = 1;

XData UrlMap [ XMLNamespace = "http://www.intersystems.com/urlmap" ]
{{
<Routes>
{routes}
</Routes>
}}

{methods}

}}
"""

,
# ------------------------------------------------------------------------------------- route
#route_template
"route_template" : """<Route Url="{route_url}" Method="{method}" Call="{operation_id}" />"""

,
# ------------------------------------------------------------------------------------- method
#disp_method_template
"disp_method_template" : """
/// {summary}
/// {description}
ClassMethod {operation_id}({method_def_params}) As %Status
{{
    Try {{
            {consumes_os}
            {produces_os}
            {parameter_check}
        Set response = ##class({app_name}.impl).{operation_id}({path_param_string}{body_param})
        Do ##class({app_name}.impl).%WriteResponse(response)

        }} Catch (ex) {{
                Try {{
                    Do ##class({app_name}.impl).%ReportRESTError(..#HTTP500INTERNALSERVERERROR, ex.AsStatus(),$parameter("{app_name}.impl","ExposeServerExceptions"))
                    }} Catch {{
                    Do ##class(%REST.Impl).%ReportRESTError(..#HTTP500INTERNALSERVERERROR, ex.AsStatus(),$parameter("{app_name}.impl","ExposeServerExceptions"))
                        }}
        }}
    Quit $$$OK
}}
 """
 ,
# ------------------------------------------------------------------------------------- request handling not required
#request_handling_not_required

"request_handling_not_required" :"""

        If $isobject(%request.Content){{
            {request_content_check}
            Set body=%request.Content
        }}
"""
,
# ------------------------------------------------------------------------------------- request handling required
#request_handling_required

"request_handling_required" : """
        If '$isobject(%request.Content) Do ##class(%REST.Impl).%ReportRESTError(..#HTTP400BADREQUEST,$$$ERROR($$$RESTRequired,"body")) Quit
{request_content_check}
        
        Set body=%request.Content
"""
,
# ------------------------------------------------------------------------------------- consumes template
#request_content_check
"request_content_check" : """
        If $case(%request.ContentType, {all_consumes},:1) {{
            Try {{
                Do ##class({app_name}.impl).%ReportRESTError(..#HTTP415UNSUPPORTEDMEDIATYPE,$$$ERROR($$$RESTContentType,%request.ContentType))
            }} Catch {{
                Do ##class(%REST.Impl).%ReportRESTError(..#HTTP415UNSUPPORTEDMEDIATYPE,$$$ERROR($$$RESTContentType,%request.ContentType))
            }}
            Quit
        }}"""


,
# ------------------------------------------------------------------------------------- produces template
#produces_template
"produces_template": """
        If '##class(%REST.Impl).%CheckAccepts("{all_produces}") {{
            Try {{
                Do ##class({app_name}.impl).%ReportRESTError(..#HTTP406NOTACCEPTABLE,$$$ERROR($$$RESTBadAccepts))
            }} Catch {{
                Do ##class(%REST.Impl).%ReportRESTError(..#HTTP406NOTACCEPTABLE,$$$ERROR($$$RESTBadAccepts))
            }}
            Quit
        }}"""


,
# ------------------------------------------------------------------------------------- implementation class
#implementation_class_template
"impl_class_template" : """

/// {description}
/// {summary}
Class {app_name}.impl  Extends %REST.Impl [ ProcedureBlock ]
{{

/// If ExposeServerExceptions is true, then details of internal errors will be exposed.

Parameter ExposeServerExceptions = 0;

{methods}

}}

"""


,
"impl_method_template":"""

///{description}
ClassMethod {operation_id}({method_def_params}{body_param}) As %Stream.Object
{{
    //(Place business logic here)
    //Do ..%SetStatusCode(<HTTP_status_code>)
    //Do ..%SetHeader(<name>,<value>)
    //Quit (Place response here) ; response may be a string, stream or dynamic object
}}

"""

}