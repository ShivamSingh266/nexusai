"""
conftest.py — project-level test configuration.

Each test MODULE that uses the FastAPI TestClient overrides app.dependency_overrides[get_db].
Because Python only has one process during `pytest` collection and all modules share
the same `app` object, the override set by the LAST imported module wins for ALL tests.

To avoid cross-module contamination we:
1. Do NOT set app.dependency_overrides at module level in test files.
2. Each test file imports a module-level engine and SessionLocal.
3. The override is applied fresh for each test session via autouse fixtures.

This conftest establishes the pytest rootdir and ensures PYTHONPATH is correct.
"""
