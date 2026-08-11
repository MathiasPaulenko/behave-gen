"""Parse wavexis recording YAML and generate Behave step definitions.

A *recording* is a YAML file produced by ``wavexis record`` (or compatible
tools) that contains a list of browser actions.  This module converts those
actions into:

* **Gherkin steps** – textual lines suitable for a ``.feature`` file.
* **Python step definitions** – ``@given``/``@when``/``@then`` decorated
  functions with real (non-``pass``) bodies.

Supported action types (first version):

============  =================================================
``navigate``  ``Given I navigate to "{url}"``
``click``     ``When I click on "{selector}"`` *or*
              ``When I click "{text}"`` (fallback when no selector)
``type``      ``When I enter "{value}" into "{selector}"``
``scroll``    ``When I scroll to {y}``
============  =================================================

Other action types are silently skipped (future improvement).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "RecordedAction",
    "RecordingError",
    "RecordingResult",
    "actions_to_feature_content",
    "actions_to_gherkin_lines",
    "actions_to_step_definitions",
    "collect_existing_step_patterns",
    "parse_recording",
]


class RecordingError(Exception):
    """User-facing error raised during recording parsing or code generation."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RecordedAction:
    """A single browser action extracted from a wavexis recording."""

    action_type: str
    url: str | None = None
    selector: str | None = None
    text: str | None = None
    value: str | None = None
    x: int | None = None
    y: int | None = None


@dataclass(frozen=True, slots=True)
class RecordingResult:
    """Outcome of processing a recording.

    ``generated_steps`` – step definition patterns that were *newly* generated.
    ``skipped_steps``    – step definition patterns that already existed.
    ``gherkin_lines``    – all Gherkin step lines (including skipped ones).
    """

    generated_steps: tuple[str, ...]
    skipped_steps: tuple[str, ...]
    gherkin_lines: tuple[str, ...]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


_SUPPORTED_TYPES = frozenset({"navigate", "click", "type", "scroll"})


