"""Cucumber-to-Behave migration plugin.

Cucumber (Java/JVM) feature files are Gherkin, but projects typically have:
- ``src/test/resources/features/`` layout
- Java step definitions (``@Given``, ``@When``, ``@Then`` annotations)
- JUnit runner classes
- ``pom.xml`` or ``build.gradle`` build files

The migrator copies feature files into a Behave ``features/`` layout, strips
Cucumber-specific annotations, and emits a migration report. Step definitions
are not auto-translated (ADR-0001: no empty skeletons); instead the migrator
suggests using ``behave-gen add steps``.
"""

from __future__ import annotations

from behave_gen.plugins.cucumber.migrator import (
    MigrationReport,
    migrate_cucumber,
)

__all__ = ["MigrationReport", "migrate_cucumber"]
