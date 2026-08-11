"""Tests for ``behave-gen add steps --from-recording``."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.steps import (
    AddStepsError,
    add_steps_from_recording,
)
from behave_gen.recording import (
    RecordedAction,
    RecordingError,
    actions_to_feature_content,
    actions_to_gherkin_lines,
    actions_to_step_definitions,
    collect_existing_step_patterns,
    parse_recording,
)

runner = CliRunner()

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "recording"


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


# ---------------------------------------------------------------------------
# parse_recording
# ---------------------------------------------------------------------------


class TestParseRecording:
    def test_parse_valid_recording(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        assert len(actions) == 6
        assert actions[0].action_type == "navigate"
        assert actions[0].url == "https://example.com"
        assert actions[1].action_type == "click"
        assert actions[1].selector == "button#login"
        assert actions[1].text == "Login"
        assert actions[2].action_type == "type"
        assert actions[2].value == "admin"

    def test_parse_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RecordingError, match="not found"):
            parse_recording(tmp_path / "nope.yaml")

    def test_parse_invalid_yaml_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("actions: [this is not valid", encoding="utf-8")
        with pytest.raises(RecordingError, match="Invalid YAML"):
            parse_recording(bad)

    def test_parse_no_actions_key_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "no_actions.yaml"
        bad.write_text("foo: bar\n", encoding="utf-8")
        with pytest.raises(RecordingError, match="actions"):
            parse_recording(bad)

    def test_parse_skips_unsupported_types(self) -> None:
        actions = parse_recording(_FIXTURES / "mixed_actions.yaml")
        assert len(actions) == 1
        assert actions[0].action_type == "navigate"

    def test_parse_empty_actions_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "empty.yaml"
        bad.write_text("actions: []\n", encoding="utf-8")
        with pytest.raises(RecordingError, match="No supported actions"):
            parse_recording(bad)


# ---------------------------------------------------------------------------
# Gherkin generation
# ---------------------------------------------------------------------------


class TestGherkinGeneration:
    def test_gherkin_lines_first_step_keeps_keyword(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert lines[0].startswith("Given ")
        assert lines[1].startswith("And ")
        assert lines[2].startswith("And ")

    def test_gherkin_navigate(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert 'Given I navigate to "https://example.com"' in lines

    def test_gherkin_click_with_selector(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert 'And I click on "button#login"' in lines[1]

    def test_gherkin_click_text_fallback(self) -> None:
        actions = parse_recording(_FIXTURES / "click_text_fallback.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert 'And I click "Login"' in lines

    def test_gherkin_type(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert 'And I enter "admin" into "input#username"' in lines

    def test_gherkin_scroll(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        lines = actions_to_gherkin_lines(actions)
        assert "And I scroll to 500" in lines

    def test_gherkin_scroll_defaults_to_zero(self) -> None:
        """A scroll action with ``y=None`` should produce ``When I scroll to 0``."""
        actions = [RecordedAction(action_type="scroll")]
        lines = actions_to_gherkin_lines(actions)
        assert lines == ["When I scroll to 0"]

    def test_parse_recording_rejects_bool_y(self, tmp_path: Path) -> None:
        """A scroll action with ``y: true`` in YAML must be rejected at parse time."""
        bad = tmp_path / "bool_y.yaml"
        bad.write_text(
            "actions:\n  - type: scroll\n    y: true\n",
            encoding="utf-8",
        )
        with pytest.raises(RecordingError, match="must be an integer"):
            parse_recording(bad)

    def test_parse_recording_rejects_string_y(self, tmp_path: Path) -> None:
        """A scroll action with ``y: abc`` in YAML must be rejected at parse time."""
        bad = tmp_path / "str_y.yaml"
        bad.write_text(
            "actions:\n  - type: scroll\n    y: abc\n",
            encoding="utf-8",
        )
        with pytest.raises(RecordingError, match="must be an integer"):
            parse_recording(bad)

    def test_parse_recording_coerces_float_y(self, tmp_path: Path) -> None:
        """A scroll action with a float ``y`` in YAML should be truncated to int."""
        pytest.importorskip("yaml")
        rec = tmp_path / "float_y.yaml"
        rec.write_text(
            "actions:\n  - type: scroll\n    y: 100.7\n",
            encoding="utf-8",
        )
        actions = parse_recording(rec)
        assert actions[0].y == 100

    def test_gherkin_navigate_missing_url_skipped(self) -> None:
        """A navigate action without url is silently skipped."""
        actions = [RecordedAction(action_type="navigate")]
        lines = actions_to_gherkin_lines(actions)
        assert lines == []

    def test_gherkin_type_missing_fields_skipped(self) -> None:
        """A type action without value or selector is silently skipped."""
        actions = [RecordedAction(action_type="type", value="admin")]
        lines = actions_to_gherkin_lines(actions)
        assert lines == []

    def test_feature_content_has_header(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        content = actions_to_feature_content(actions)
        assert "Feature: Recorded user flow" in content
        assert "Scenario: Recorded session" in content


# ---------------------------------------------------------------------------
# Step definition generation
# ---------------------------------------------------------------------------


class TestStepDefinitions:
    def test_generates_navigate_step(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, generated, _ = actions_to_step_definitions(actions)
        assert "I navigate to" in source
        assert "@given" in source
        assert "def step_navigate" in source
        assert "context.page.navigate(url)" in source

    def test_generates_click_selector_step(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, generated, _ = actions_to_step_definitions(actions)
        assert 'I click on "{selector}"' in source
        assert "def step_click_selector" in source
        assert "context.page.click(selector)" in source

    def test_generates_click_text_step(self) -> None:
        actions = parse_recording(_FIXTURES / "click_text_fallback.yaml")
        source, generated, _ = actions_to_step_definitions(actions)
        assert 'I click "{text}"' in source
        assert "def step_click_text" in source

    def test_generates_type_step(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, generated, _ = actions_to_step_definitions(actions)
        assert 'I enter "{value}" into "{selector}"' in source
        assert "def step_type" in source
        assert "context.page.fill(selector, value)" in source

    def test_generates_scroll_step(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, generated, _ = actions_to_step_definitions(actions)
        assert "I scroll to {y}" in source
        assert "def step_scroll" in source

    def test_no_pass_skeletons(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, _, _ = actions_to_step_definitions(actions)
        assert "\n    pass\n" not in source

    def test_deduplication_within_recording(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        source, generated, skipped = actions_to_step_definitions(actions)
        # Two click actions with selector -> only one step def generated.
        assert 'I click on "{selector}"' in generated
        # The second click (submit button) is skipped.
        assert len(skipped) >= 1

    def test_deduplication_with_existing_patterns(self) -> None:
        actions = parse_recording(_FIXTURES / "sample_recording.yaml")
        existing = {'I navigate to "{url}"'}
        source, generated, skipped = actions_to_step_definitions(
            actions, existing_patterns=existing
        )
        assert 'I navigate to "{url}"' not in generated
        assert 'I navigate to "{url}"' in skipped
        assert 'I click on "{selector}"' in generated

    def test_all_existing_returns_empty_source(self) -> None:
        actions = parse_recording(_FIXTURES / "click_text_fallback.yaml")
        existing = {
            'I navigate to "{url}"',
            'I click on "{selector}"',
            'I click "{text}"',
        }
        source, generated, skipped = actions_to_step_definitions(
            actions, existing_patterns=existing
        )
        assert source == ""
        assert len(generated) == 0
        assert len(skipped) >= 1


# ---------------------------------------------------------------------------
# collect_existing_step_patterns
# ---------------------------------------------------------------------------


class TestCollectExistingPatterns:
    def test_collects_from_python_file(self, tmp_path: Path) -> None:
        steps_dir = tmp_path / "steps"
        steps_dir.mkdir()
        (steps_dir / "existing.py").write_text(
            textwrap.dedent(
                """
                from behave import given, when

                @given('I navigate to "{url}"')
                def step_navigate(context, url):
                    pass

                @when('I click on "{selector}"')
                def step_click(context, selector):
                    pass
                """
            ),
            encoding="utf-8",
        )
        patterns = collect_existing_step_patterns(steps_dir)
        assert 'I navigate to "{url}"' in patterns
        assert 'I click on "{selector}"' in patterns

    def test_empty_dir_returns_empty_set(self, tmp_path: Path) -> None:
        steps_dir = tmp_path / "steps"
        steps_dir.mkdir()
        assert collect_existing_step_patterns(steps_dir) == set()

    def test_nonexistent_dir_returns_empty_set(self, tmp_path: Path) -> None:
        assert collect_existing_step_patterns(tmp_path / "nope") == set()


# ---------------------------------------------------------------------------
# add_steps_from_recording (integration)
# ---------------------------------------------------------------------------


class TestAddStepsFromRecording:
    def test_generates_steps_and_feature(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        steps_path, feature_path, generated, skipped = add_steps_from_recording(
            root, _FIXTURES / "sample_recording.yaml"
        )
        assert steps_path.is_file()
        assert feature_path is not None
        assert feature_path.is_file()
        content = steps_path.read_text(encoding="utf-8")
        assert "from behave import given, when" in content
        assert "def step_navigate" in content
        assert "def step_click_selector" in content
        assert "def step_type" in content
        assert len(generated) >= 4

    def test_feature_content_correct(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        _, feature_path, _, _ = add_steps_from_recording(root, _FIXTURES / "sample_recording.yaml")
        assert feature_path is not None
        content = feature_path.read_text(encoding="utf-8")
        assert "Feature: Recorded user flow" in content
        assert 'Given I navigate to "https://example.com"' in content
        assert 'And I click on "button#login"' in content

    def test_existing_steps_file_raises(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        add_steps_from_recording(root, _FIXTURES / "sample_recording.yaml")
        with pytest.raises(AddStepsError, match="already exists"):
            add_steps_from_recording(root, _FIXTURES / "sample_recording.yaml")

    def test_existing_feature_file_skipped(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        # Pre-create the feature file.
        feature = root / "features" / "recorded.feature"
        feature.parent.mkdir(parents=True, exist_ok=True)
        feature.write_text("Feature: Custom\n", encoding="utf-8")
        _, feature_path, _, _ = add_steps_from_recording(root, _FIXTURES / "sample_recording.yaml")
        assert feature_path is None
        # Original content preserved.
        assert "Custom" in feature.read_text(encoding="utf-8")

    def test_missing_project_raises(self, tmp_path: Path) -> None:
        with pytest.raises(AddStepsError, match="Project root not found"):
            add_steps_from_recording(tmp_path / "nope", _FIXTURES / "sample_recording.yaml")

    def test_missing_recording_raises(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        with pytest.raises(AddStepsError, match="not found"):
            add_steps_from_recording(root, tmp_path / "nope.yaml")

    def test_dedup_with_existing_step_file(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        steps_dir = root / "features" / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)
        # Write an existing step file with a navigate pattern.
        (steps_dir / "existing.py").write_text(
            textwrap.dedent(
                """
                from behave import given

                @given('I navigate to "{url}"')
                def step_navigate(context, url):
                    context.page.navigate(url)
                """
            ),
            encoding="utf-8",
        )
        _, _, generated, skipped = add_steps_from_recording(
            root, _FIXTURES / "sample_recording.yaml"
        )
        assert 'I navigate to "{url}"' not in generated
        assert 'I navigate to "{url}"' in skipped

    def test_click_text_fallback(self, tmp_path: Path) -> None:
        root = _make_project(tmp_path)
        steps_path, _, generated, _ = add_steps_from_recording(
            root, _FIXTURES / "click_text_fallback.yaml"
        )
        content = steps_path.read_text(encoding="utf-8")
        assert 'I click "{text}"' in content
        assert "def step_click_text" in content
        assert 'I click "{text}"' in generated


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestCliFromRecording:
    def test_cli_from_recording(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        result = runner.invoke(
            app,
            ["add", "steps", "--from-recording", str(_FIXTURES / "sample_recording.yaml")],
        )
        assert result.exit_code == 0, result.output
        assert (root / "features" / "steps" / "recorded_steps.py").is_file()
        assert (root / "features" / "recorded.feature").is_file()
        assert "Generated step definitions" in result.output

    def test_cli_no_lib_no_recording_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        result = runner.invoke(app, ["add", "steps"])
        assert result.exit_code == 1
        assert "Either --lib or --from-recording" in result.output

    def test_cli_combined_lib_and_recording(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        result = runner.invoke(
            app,
            [
                "add",
                "steps",
                "--lib",
                "http",
                "--from-recording",
                str(_FIXTURES / "sample_recording.yaml"),
            ],
        )
        assert result.exit_code == 0, result.output
        assert (root / "features" / "steps" / "http_steps.py").is_file()
        assert (root / "features" / "steps" / "recorded_steps.py").is_file()
        assert (root / "features" / "recorded.feature").is_file()
        assert "Added step library" in result.output
        assert "Generated step definitions" in result.output

    def test_cli_recording_file_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        result = runner.invoke(
            app, ["add", "steps", "--from-recording", str(tmp_path / "nope.yaml")]
        )
        assert result.exit_code == 1
        assert "not found" in result.output
