import json
import pytest
from pathlib import Path

from intersystems_openapi3.main import generate_from_spec


def write_spec(tmp_path: Path, spec: dict) -> Path:
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


DATATYPE_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Datatype Test API", "version": "1.0.0"},
    "paths": {
        "/test/{username}/{tag}/{code}/{emptyTag}/{note}/{age}/{count32}/{count64}/{qty}": {
            "get": {
                "operationId": "testOperation",
                "parameters": [
                    # string: maxLength only
                    {"name": "username",  "in": "path", "required": True, "schema": {"type": "string", "maxLength": 50}},
                    # string: minLength only
                    {"name": "tag",       "in": "path", "required": True,"schema": {"type": "string", "minLength": 3}},
                    # string: both minLength and maxLength
                    {"name": "code",      "in": "path", "required": True,"schema": {"type": "string", "minLength": 3, "maxLength": 20}},
                    # string: maxLength of 0 — tests that 0 is not treated as missing
                    {"name": "emptyTag",  "in": "path", "required": True,"schema": {"type": "string", "maxLength": 0}},
                    # string: no constraints — no validation should be generated
                    {"name": "note",      "in": "path", "required": True,"schema": {"type": "string"}},
                    # integer: explicit minimum and maximum
                    {"name": "age",       "in": "path", "required": True,"schema": {"type": "integer", "minimum": 0, "maximum": 120}},
                    # integer: int32 format — should apply default int32 bounds
                    {"name": "count32",   "in": "path", "required": True,"schema": {"type": "integer", "format": "int32"}},
                    # integer: int64 format — should apply default int64 bounds
                    {"name": "count64",   "in": "path", "required": True,"schema": {"type": "integer", "format": "int64"}},
                    # integer: multipleOf
                    {"name": "qty",       "in": "path", "required": True,"schema": {"type": "integer", "multipleOf": 5}}
                ],
                "responses": {"200": {"description": "ok"}}
            }
        }
    }
}


@pytest.fixture
def disp_content(tmp_path):
    spec_file = write_spec(tmp_path, DATATYPE_SPEC)
    generate_from_spec(spec_file, tmp_path, "TestApp")
    return (tmp_path / "TestApp.disp.cls").read_text(encoding="utf-8")


# ── string: maxLength ─────────────────────────────────────────────────────────

def test_string_maxlength_generates_length_check(disp_content):
    assert "$length(username)>50" in disp_content
    assert "HTTP400BADREQUEST" in disp_content
    assert '$$$ERROR($$$RESTInvalid,"username",username)' in disp_content


# ── string: minLength ─────────────────────────────────────────────────────────

def test_string_minlength_generates_length_check(disp_content):
    assert "$length(tag)<3" in disp_content


# ── string: maxLength and minLength together ──────────────────────────────────

def test_string_maxlength_and_minlength_combined(disp_content):
    assert "($length(code)>20)||($length(code)<3)" in disp_content


# ── string: maxLength of 0 is not skipped ────────────────────────────────────

def test_string_maxlength_zero_is_not_skipped(disp_content):
    assert "$length(emptyTag)>0" in disp_content


# ── string: no constraints produces no validation ────────────────────────────

def test_string_no_constraints_produces_no_validation(disp_content):
    assert "$length(note)" not in disp_content


# ── integer: explicit maximum and minimum ─────────────────────────────────────

def test_integer_explicit_maximum_and_minimum(disp_content):
    assert '$number(age,"I",0,120)' in disp_content


# ── integer: int32 default bounds ─────────────────────────────────────────────

def test_integer_int32_applies_default_bounds(disp_content):
    assert '($number(count32,"I",-2147483648,2147483647)="")' in disp_content


# ── integer: int64 default bounds ─────────────────────────────────────────────

def test_integer_int64_applies_default_bounds(disp_content):
    assert '($number(count64,"I",-9223372036854775808,9223372036854775807)="")' in disp_content



# ── integer: multipleOf ───────────────────────────────────────────────────────

def test_integer_multipleof_generates_modulo_check(disp_content):
    assert '($number(qty,"I")="")||((qty#5)\'=0)' in disp_content
