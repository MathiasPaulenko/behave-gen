# Architecture

## Package structure

```text
behave_gen/
  cli/              Typer CLI application
    app.py          Command registration and global options
  commands/         One module per CLI command
    init.py         Project scaffolding
    add.py          add feature
    steps.py        add steps
    environment.py  add environment, add config
    check.py        check / doctor
    lint.py         lint
    format.py       format
    from_openapi.py from-openapi
    from_postman.py from-postman
    from_swagger.py from-swagger
    migrate.py      migrate
    preview.py      preview
    stats.py        stats
    update.py       update
  generators/       Pluggable code generators
    openapi.py      OpenAPI generator
    postman.py      Postman generator
  plugins/          Source-specific parsers and builders
    openapi/        OpenAPI parser, feature builder, step builder
    postman/        Postman parser, feature builder
    swagger/        Swagger 2.0 → OpenAPI 3.x converter
    cucumber/       Cucumber migrator
  step_libraries/   Built-in step library templates
    http_steps.py.tpl
    auth_steps.py.tpl
  templates/        Project and feature templates
    default/        Default project template
    features/       Feature file templates (default, crud)
    engine.py       Template engine abstraction
    registry.py     Template registry
    discovery.py    Template discovery
    variants.py     Template variant selection (kit/data wiring)
  config.py         [tool.behave-gen] configuration model
  project.py        Project detection and state
  diagnostics.py    Optional-dependency handling
```

## Design decisions

### Modular monolith

behave-gen is a single package with a plugin-like generator protocol.
Built-in generators live in `behave_gen.generators`. Third-party generators
can register through the `behave_gen.generators` entry point. The CLI, core,
templates, and integrations are part of the same package and deploy.

### Template engine abstraction

The template engine is abstracted behind a common interface. The default
engine uses Python's `string.Template` (no dependencies). Jinja2 is available
as an optional extra for advanced templating.

### Optional dependency strategy

behave-gen requires only `behave`, `behave-model`, and `typer`. Each ecosystem
tool (`behave-doctor`, `behave-lint`, `behave-format`, `behave-kit`,
`behave-data`) is an optional extra. Wrappers check availability at runtime
and print an install hint if missing.

---

## Architecture Decision Records

### ADR-0001: No empty step skeletons

**Status:** Proposed

The original project brief included producing empty step-definition skeletons
with `pass` bodies. Empty skeletons create the illusion of progress but:

- rot immediately when step text changes;
- hide real implementation work;
- encourage copy-paste of `pass` functions;
- do not help users discover reusable step libraries.

**Decision:** `behave-gen` will not emit empty step definitions. Step
implementations are produced only when:

- a reusable step library is added (`behave-gen add steps --lib <lib>`), or
- a generator has enough backend context to emit concrete code
  (`behave-gen from-openapi --step-lib <lib>`), or
- a Cucumber migration translates existing code to Python.

Undefined steps are surfaced by `behave-doctor` through `behave-gen check` and
resolved by adding a library or writing steps manually.

---

### ADR-0002: Modular monolith with plugin generators

**Status:** Proposed

`behave-gen` must support multiple input sources (OpenAPI, Postman, Swagger,
Cucumber) and multiple output targets (project templates, feature files, step
files). The codebase should stay simple enough for a single maintainer but
extensible enough for community generators.

**Decision:** Use a modular monolith: a single package `behave_gen` with a
plugin-like generator protocol. Built-in generators live in
`behave_gen.generators`. Third-party generators can register through the
`behave_gen.generators` entry point.

---

### ADR-0003: Template engine

**Status:** Proposed

Project and file templates are central to `behave-gen`. A powerful template
engine improves user customization, but adding a heavy dependency conflicts
with the zero-deps goal for generated projects and the minimal runtime of
`behave-gen` itself.

**Decision:** Use Python's built-in `string.Template` for all built-in
templates. Support `jinja2` as an optional extra (`behave-gen[jinja2]`) for
custom user templates. The template renderer is abstracted so a future engine
can be added without breaking existing templates.

---

### ADR-0004: Optional dependency strategy

**Status:** Proposed

`behave-gen` integrates with `behave-doctor`, `behave-lint`, `behave-format`,
`behave-kit`, `behave-data`, and future `behave-steplib`. Requiring all of them
would bloat the install and force upgrades that users may not want. Missing
integrations should degrade gracefully.

**Decision:**

- `behave-gen` requires only `behave`, `behave-model`, and `typer`.
- Each ecosystem tool is an optional extra (`doctor`, `lint`, `format`, `kit`,
  `data`, `steplib`) mapped to the corresponding package.
- Wrappers check availability at runtime and print an install hint if missing.
- Generated projects include only the extras selected by the user during
  `init` or added later via `add config`.
