from typing import Any

DATATYPE_MAP= {
    "string" : "%String",
    "integer": "%Integer",
    "number" : "%Float",
    "boolean": "%Boolean"
}


def generate_string_parameter_template(parameter: dict[str, Any]) -> str:

    schema = parameter.get("schema",{})
    schema_format = schema.get("format","")
    name = parameter.get("name")

    delim = ""
    test_text = ""
    byte_text = ""
    if schema_format == "byte":
        byte_text = f"      Set {name} = $system.Encryption.Base64Decode({name})" + "\n"
    elif schema_format == "date":
        test_text = f"(##class(%Date).XSDToLogical({name})= "")"
        delim = "||"
    elif schema_format == "date-time":
        test_text = f"(##class(%TimeStamp).XSDToLogical({name})= "")"
        delim = "||"

    maxLength = schema.get("maxLength")
    minLength = schema.get("minLength")

    ##TODO: Sanitize pattern and escape " and ) etc if present..
    pattern = schema.get("pattern","")

    if maxLength is not None :
        test_text = f"{test_text}{delim}($length({name})>{maxLength})"
        delim = "||"

    if minLength is not None:
        test_text = f"{test_text}{delim}($length({name})<{minLength})"
        delim = "||"
        
    if pattern != "":
        test_text = f"{test_text}{delim}'$match({name},\"{pattern}\")"
        
    if test_text != "":
            test_text = f"        If {test_text} Do ##class(%REST.Impl).%ReportRESTError(..#HTTP400BADREQUEST,$$$ERROR($$$RESTInvalid,\"{name}\",{name})) Quit"

   
    return byte_text + test_text 


def generate_integer_parameter_template(parameter: dict[str, Any]) -> str:

    schema = parameter.get("schema",{})
    schema_format = schema.get("format","")
    name = parameter.get("name")

    test_text = ""

    maximum = schema.get("maximum","")
    minimum = schema.get("minimum","")
    multipleOf = schema.get("multipleOf","")
    
    if schema_format == "int32":
        if minimum == "": minimum = -2147483648
        if maximum == "": maximum = 2147483647
    
    elif schema_format == "int64":
        if minimum == "": minimum = -9223372036854775808
        if maximum == "": maximum = 9223372036854775807
	
    ## TODO: set excusive maximum values
	# If maximum'="" and schema.get("exclusiveMaximum"): maximum=maximum-1
	# If minimum'=""and schema.get("exclusiveMinimum"):  minimum=minimum+1
    test_text = f'($number({name},"I"'
    if (minimum != "" ) or (maximum != "" ): test_text = test_text+","+str(minimum)
    if maximum != "": test_text = test_text + "," + str(maximum)
    test_text = f'{test_text})="")'
    if multipleOf != "":
        test_text = f"{test_text}||(({name}#{multipleOf})'=0)"

    if test_text != "":
            test_text = f"        If {test_text} Do ##class(%REST.Impl).%ReportRESTError(..#HTTP400BADREQUEST,$$$ERROR($$$RESTInvalid,\"{name}\",{name})) Quit"


    return test_text
	
	
## TODO
# Number
# Boolean
# Array
# Object/File