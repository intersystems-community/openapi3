# Contributing to OpenAPI3

## Before you start

Before starting work on your pull request, please be aware of the following guidelines:

1. Make sure at least one GitHub issue exists that your pull request will "fix". If no issue exists yet, please create it before starting your work.
1. If an issue already exists but is assigned to someone else, please message them before starting your work. The other user may have work in progress.
1. Feature requests require a detailed spec laid out in the issue before a linked pull request will be reviewed. The spec should be approved by at least one maintainer before starting work on it. This is needed to ensure that the feature is in line with the broader roadmap for the extensions and to avoid contributors wasting their time on something that will not be accepted.

## Contributing a pull request

Work should be done on a unique branch -- not the master branch. Pull requests require the approval of the maintainer, as described in the [Governance document](https://github.com/intersystems-community/openapi3/blob/main/GOVERNANCE.md). In addition to that, it's often good to request a review by someone familiar with the technical details of your particular pull request.

We expect tests with full coverage to be included, and CI to be passing for a pull request before we will consider merging it.

## Development

You can clone the repo and install in editable mode:

```bash
git clone https://github.com/intersystems-community/openapi3.git
cd openapi3
pip install -e .
```

Run the test suite:

```bash
pytest tests/
```

Make sure to run the postman test suite as well under tests/integration