"""``behave-gen add steps`` command implementation.

Copies a built-in step library (a real, runnable step-definition module) into
a project's ``features/steps/`` directory. No empty ``pass`` skeletons are
ever emitted (see ``ref/adr/0001-no-empty-step-skeletons.md``).
"""

from __future__ import annotations

import string
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import resolve_project_root, safe_write_text
from behave_gen.project import Project, ProjectError
from behave_gen.recording import (
    RecordedAction,
    RecordingError,
    actions_to_feature_content,
    actions_to_step_definitions,
    collect_existing_step_patterns,
    parse_recording,
)

_STEP_LIB_ROOT = "behave_gen.step_libraries"

# Built-in libraries: name -> (template filename, output filename).
_BUILTIN_LIBRARIES: dict[str, tuple[str, str]] = {
    "http": ("http_steps.py.tpl", "http_steps.py"),
    "auth": ("auth_steps.py.tpl", "auth_steps.py"),
}


class AddStepsError(Exception):
    """User-facing error raised by ``add steps``."""


@dataclass(frozen=True, slots=True)
class AddStepsOptions:
    """Options for ``add steps``.

    Either ``lib`` or ``from_recording`` must be provided (both may be
    combined: the library is copied first, then recording-derived steps are
    deduplicated against it).
    """

    lib: str | None = None
    from_recording: str | Path | None = None


