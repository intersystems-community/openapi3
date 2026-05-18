# InterSystems_OpenAPI3

Spec-first REST API development is an approach where you define your API's structure and behavior in a machine-readable document — the [OpenAPI Specification (OAS)](https://swagger.io/specification/) — before writing any application code. This document acts as a formal contract between the API provider and its consumers, ensuring everyone agrees on the data models and endpoints early in the lifecycle.

intersystems_openapi3 is a library that facilitates spec-first development for InterSystems IRIS. It speeds development of an [ObjectScript CSP](https://docs.intersystems.com/iris20261/csp/docbook/Doc.View.cls?KEY=GCSP_intro)-based web backend using a valid OpenAPI 3.1.x spec in json format.

# Installing

```bash
pip install intersystems_openapi3
```

# Usage

```bash
intersystems_openapi3 /path/to/valid_openapi3_1_spec.json
```

```bash
intersystems_openapi3 /path/to/valid_openapi3_1_spec.json -o /path/to/output/folder
```

```bash
intersystems_openapi3 /path/to/valid_openapi3_1_spec.json -n WebAppName
```

```bash
intersystems_openapi3 --version
```

```bash
intersystems_openapi3 --help
```
