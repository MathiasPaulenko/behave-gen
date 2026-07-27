# Feature Templates

`behave-gen add feature` generates `.feature` files from templates. Two
templates are built-in.

## default

The `default` template produces a single scenario with placeholder steps:

```bash
behave-gen add feature login
```

```gherkin
Feature: Login
  Description for Login.

  Scenario: Login scenario
    Given a precondition for Login
    When an action is performed
    Then the result is observed
```

With tags:

```bash
behave-gen add feature login --tags smoke,auth
```

```gherkin
@smoke @auth
Feature: Login
  Description for Login.

  Scenario: Login scenario
    Given a precondition for Login
    When an action is performed
    Then the result is observed
```

The placeholder steps (`Given a precondition for...`, `When an action is
performed`, `Then the result is observed`) are intentionally generic. Replace
them with steps from a [step library](step-libraries.md) or your own
definitions.

## crud

The `crud` template produces a scenario outline with create, read, update, and
delete steps, plus an examples table:

```bash
behave-gen add feature checkout --template crud
```

```gherkin
Feature: Checkout
  CRUD scenarios for Checkout.

  Background:
    Given a clean state for Checkout

  Scenario Outline: create, read, update, and delete Checkout
    When I create a Checkout with "<value>"
    Then I can read the Checkout with "<value>"
    When I update the Checkout to "<new_value>"
    Then I can read the Checkout with "<new_value>"
    When I delete the Checkout
    Then the Checkout no longer exists

    Examples:
      | value   | new_value  |
      | alpha   | alpha-upd  |
      | beta    | beta-upd   |
```

The CRUD steps are also generic placeholders. Implement them in
`features/steps/` or use the [HTTP step library](step-libraries.md#http-step-library)
for API-backed CRUD operations.

## Custom templates

Place custom `.feature` templates in your project's `templates_dir` (default:
`templates/`). The template engine is configured via
[`template_engine` in `pyproject.toml`](configuration.md#template-engine).

### string engine

```text
${tags}Feature: $feature_name
  Description for $feature_name.

  Scenario: $feature_name scenario
    Given a precondition for $feature_name
```

### jinja2 engine

```text
{{ tags }}Feature: {{ feature_name }}
  Description for {{ feature_name }}.

  Scenario: {{ feature_name }} scenario
    Given a precondition for {{ feature_name }}
```

!!! note "Tags include a trailing newline"

    The `tags` variable already contains a trailing `\n` when tags are
    present (e.g. `@smoke @auth\n`). This means `${tags}Feature:` renders
    as two lines — tags on their own line, then `Feature:` on the next —
    which is valid Gherkin. When no tags are provided, `tags` is empty and
    the line collapses to just `Feature:`.

### Template variables

| Variable | Description |
| -------- | ----------- |
| `feature_name` | Humanized feature name (e.g. `user_login` → `User login`). |
| `name` | Raw feature name as passed on the CLI. |
| `tags` | Tags line including trailing newline (e.g. `@smoke @auth\n`), or empty string when no tags are set. |
