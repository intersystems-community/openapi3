"""Regenerate method signatures using IRIS dictionary definitions."""

import os
import re
from typing import Any
from uuid import uuid4
from getpass import getpass

_CLASS_RE = re.compile(r"^([ \t]*Class[ \t]+)([%\w.]+)", re.MULTILINE)
_CHUNK_SIZE = 32_000


def iris_conn(args: dict):
    # pip install intersystems-irispython
    import iris
    # args = {'hostname':'127.0.0.1', 'port': 51783,'namespace':'USER', 'username': 'superuser', 'password':'SYS'}
    conn = iris.connect(**args)
    return iris.createIRIS(conn), args["namespace"]

def get_args() -> dict:
    def value(env_name: str, prompt: str) -> str:
        return os.getenv(env_name) or input(prompt).strip()

    return {
        "hostname": value("IRIS_HOSTNAME", "IRIS_HOSTNAME: "),
        "port": int(value("IRIS_PORT", "IRIS_PORT: ")),
        "namespace": value("IRIS_NAMESPACE", "IRIS_NAMESPACE: "),
        "username": value("IRIS_USERNAME", "IRIS_USERNAME: "),
        "password": os.getenv("IRIS_PASSWORD") or getpass("IRIS_PASSWORD: "),
    }

def regenerate_impl( new_text: str, old_text: str, class_name: str) -> str:
    """Update old method arguments and return types from a new class."""

    print(" Set these as environment variables to avoid entering each time")

    args = get_args()
    myiris, namespace = iris_conn(args)

    original_name = class_name
    token = uuid4().hex
    old_name = f"OpenAPI3.Temp.T{token}Old"
    new_name = f"OpenAPI3.Temp.T{token}New"

    try:
        old_class = _class_from_text( myiris, namespace, old_name, _rename(old_text, old_name))
        new_class = _class_from_text( myiris, namespace, new_name, _rename(new_text, new_name))

        old_methods = _methods(old_class)
        new_methods = _methods(new_class)

        for name, old_method in old_methods.items():
            new_method = new_methods.get(name)
            if new_method is None:
                continue

            changed = False
            old_values = []
            for property_name in ("FormalSpec", "ReturnType"):
                new_value = new_method.get(property_name)
                if old_method.get(property_name) != new_value:
                    old_values.append(property_name+":"+old_method.get(property_name))
                    old_method.set(property_name, new_value)
                    changed = True

            description = new_method.get("Description") or ""
            if changed:
                description = description + " WARNING: Method Signature changed" + " \n /// " + " Old values : " + ",".join(old_values)

            old_method.set("Description",description)


        _check(myiris, old_class.invoke("%Save"))
        return _rename(_text_from_class(myiris, namespace, old_name), original_name)
    finally:
        for name in (new_name, old_name):
            myiris.classMethodValue("%Dictionary.ClassDefinition", "%DeleteId", name)


def _class_from_text(db: Any, namespace: str, name: str, text: str) -> Any:
    stream = _stream(db, text)
    status = db.classMethodValue( "%Compiler.UDL.TextServices","SetTextFromStream",namespace,name,stream)
    _check(db, status)
    return db.classMethodObject("%Dictionary.ClassDefinition", "%OpenId", name)


def _text_from_class(db: Any, namespace: str, name: str) -> str:
    stream = _stream(db)
    status = db.classMethodValue( "%Compiler.UDL.TextServices", "GetTextAsStream",namespace,name,stream)
    _check(db, status)
    stream.invoke("Rewind")
    parts = []
    while not stream.get("AtEnd"):
        parts.append(stream.invoke("Read", _CHUNK_SIZE))
    return "".join(parts)


def _stream(db: Any, text: str = "") -> Any:
    stream = db.classMethodObject("%Stream.TmpCharacter", "%New")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "\r\n")

    for start in range(0, len(text), _CHUNK_SIZE):
        _check(db, stream.invoke("Write", text[start:start + _CHUNK_SIZE]))

    stream.invoke("Rewind")
    return stream


def _methods(class_definition: Any) -> dict[str, Any]:
    methods = class_definition.getObject("Methods")
    return {
        method.get("Name"): method
        for method in (
            methods.invokeObject("GetAt", index)
            for index in range(1, methods.invoke("Count") + 1)
        )
    }



def _rename(text: str, name: str) -> str:
    if _CLASS_RE.search(text) is None:
        raise ValueError("ObjectScript Class declaration not found")
    return _CLASS_RE.sub(rf"\g<1>{name}", text, count=1)


def _check(db: Any, status: Any) -> None:
    if db.classMethodBoolean("%SYSTEM.Status", "IsError", status):
        message = db.classMethodString("%SYSTEM.Status", "GetErrorText", status)
        raise RuntimeError(message)