def parse_recording(path: str | Path) -> list[RecordedAction]:
    """Read and parse a wavexis recording YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        A list of :class:`RecordedAction` objects.

    Raises:
        RecordingError: If the file cannot be read, is not valid YAML, or
            does not contain an ``actions`` list.

    """
    p = Path(path)
    if not p.is_file():
        raise RecordingError(f"Recording file not found: {p}")
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordingError(f"Could not read recording {p}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise RecordingError(f"Could not decode recording {p}: {exc}") from exc

    try:
        import yaml  # noqa: PLC0415 - optional extra.
    except ImportError as exc:
        raise RecordingError(
            "YAML support requires pyyaml. Install with: pip install pyyaml"
        ) from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise RecordingError(f"Invalid YAML in recording {p}: {exc}") from exc

    if not isinstance(data, dict):
        raise RecordingError(f"Recording must be a YAML mapping, got {type(data).__name__}.")
    actions_raw = data.get("actions")
    if not isinstance(actions_raw, list):
        raise RecordingError("Recording must contain an 'actions' list.")

    actions: list[RecordedAction] = []
    for i, item in enumerate(actions_raw):
        if not isinstance(item, dict):
            raise RecordingError(f"Action #{i} is not a mapping: {item!r}")
        action_type = item.get("type")
        if not isinstance(action_type, str):
            raise RecordingError(f"Action #{i} missing 'type' field.")
        if action_type not in _SUPPORTED_TYPES:
            continue
        actions.append(
            RecordedAction(
                action_type=action_type,
                url=item.get("url"),
                selector=item.get("selector"),
                text=item.get("text"),
                value=item.get("value"),
                x=_coerce_int(item.get("x"), "x", i),
                y=_coerce_int(item.get("y"), "y", i),
            )
        )
    if not actions:
        raise RecordingError("No supported actions found in recording.")
    return actions


# ---------------------------------------------------------------------------
# Gherkin generation
# ---------------------------------------------------------------------------


def _gherkin_navigate(action: RecordedAction) -> str | None:
    if not action.url:
        return None
    return f'Given I navigate to "{action.url}"'


def _gherkin_click(action: RecordedAction) -> str | None:
    if action.selector:
        return f'When I click on "{action.selector}"'
    if action.text:
        return f'When I click "{action.text}"'
    return None


def _gherkin_type(action: RecordedAction) -> str | None:
    if not action.value or not action.selector:
        return None
    return f'When I enter "{action.value}" into "{action.selector}"'


def _coerce_int(value: object, field_name: str, index: int) -> int | None:
    """Validate that *value* is an int or None, rejecting bools and other types."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise RecordingError(f"Action #{index} field '{field_name}' must be an integer, got bool.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    raise RecordingError(
        f"Action #{index} field '{field_name}' must be an integer, got {type(value).__name__}."
    )


def _gherkin_scroll(action: RecordedAction) -> str | None:
    y = action.y if action.y is not None else 0
    return f"When I scroll to {y}"


_GHERKIN_DISPATCH: dict[str, Callable[[RecordedAction], str | None]] = {
    "navigate": _gherkin_navigate,
    "click": _gherkin_click,
    "type": _gherkin_type,
    "scroll": _gherkin_scroll,
}


def _gherkin_line(action: RecordedAction) -> str | None:
    """Convert a single action to a Gherkin step line, or ``None`` if unsupported."""
    handler = _GHERKIN_DISPATCH.get(action.action_type)
    if handler is None:
        return None
    return handler(action)


def actions_to_gherkin_lines(actions: list[RecordedAction]) -> list[str]:
    """Convert actions to Gherkin step lines.

    The first step keeps its original keyword; subsequent steps use ``And``.
    """
    lines: list[str] = []
    for action in actions:
        line = _gherkin_line(action)
        if line is None:
            continue
        if lines:
            keyword = line.split(" ", 1)[0]
            rest = line[len(keyword) + 1 :]
            lines.append(f"And {rest}")
        else:
            lines.append(line)
    return lines


def actions_to_feature_content(actions: list[RecordedAction]) -> str:
    """Build a complete ``.feature`` file from recorded actions."""
    lines = actions_to_gherkin_lines(actions)
    body = "\n".join(f"    {line}" for line in lines)
    return f"Feature: Recorded user flow\n\n  Scenario: Recorded session\n{body}\n"


# ---------------------------------------------------------------------------
# Step definition generation
# ---------------------------------------------------------------------------


# Maps a *step pattern key* (the decorator string without the keyword prefix)
# to (function_name, decorator_keyword, body_statement).
_STEP_TEMPLATES: dict[str, tuple[str, str, str]] = {
    'I navigate to "{url}"': (
        "step_navigate",
        "given",
        "    context.page.navigate(url)",
    ),
    'I click on "{selector}"': (
        "step_click_selector",
        "when",
        "    context.page.click(selector)",
    ),
    'I click "{text}"': (
        "step_click_text",
        "when",
        "    context.page.click(f\"text='{text}'\")",
    ),
    'I enter "{value}" into "{selector}"': (
        "step_type",
        "when",
        "    context.page.fill(selector, value)",
    ),
    "I scroll to {y}": (
        "step_scroll",
        "when",
        '    context.page.evaluate(f"window.scrollTo(0, {y})")',
    ),
}


def _key_navigate(action: RecordedAction) -> str | None:
    if not action.url:
        return None
    return 'I navigate to "{url}"'


def _key_click(action: RecordedAction) -> str | None:
    if action.selector:
        return 'I click on "{selector}"'
    if action.text:
        return 'I click "{text}"'
    return None


def _key_type(action: RecordedAction) -> str | None:
    if not action.value or not action.selector:
        return None
    return 'I enter "{value}" into "{selector}"'


def _key_scroll(_action: RecordedAction) -> str | None:
    return "I scroll to {y}"


_KEY_DISPATCH: dict[str, Callable[[RecordedAction], str | None]] = {
    "navigate": _key_navigate,
    "click": _key_click,
    "type": _key_type,
    "scroll": _key_scroll,
}


def _step_pattern_key(action: RecordedAction) -> str | None:
    """Return the template key for an action, or ``None`` if unsupported."""
    handler = _KEY_DISPATCH.get(action.action_type)
    if handler is None:
        return None
    return handler(action)


def actions_to_step_definitions(
    actions: list[RecordedAction],
    *,
    existing_patterns: set[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    """Generate Python step definitions from recorded actions.

    Args:
        actions: Recorded actions to convert.
        existing_patterns: Step decorator patterns already present in the
            project.  Matching patterns are skipped (deduplicated).

    Returns:
        A tuple of ``(source_code, generated_patterns, skipped_patterns)``.

    """
    if existing_patterns is None:
        existing_patterns = set()

    # Preserve order while deduplicating within the recording itself.
    seen: set[str] = set()
    generated: list[str] = []
    skipped: list[str] = []

    for action in actions:
        key = _step_pattern_key(action)
        if key is None:
            continue
        if key in existing_patterns or key in seen:
            skipped.append(key)
            continue
        seen.add(key)
        generated.append(key)

    if not generated:
        return "", generated, skipped

    lines: list[str] = [
        '"""Step definitions generated from a wavexis recording.',
        "",
        "Generated by behave-gen. Each function performs a real browser",
        "action via ``context.page`` (a Playwright/wavexis page object).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from behave import given, when",
        "",
        "",
    ]

    for i, key in enumerate(generated):
        func_name, decorator, body = _STEP_TEMPLATES[key]
        lines.append(f"@{decorator}('{key}')")
        lines.append(f"def {func_name}(context: Any) -> None:")
        # Extract parameter names from the template key for the signature.
        params = re.findall(r"\{(\w+)\}", key)
        if params:
            sig = ", ".join(f"{p}: str" for p in params)
            lines[-1] = f"def {func_name}(context: Any, {sig}) -> None:"
        lines.append(body)
        if i < len(generated) - 1:
            lines.append("")
            lines.append("")

    return "\n".join(lines) + "\n", generated, skipped


# ---------------------------------------------------------------------------
# Deduplication helpers
# ---------------------------------------------------------------------------


_DECORATOR_RE = re.compile(
    r"""@(?:given|when|then)\s*\(\s*['"](.+?)['"]\s*\)""",
    re.DOTALL,
)


def collect_existing_step_patterns(steps_dir: str | Path) -> set[str]:
    """Scan ``steps_dir`` for existing step decorator patterns.

    Returns a set of pattern strings (e.g. ``'I navigate to "{url}"'``)
    found in ``.py`` files within the directory.
    """
    directory = Path(steps_dir)
    if not directory.is_dir():
        return set()
    patterns: set[str] = set()
    for py_file in directory.glob("*.py"):
        if py_file.is_symlink():
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in _DECORATOR_RE.finditer(text):
            patterns.add(match.group(1))
    return patterns
