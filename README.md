# intersystems_openapi3

A CLI tool that generates InterSystems IRIS CSP REST backend classes from an OpenAPI 3.1.x specification. Point it at a valid JSON spec and it produces two ready-to-import ObjectScript class files — a dispatch class that handles routing and validation, and an implementation stub where you fill in the business logic.

## Requirements

- Python 3.9+
- A valid OpenAPI 3.1.x spec in JSON format

## Installation

```bash
pip install intersystems_openapi3
```

## Usage

**Generate classes from a spec (output alongside the spec file):**
```bash
intersystems_openapi3 /path/to/spec.json
```

**Write output to a specific directory:**
```bash
intersystems_openapi3 /path/to/spec.json -o /path/to/output/
```

**Use a custom name for the generated classes:**
```bash
intersystems_openapi3 /path/to/spec.json -n MyRestService
```

**Other flags:**
```bash
intersystems_openapi3 --version
intersystems_openapi3 --help
```

## Output

Two ObjectScript class files are generated in the output directory:

| File | Description |
|------|-------------|
| `{MyRestService}.disp.cls` | Dispatch class — handles URL routing, parameter validation, request body checks, and Accept header validation. **Do not edit.** |
| `{MyRestService}.impl.cls` | Implementation class — one stub method per operation. Add your business logic here. |

Import both files into your InterSystems IRIS instance to set up the REST API.

## What gets generated

For each operation in the spec, the tool produces:

- **Typed method signatures** — parameters are annotated with ObjectScript types derived from the OpenAPI schema (`%String`, `%Integer`, `%Float`, `%Boolean`)
- **Parameter validation** — enforces constraints such as `minLength`, `maxLength`, `pattern`, `minimum`, `maximum`, and format-specific bounds (`int32`, `int64`)
- **Request body handling** — validates that required bodies are present and checks `Content-Type` against declared media types
- **Response media type validation** — validates `Accept` headers against declared response schemas
- **Auto-assigned operation IDs** — if your spec omits `operationId`, one is generated from the HTTP method and path

## Example

Given a spec with a `GET /users/{id}` operation, the tool generates a dispatch method that validates the `id` path parameter and calls through to an implementation stub:

```objectscript
/// GET /users/{id}
ClassMethod GetUsersId(id As %String) As %Status
{
    // Add your business logic here
    Quit $$$OK
}
```


