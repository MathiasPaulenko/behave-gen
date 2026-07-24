# Cucumber Migration

`behave-gen migrate` converts a Cucumber (Java) project to a Behave project
layout by copying `.feature` files and emitting a migration report.

## Usage

```bash
behave-gen migrate path/to/cucumber-project --out-dir migrated
```

### What it does

1. **Scans** the source directory for `.feature` files (typically under
   `src/test/resources/features/`).
2. **Copies** each `.feature` file into the output directory, preserving the
   directory structure.
3. **Reports** the number of migrated files, any skipped files, and warnings
   about Java step definitions that need manual translation.

### What it does not do

- **Does not translate Java step definitions to Python.** Java step files
  (`*Steps.java`) are detected and reported as a warning. Use
  `behave-gen add steps --lib <http|auth>` to generate Python step definitions,
  or write them manually.
- **Does not convert Gherkin syntax.** Cucumber and Behave both use Gherkin,
  so `.feature` files are compatible as-is. The only differences are in step
  definitions, not feature files.

## Example

Source Cucumber project:

```text
cucumber-project/
  src/
    test/
      java/
        com/
          example/
            LoginSteps.java
      resources/
        features/
          login.feature
          checkout.feature
```

Run migration:

```bash
behave-gen migrate cucumber-project --out-dir migrated
```

Output:

```text
Migrated feature migrated/features/src/test/resources/features/checkout.feature
Migrated feature migrated/features/src/test/resources/features/login.feature

Migrated 2 feature file(s).
migrate: warning: Found 1 Java step definition file(s).
Use 'behave-gen add steps --lib <http|auth>' to generate Python step definitions.
```

Result:

```text
migrated/
  features/
    src/
      test/
        resources/
          features/
            login.feature
            checkout.feature
```

## After migration

1. **Add step definitions:**

   ```bash
   cd migrated
   behave-gen add steps --lib http
   behave-gen add steps --lib auth
   ```

2. **Check for undefined steps:**

   ```bash
   behave-gen check
   ```

3. **Run tests:**

   ```bash
   behave
   ```

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `SOURCE_DIR` | _required_ | Cucumber project to migrate. |
| `--out-dir` | `.` | Output directory for the Behave project. |
| `--from` | `java` | Source language (`java`, `ruby`). |
