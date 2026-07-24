"""End-to-end integration tests for behave-gen.

These tests exercise full workflows — ``init``, ``add feature``, ``add steps``,
``from-openapi``, ``migrate``, ``check``, ``stats``, ``preview``, ``update`` —
against real Behave projects generated on disk. They verify that the generated
projects are structurally valid, parse cleanly, and pass ``behave --dry-run``.
"""
