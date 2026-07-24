# CLI Reference

All commands share these global options:

| Option | Description |
| ------ | ----------- |
| `--project PATH` | Project root directory (default: current working directory). |
| `--config PATH` | Path to an explicit `pyproject.toml` config file (reserved). |
| `--verbose, -v` | Enable verbose output (reserved). |
| `--dry-run` | Show what would happen without writing files (reserved). |

---

## init

Create a new Behave project from a template.

```bash
behave-gen init [OPTIONS] NAME
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `NAME` | New project directory name. |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--template` | `default` | Template set to use. |
| `--template-engine` | `string` | Template engine: `string` or `jinja2`. |
| `--kit` | `false` | Pre-wire behave-kit in `environment.py`. |
| `--data` | `false` | Pre-wire behave-data hooks. |
| `--force` | `false` | Overwrite an existing directory. |

**Example:**

```bash
behave-gen init my-project --kit --data
```

---

## add feature

Add a `.feature` file to the project.

```bash
behave-gen add feature [OPTIONS] NAME
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `NAME` | Feature name (without extension). |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--tags` | _none_ | Comma or space separated tags. |
| `--template` | `default` | Feature template: `default` or `crud`. |

**Example:**

```bash
behave-gen add feature login --tags smoke,auth
behave-gen add feature checkout --template crud
```

See [Feature Templates](templates.md).

---

## add steps

Add real step definitions from a step library.

```bash
behave-gen add steps [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--lib` | _required_ | Step library name: `http` or `auth`. |

**Example:**

```bash
behave-gen add steps --lib http
behave-gen add steps --lib auth
```

See [Step Libraries](step-libraries.md).

---

## add environment

Add or update `environment.py` with ecosystem hooks.

```bash
behave-gen add environment [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--kit` | `false` | Add behave-kit fixtures. |
| `--data` | `false` | Add behave-data hooks. |

**Example:**

```bash
behave-gen add environment --kit --data
```

---

## add config

Add an ecosystem package to `pyproject.toml`.

```bash
behave-gen add config NAME
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `NAME` | Config to add: `behave-kit` or `behave-data`. |

**Example:**

```bash
behave-gen add config behave-kit
```

---

## from-openapi

Generate features and steps from an OpenAPI 3.x spec.

```bash
behave-gen from-openapi [OPTIONS] SPEC
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `SPEC` | Path to an OpenAPI 3.x spec (YAML or JSON). |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--out-dir` | `gen` | Output directory for the generated project (creates a `features/` subdir). |
| `--step-lib` | _none_ | Step library to bind (e.g. `http`). |
| `--tag` | _none_ | Tag generated scenarios. |
| `--include-path` | _all_ | Restrict to these paths (repeatable). |
| `--include-method` | _all_ | Restrict to these HTTP methods (repeatable). |

**Example:**

```bash
behave-gen from-openapi spec.yaml --out-dir gen --step-lib http --tag api
behave-gen from-openapi spec.yaml --include-path /pets --include-method GET
```

See [Generators](generators.md).

---

## from-postman

Generate features and steps from a Postman collection.

```bash
behave-gen from-postman [OPTIONS] COLLECTION
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `COLLECTION` | Path to a Postman Collection v2.1 JSON file. |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--out-dir` | `gen` | Output directory for the generated project (creates a `features/` subdir). |
| `--step-lib` | _none_ | Step library to bind (e.g. `http`). |
| `--tag` | _none_ | Tag generated scenarios. |

**Example:**

```bash
behave-gen from-postman collection.json --out-dir gen --step-lib http --tag api
```

See [Generators](generators.md).

---

## from-swagger

Generate features and steps from a Swagger 2.0 spec.

```bash
behave-gen from-swagger [OPTIONS] SPEC
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `SPEC` | Path to a Swagger 2.0 spec (JSON). |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--out-dir` | `gen` | Output directory for the generated project (creates a `features/` subdir). |
| `--step-lib` | _none_ | Step library to bind (e.g. `http`). |
| `--tag` | _none_ | Tag generated scenarios. |

**Example:**

```bash
behave-gen from-swagger swagger.json --out-dir gen --step-lib http --tag api
```

See [Generators](generators.md).

---

## migrate

Migrate a Cucumber project to Behave.

```bash
behave-gen migrate [OPTIONS] SOURCE_DIR
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `SOURCE_DIR` | Cucumber project to migrate. |

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--out-dir` | `migrated` | Output directory for the migrated project (creates a `features/` subdir). |

**Example:**

```bash
behave-gen migrate path/to/cucumber-project --out-dir migrated
```

See [Cucumber Migration](migration.md).

---

## check

Check project health via behave-doctor.

```bash
behave-gen check [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--format` | `text` | Output format: `text` or `json`. |

**Example:**

```bash
behave-gen check
behave-gen check --format json
```

---

## doctor

Alias for `check`.

```bash
behave-gen doctor
```

---

## lint

Lint `.feature` files via behave-lint.

```bash
behave-gen lint [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--fix` | `false` | Apply fixes where possible. |

**Example:**

```bash
behave-gen lint
behave-gen lint --fix
```

---

## format

Format `.feature` files via behave-format.

```bash
behave-gen format [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--check` | `false` | Check formatting without writing. |

**Example:**

```bash
behave-gen format
behave-gen format --check
```

---

## preview

Preview a feature file with resolved examples and tables.

```bash
behave-gen preview [OPTIONS] FEATURE
```

**Arguments:**

| Argument | Description |
| -------- | ----------- |
| `FEATURE` | Path to a `.feature` file. |

**Example:**

```bash
behave-gen preview features/login.feature
```

---

## stats

Report project statistics.

```bash
behave-gen stats [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--format` | `text` | Output format: `text` or `json`. |

**Example:**

```bash
behave-gen stats
behave-gen stats --format json
```

---

## update

Re-apply generated environment and step libraries to an existing project.

```bash
behave-gen update [OPTIONS]
```

**Options:**

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--kit` | `false` | Include behave-kit wiring in `environment.py`. |
| `--data` | `false` | Include behave-data wiring in `environment.py`. |
| `--force` | `false` | Regenerate and back up changed files. |

**Example:**

```bash
behave-gen update --force
```

Files generated by behave-gen (marked with `Generated by behave-gen`) are
refreshed. User-modified files without the marker are skipped unless `--force`
is used.
