import json
import pytest
from pathlib import Path

import intersystems_openapi3.main as main
from intersystems_openapi3.main import generate_from_spec


# Regenerating an existing impl now delegates to a live IRIS instance. These are
# generation tests, so stub that out: when an impl file already exists, just keep
# the freshly generated text instead of connecting to IRIS.
@pytest.fixture(autouse=True)
def _no_iris(monkeypatch):
    monkeypatch.setattr(main, "regenerate_impl",
                        lambda new_text, old_text, class_name: new_text)


# ── helpers ───────────────────────────────────────────────────────────────────

def write_spec(tmp_path: Path, spec: dict) -> Path:
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


MAIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/fruits": {
            "get": {
                "operationId": "listFruits",
                "responses": {"200": {"description": "ok"}}
            },
            "post": {
                "operationId": "createFruit",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}}
                },
                "responses": {"201": {"description": "created"}}
            }
        },
                # path param WITH schema type — tests typed method signature

        "/fruit/{fruitName}": {
            "get": {
                "operationId": "getFruit",
                "parameters": [{"name": "fruitName", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "ok"}}
            }
        },
                # path param WITHOUT schema — tests untyped method signature

        "/stores/{storeId}": {
            "get": {
                "operationId": "getStore",
                "parameters": [{"name": "storeId", "in": "path", "required": True}],
                "responses": {"200": {"description": "ok"}}
            }
        },
                # no operationId — tests auto-assignment (Operation1, Operation2)

        "/items": {
            "get":  {"responses": {"200": {"description": "ok"}}},
            "post": {"responses": {"200": {"description": "ok"}}}
        }
    }
}


@pytest.fixture
def disp_content(tmp_path):
    spec_file = write_spec(tmp_path, MAIN_SPEC)
    generate_from_spec(spec_file, tmp_path, "TestApp")
    return (tmp_path / "TestApp.disp.cls").read_text(encoding="utf-8")


@pytest.fixture
def impl_content(tmp_path):
    spec_file = write_spec(tmp_path, MAIN_SPEC)
    generate_from_spec(spec_file, tmp_path, "TestApp")
    return (tmp_path / "TestApp.impl.cls").read_text(encoding="utf-8")


# ── version validation ────────────────────────────────────────────────────────

def test_wrong_version_prints_error_and_does_not_write(tmp_path, capsys):
    spec = {**MAIN_SPEC, "openapi": "3.0.0"}
    spec_file = write_spec(tmp_path, spec)

    generate_from_spec(spec_file, tmp_path, "TestApp")

    captured = capsys.readouterr()
    assert "Please enter a spec file which is version 3.1.x" in captured.out
    assert not (tmp_path / "TestApp.disp.cls").exists()
    assert not (tmp_path / "TestApp.impl.cls").exists()


def test_missing_openapi_key_prints_error_and_does_not_write(tmp_path, capsys):
    spec = {"info": {"title": "Test"}, "paths": {}}
    spec_file = write_spec(tmp_path, spec)

    generate_from_spec(spec_file, tmp_path, "TestApp")

    captured = capsys.readouterr()
    assert "Invalid specification file" in captured.out
    assert not (tmp_path / "TestApp.disp.cls").exists()


# ── output files created ──────────────────────────────────────────────────────

def test_output_files_are_created(tmp_path):
    spec_file = write_spec(tmp_path, MAIN_SPEC)
    generate_from_spec(spec_file, tmp_path, "TestApp")

    assert (tmp_path / "TestApp.disp.cls").exists()
    assert (tmp_path / "TestApp.impl.cls").exists()


def test_output_files_are_not_empty(disp_content, impl_content):
    assert disp_content.strip() != ""
    assert impl_content.strip() != ""


# ── disp class content ────────────────────────────────────────────────────────

def test_disp_class_contains_app_name(disp_content):
    assert "Class TestApp.disp" in disp_content


def test_disp_class_extends_csp_rest(disp_content):
    assert "Extends %CSP.REST" in disp_content


def test_disp_class_contains_route_for_operation(disp_content):
    assert '<Route Url="/fruits" Method="get" Call="listFruits" />' in disp_content
    assert "listFruits" in disp_content


def test_disp_class_contains_method_for_operation(disp_content):
    assert "ClassMethod listFruits" in disp_content


# ── impl class content ────────────────────────────────────────────────────────

def test_impl_class_extends_rest_impl(impl_content):
    assert "Extends %REST.Impl" in impl_content


def test_impl_class_contains_method_stub(impl_content):
    assert "ClassMethod listFruits" in impl_content


# ── path parameters ───────────────────────────────────────────────────────────

def test_path_parameter_with_datatype_in_method_signature(disp_content):
    assert "ClassMethod getFruit(fruitName As %String)" in disp_content


def test_path_parameter_without_datatype_in_method_signature(disp_content):
    assert "ClassMethod getStore(storeId)" in disp_content


# ── auto-assigned operationId ─────────────────────────────────────────────────

def test_missing_operation_id_gets_auto_assigned(disp_content):
    assert "Operation1" in disp_content


# ── request body ─────────────────────────────────────────────────────────────

def test_post_with_request_body_generates_consumes_check(disp_content):
    assert '$$$ERROR($$$RESTRequired,"body")' in disp_content
    assert "application/json" in disp_content
    assert "HTTP415" in disp_content


# ── error handling ────────────────────────────────────────────────────────────

def test_invalid_json_raises(tmp_path):
    spec_file = tmp_path / "bad.json"
    spec_file.write_text("not valid json", encoding="utf-8")

    with pytest.raises(Exception):
        generate_from_spec(spec_file, tmp_path, "TestApp")


def test_runtime_error_includes_operation_context(tmp_path):
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/pets/{petId}": {
                "get": {
                    "operationId": "getPet",
                    "parameters": [{"name": "petId", "in": "path", "required": True}],  # no schema
                    "responses": {"200": {"content": {"invalid media type!!":{}}}}
                }
            }
        }
    }
    spec_file = write_spec(tmp_path, spec)

    with pytest.raises(RuntimeError, match="GET /pets") as hhh:
        print(hhh)
        generate_from_spec(spec_file, tmp_path, "TestApp")