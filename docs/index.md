# behave-gen

**CLI toolkit for scaffolding and evolving Behave BDD projects.**

`behave-gen` helps you create, extend, and maintain Behave (Python BDD)
projects. It scaffolds new projects, generates `.feature` files and concrete
step definitions, integrates ecosystem tools (behave-doctor, behave-lint,
behave-format), and migrates Cucumber projects to Behave.

---

## What can behave-gen do?

- **Scaffold** a new Behave project with `init`.
- **Generate** `.feature` files from templates or from OpenAPI / Postman /
  Swagger specs.
- **Add** real, runnable step libraries (HTTP, auth) — no empty skeletons.
- **Migrate** Cucumber (Java) projects to Behave.
- **Check** project health with behave-doctor diagnostics.
- **Lint** and **format** `.feature` files.
- **Report** statistics and preview features.
- **Update** generated files to the latest behave-gen versions.

## Quick example

```bash
behave-gen init my-project
cd my-project
behave-gen add feature login --tags smoke,auth
behave-gen add steps --lib http
behave-gen check
behave
```

## Design principles

- **Minimal dependencies** — only `behave`, `behave-model`, and `typer` at
  runtime. Everything else is an optional extra.
- **No empty skeletons** — step definitions are real, runnable code. See
  [ADR-0001](architecture.md#adr-0001-no-empty-step-skeletons).
- **Idempotent** — running a command twice produces the same result.
- **Deterministic** — identical inputs always produce identical projects.

## Next steps

- [Installation](installation.md) — how to install behave-gen and its extras.
- [Quick Start](quickstart.md) — a guided tour of the main workflows.
- [CLI Reference](cli.md) — every command and its options.
- [Examples](https://github.com/behave-gen/behave-gen/tree/main/examples) —
  ready-to-run projects in the repository.
