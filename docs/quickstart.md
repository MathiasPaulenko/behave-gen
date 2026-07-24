# Quick Start

This guide walks through the most common behave-gen workflows.

## 1. Create a project

```bash
behave-gen init my-project
cd my-project
```

This creates:

```text
my-project/
  features/
    sample.feature      Placeholder feature (replace or remove)
    steps/
      .gitkeep
  environment.py        Behave hooks (before/after scenario)
  behave.toml           Behave configuration
  pyproject.toml        Project metadata + [tool.behave-gen] config
  README.md
```

Verify the project runs:

```bash
behave --dry-run
```

## 2. Add a feature

```bash
behave-gen add feature login --tags smoke,auth
```

Creates `features/login.feature`:

```gherkin
@smoke @auth
Feature: Login
  Description for Login.

  Scenario: Login scenario
    Given a precondition for Login
    When an action is performed
    Then the result is observed
```

Use the CRUD template for scenario outlines:

```bash
behave-gen add feature checkout --template crud --tags regression
```

See [Feature Templates](templates.md) for details.

## 3. Add step definitions

```bash
behave-gen add steps --lib http
behave-gen add steps --lib auth
```

This copies real, runnable step libraries into `features/steps/`:

- `http_steps.py` — HTTP requests with `urllib` (no extra dependencies).
- `auth_steps.py` — Session and authentication state management.

See [Step Libraries](step-libraries.md) for the full list of available steps.

## 4. Write features that use the step libraries

The placeholder templates use generic step text. Replace them with steps
that match the libraries you added:

```gherkin
@smoke @auth
Feature: Login
  Scenario: Successful login
    Given the base URL is "http://localhost:8080"
    And I am not authenticated
    When I send a POST request to "/auth/login" with body
      """
      {"username": "admin", "password": "secret"}
      """
    Then the response status should be 200
    And the response JSON should contain "token"
```

## 5. Check project health

```bash
behave-gen check
```

Runs [behave-doctor](https://pypi.org/project/behave-doctor/) diagnostics and
reports undefined steps, unused definitions, and other issues.

## 6. Run tests

```bash
behave
```

## 7. Generate from an OpenAPI spec

```bash
behave-gen from-openapi spec.yaml --out-dir gen --step-lib http --tag api
```

Produces `.feature` files grouped by path, each with scenarios that use the
HTTP step library. See [Generators](generators.md).

## 8. Migrate from Cucumber

```bash
behave-gen migrate path/to/cucumber-project --out-dir migrated
```

Copies `.feature` files into a Behave layout. See
[Cucumber Migration](migration.md).

## 9. Report statistics

```bash
behave-gen stats
```

```text
Project: my-project
  Features:         3
  Scenarios:        2
  Scenario outlines: 1
  Steps:            9
  Tags:             3
  Files:            3
```

## 10. Preview a feature

```bash
behave-gen preview features/login.feature
```

Pretty-prints the feature with resolved examples and tables.
