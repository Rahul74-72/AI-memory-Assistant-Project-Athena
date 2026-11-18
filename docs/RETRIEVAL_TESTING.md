# Running retrieval regression tests

Run commands from the repository root, using a disposable virtual environment with the project's development dependencies installed.

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_retriever*.py
```

On shells that do not expand filename wildcards, use explicit paths or run the full suite with `python -m pytest`.

## Database isolation

`tests/conftest.py` sets `ATHENA_DATA_DIR` to a temporary directory before application imports and overrides the API database with an in-memory SQLite database for each test. It also supplies a test-only JWT secret and disables rate limiting. Run tests through pytest so these fixtures are loaded; do not point tests at your personal memory database.

Even retrieval tests that mock sessions load the automatic API database fixture, so installing only pytest and SQLAlchemy is insufficient. Use the development requirements above.

A successful run must exit with code zero, including fixture cleanup. Passing assertions followed by a temporary-directory permission error is a failed run; use an environment with a writable temporary directory and rerun before reporting success.
