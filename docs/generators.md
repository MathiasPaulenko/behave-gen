# Generators

behave-gen can generate `.feature` files and step definitions from external
specifications: OpenAPI 3.x, Postman Collections, and Swagger 2.0.

## from-openapi

Generate features and HTTP steps from an OpenAPI 3.x spec (YAML or JSON).

```bash
behave-gen from-openapi spec.yaml --out-dir gen --step-lib http --tag api
```

### How it works

1. **Parse** — The OpenAPI spec is parsed (YAML via `pyyaml`, JSON via the
   standard library). Requires the `openapi` extra for YAML files.
2. **Build features** — Each path produces a `.feature` file grouped by path
   segment. Each operation (GET, POST, PUT, DELETE, PATCH) becomes a scenario.
3. **Build steps** — When `--step-lib http` is passed, a concrete
   `http_steps.py` module is generated alongside the features.

### Output structure

```text
gen/
  features/
    pets.feature           # /pets endpoints
    pets_petId.feature     # /pets/{petId} endpoints
    steps/
      http_steps.py        # HTTP step library
```

### Filtering

Restrict generation to specific paths or methods:

```bash
behave-gen from-openapi spec.yaml \
  --include-path /pets \
  --include-method GET \
  --include-method POST
```

### Generated scenario example

For a `GET /pets` operation:

```gherkin
@api
Feature: Pets
  Scenarios for Pets generated from Petstore YAML API.

  Scenario: List all pets
    When I send a GET request to "/pets"
    Then the response status should be 200
```

The scenarios use the [HTTP step library](step-libraries.md#http-step-library)
patterns, so they work with the generated `http_steps.py`.

### Options

| Option | Description |
| ------ | ----------- |
| `SPEC` | Path to an OpenAPI 3.x spec (YAML or JSON). |
| `--out-dir` | Output directory (default: `features`). |
| `--step-lib` | Step library to bind (e.g. `http`). |
| `--tag` | Tag applied to all generated scenarios. |
| `--include-path` | Restrict to these paths (repeatable). |
| `--include-method` | Restrict to these HTTP methods (repeatable). |

---

## from-postman

Generate features from a Postman Collection v2.1 JSON file.

```bash
behave-gen from-postman collection.json --out-dir gen --step-lib http --tag api
```

### How it works

1. **Parse** — The Postman collection JSON is parsed. Each item (request) is
   extracted with its method, URL, name, and description.
2. **Build features** — Items are grouped by Postman folder. Each folder
   becomes a `.feature` file, each request becomes a scenario.
3. **Build steps** — When `--step-lib http` is passed, an `http_steps.py`
   module is generated.

### Options

| Option | Description |
| ------ | ----------- |
| `COLLECTION` | Path to a Postman Collection v2.1 JSON file. |
| `--out-dir` | Output directory (default: `features`). |
| `--step-lib` | Step library to bind (e.g. `http`). |
| `--tag` | Tag applied to all generated scenarios. |

---

## from-swagger

Convert a Swagger 2.0 spec to OpenAPI 3.x in memory, then generate features
and steps using the OpenAPI generator.

```bash
behave-gen from-swagger swagger.json --out-dir gen --step-lib http --tag api
```

### How it works

1. **Convert** — The Swagger 2.0 spec is converted to OpenAPI 3.x in memory.
   Paths, operations, parameters, and responses are mapped.
2. **Build features** — Same as `from-openapi`.
3. **Build steps** — Same as `from-openapi`.

### Options

| Option | Description |
| ------ | ----------- |
| `SPEC` | Path to a Swagger 2.0 spec (JSON). |
| `--out-dir` | Output directory (default: `features`). |
| `--step-lib` | Step library to bind (e.g. `http`). |
| `--tag` | Tag applied to all generated scenarios. |

---

## Re-generating with update

When the source spec changes, re-run the generator or use `behave-gen update`:

```bash
behave-gen update --from-openapi spec.yaml --force
```

This re-applies the generator and overwrites previously generated files.