def _load_step_template(template_name: str) -> str:
    with resources.as_file(resources.files(_STEP_LIB_ROOT).joinpath(template_name)) as p:
        path = Path(p)
        if not path.is_file():
            raise AddStepsError(f"Step library template not found: {template_name}.")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AddStepsError(f"Could not read template {template_name}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise AddStepsError(f"Could not decode template {template_name}: {exc}") from exc


def _available_libraries() -> tuple[str, ...]:
    return tuple(sorted(_BUILTIN_LIBRARIES))


def add_steps(
    project_root: str | Path,
    options: AddStepsOptions,
    *,
    steps_dir: str | Path = "features/steps",
    output_file: str | Path | None = None,
) -> Path:
    """Copy a step library into ``project_root``'s steps directory.

    Args:
        project_root: Root of the Behave project.
        options: Add-steps options.
        steps_dir: Steps directory relative to ``project_root``.
        output_file: Optional explicit target path. When omitted the standard
            library filename inside ``steps_dir`` is used.

    Returns:
        The path to the written step-definition file.

    Raises:
        AddStepsError: If the project is missing, the library is unknown, or
            the file already exists.

    """
    if options.lib is None:
        raise AddStepsError("No step library specified.")
    if options.lib not in _BUILTIN_LIBRARIES:
        available = ", ".join(_available_libraries())
        raise AddStepsError(f"Unknown step library {options.lib!r}. Available: {available}.")

    root = Path(project_root).resolve()
    if not root.is_dir():
        raise AddStepsError(f"Project root not found: {root}")

    steps = (root / steps_dir).resolve()
    if not steps.is_relative_to(root):
        raise AddStepsError(f"Steps directory {steps} escapes project root {root}.")
    try:
        steps.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AddStepsError(f"Could not create steps directory {steps}: {exc}") from exc

    template_name, output_name = _BUILTIN_LIBRARIES[options.lib]
    if output_file is None:
        target = steps / output_name
    else:
        target = Path(output_file)
        if not target.is_absolute():
            target = steps / output_file
        target = target.resolve()
    if not target.is_relative_to(steps):
        raise AddStepsError(f"Step file {target} must be inside steps directory {steps}.")
    if target.exists() or target.is_symlink():
        raise AddStepsError(
            f"Step file already exists: {target}. Remove it or choose another library."
        )

    raw = _load_step_template(template_name)
    project_name = root.name.replace("\\", "\\\\").replace('"', '\\"')
    try:
        rendered = string.Template(raw).substitute(project_name=project_name)
    except KeyError as exc:
        key = exc.args[0] if exc.args else "<unknown>"
        raise AddStepsError(f"Missing template variable ${key}.") from exc

    try:
        safe_write_text(target, rendered)
    except OSError as exc:
        raise AddStepsError(f"Could not write step file {target}: {exc}") from exc
    return target


def _ensure_dir(root: Path, subdir: str | Path, label: str) -> Path:
    """Resolve and create a subdirectory inside ``root``, validating containment."""
    directory = (root / subdir).resolve()
    if not directory.is_relative_to(root):
        raise AddStepsError(f"{label} directory {directory} escapes project root {root}.")
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AddStepsError(f"Could not create {label} directory {directory}: {exc}") from exc
    return directory


def _write_steps_file(target: Path, source: str) -> None:
    """Write step definitions (or a marker file when all steps already exist)."""
    content = (
        source
        if source
        else '"""All steps from the recording already exist in this project.\n"""\n'
    )
    try:
        safe_write_text(target, content)
    except OSError as exc:
        raise AddStepsError(f"Could not write step file {target}: {exc}") from exc


def _write_feature_file(
    features: Path, filename: str, actions: list[RecordedAction]
) -> Path | None:
    """Write a feature file from actions, skipping if it already exists."""
    target = features / filename
    if not target.is_relative_to(features):
        raise AddStepsError(f"Feature file {target} must be inside features directory {features}.")
    if target.exists() or target.is_symlink():
        return None
    try:
        safe_write_text(target, actions_to_feature_content(actions))
    except OSError as exc:
        raise AddStepsError(f"Could not write feature file {target}: {exc}") from exc
    return target


@dataclass(frozen=True, slots=True)
class RecordingOutput:
    """Output filenames for recording-derived steps and features."""

    steps_filename: str = "recorded_steps.py"
    feature_filename: str = "recorded.feature"


def add_steps_from_recording(
    project_root: str | Path,
    recording_path: str | Path,
    *,
    steps_dir: str | Path = "features/steps",
    features_dir: str | Path = "features",
    output: RecordingOutput | None = None,
) -> tuple[Path, Path | None, list[str], list[str]]:
    """Generate step definitions and a feature file from a wavexis recording.

    Args:
        project_root: Root of the Behave project.
        recording_path: Path to the wavexis recording YAML file.
        steps_dir: Steps directory relative to ``project_root``.
        features_dir: Features directory relative to ``project_root``.
        output: Output filenames for generated step definitions and feature
            file. Defaults to ``recorded_steps.py`` and ``recorded.feature``.

    Returns:
        A tuple of ``(steps_path, feature_path_or_None, generated, skipped)``.

    Raises:
        AddStepsError: If the project is missing, paths escape the project
            root, the recording is invalid, or output files already exist.

    """
    out = output or RecordingOutput()
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise AddStepsError(f"Project root not found: {root}")

    steps = _ensure_dir(root, steps_dir, "Steps")
    features = _ensure_dir(root, features_dir, "Features")

    try:
        actions = parse_recording(recording_path)
    except RecordingError as exc:
        raise AddStepsError(str(exc)) from exc

    existing = collect_existing_step_patterns(steps)
    source, generated, skipped = actions_to_step_definitions(actions, existing_patterns=existing)

    steps_target = steps / out.steps_filename
    if not steps_target.is_relative_to(steps):
        raise AddStepsError(f"Step file {steps_target} must be inside steps directory {steps}.")
    if steps_target.exists() or steps_target.is_symlink():
        raise AddStepsError(
            f"Step file already exists: {steps_target}. Remove it or choose another name."
        )
    _write_steps_file(steps_target, source)

    feature_path = _write_feature_file(features, out.feature_filename, actions)
    return steps_target, feature_path, generated, skipped


def _print_recording_result(
    steps_path: Path,
    feature_path: Path | None,
    generated: list[str],
    skipped: list[str],
) -> None:
    """Print a human-readable summary of the recording-to-steps conversion."""
    print(f"Generated step definitions at {steps_path}")
    if feature_path is not None:
        print(f"Generated feature file at {feature_path}")
    else:
        print("Feature file already exists - skipped.")
    if generated:
        print(f"New step patterns ({len(generated)}):")
        for pattern in generated:
            print(f"  - {pattern}")
    if skipped:
        print(f"Skipped duplicate patterns ({len(skipped)}):")
        for pattern in skipped:
            print(f"  - {pattern}")
    if not generated and not skipped:
        print("No supported actions found in recording.")


def run_add_steps(
    options: AddStepsOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen add steps``."""
    if options.lib is None and options.from_recording is None:
        print(
            "add steps: Either --lib or --from-recording must be specified.",
            file=sys.stderr,
        )
        return 1

    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"add steps: {exc}", file=sys.stderr)
        return 1

    if options.lib is not None:
        try:
            path = add_steps(project.root, options, steps_dir=project.steps_dir)
        except AddStepsError as exc:
            print(f"add steps: {exc}", file=sys.stderr)
            return 1
        print(f"Added step library {options.lib!r} at {path}")

    if options.from_recording is not None:
        try:
            steps_path, feature_path, generated, skipped = add_steps_from_recording(
                project.root,
                options.from_recording,
                steps_dir=project.steps_dir,
                features_dir=project.features_dir,
            )
        except AddStepsError as exc:
            print(f"add steps: {exc}", file=sys.stderr)
            return 1
        _print_recording_result(steps_path, feature_path, generated, skipped)

    return 0
