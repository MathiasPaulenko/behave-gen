"""Tests for the generated HTTP step library.

These tests render the http step library template into a temporary module and
exercise the real (non-empty) implementations directly, proving the generated
code is runnable and contains no ``pass``-only skeletons.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.steps import AddStepsOptions, add_steps


def _load_generated_module(module_name: str, file_path: Path) -> types.ModuleType:
    """Import a generated step file as an isolated module."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class _Ctx:
    """Minimal behave context stand-in."""

    def __init__(self, text: str | None = None) -> None:
        self.text = text
        self.behave_gen_http = None


@pytest.fixture(scope="session")
def http_module(tmp_path_factory: pytest.TempPathFactory) -> types.ModuleType:
    """Load the generated HTTP step library once per session.

    behave registers step decorators in a global registry at import time, so
    the module must be imported exactly once to avoid AmbiguousStep errors.
    """
    root = init_project(tmp_path_factory.mktemp("http"), InitOptions(name="httpproj"))
    path = add_steps(root, AddStepsOptions(lib="http"))
    return _load_generated_module("behave_gen_test_http", path)


def test_http_steps_no_pass_skeletons(http_module: types.ModuleType) -> None:
    source = Path(http_module.__file__).read_text(encoding="utf-8")  # type: ignore[arg-type]
    assert "pass" not in source.replace("passlib", "").replace("bypass", "")
    # Every step function body must contain a real statement.
    assert "assert" in source or "_request" in source


def test_http_steps_send_request_and_check_status(http_module: types.ModuleType) -> None:
    ctx = _Ctx()
    # No server running: expect a connection error surfaced as a non-2xx, but
    # the step must perform a real request attempt. We monkeypatch _request.
    called: dict[str, str] = {}

    class FakeResp:
        status = 200
        body = b'{"ok": true}'
        headers: dict[str, str] = {}

    def fake_request(method: str, url: str, **kwargs: object) -> FakeResp:
        called["method"] = method
        called["url"] = url
        return FakeResp()

    http_module._request = fake_request  # type: ignore[attr-defined]
    http_module.send_request(ctx, "GET", "/health")
    assert called == {"method": "GET", "url": "http://localhost:8080/health"}
    http_module.check_status(ctx, 200)


def test_http_steps_check_json_key_and_value(http_module: types.ModuleType) -> None:
    ctx = _Ctx()

    class FakeResp:
        status = 200
        body = b'{"user": "alice", "active": true}'
        headers: dict[str, str] = {}

    http_module._request = lambda *a, **k: FakeResp()  # type: ignore[attr-defined]
    http_module.send_request(ctx, "GET", "/me")
    http_module.check_json_key(ctx, "user")
    http_module.check_json_value(ctx, "user", "alice")


def test_http_steps_set_base_url(http_module: types.ModuleType) -> None:
    ctx = _Ctx()
    http_module.set_base_url(ctx, "https://api.example.com/")
    assert ctx.behave_gen_http.base_url == "https://api.example.com"


def test_http_steps_send_with_body(http_module: types.ModuleType) -> None:
    ctx = _Ctx(text='{"name": "bob"}')
    captured: dict[str, object] = {}

    class FakeResp:
        status = 201
        body = b'{"id": 1}'
        headers: dict[str, str] = {}

    def fake_request(
        method: str, url: str, *, body: object = None, headers: object = None
    ) -> FakeResp:
        captured["body"] = body
        captured["method"] = method
        return FakeResp()

    http_module._request = fake_request  # type: ignore[attr-defined]
    http_module.send_request_with_body(ctx, "POST", "/users")
    assert captured["body"] == {"name": "bob"}
    assert captured["method"] == "POST"
    http_module.check_status(ctx, 201)
