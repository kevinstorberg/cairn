# Production Preflight

Cairn provides generic preflight helpers for production-readiness checks before a
cutover. The helpers are scaffolding: each downstream app supplies its expected
migration heads, table names, database URLs, and backup evidence.

Source of truth:

- Preflight helper: [../src/operations/preflight.py](../src/operations/preflight.py)
- CLI wrapper: [../scripts/preflight.py](../scripts/preflight.py)
- Runtime settings: [../src/settings.py](../src/settings.py)
- Deployment boundaries: [DEPLOYMENT.md](DEPLOYMENT.md)

## Convention

- Run read-only preflight before pointing traffic at an existing production
  database.
- Use `--expected-head` for each Alembic head that must be present.
- Use `--table` for row-count evidence that matters to the app.
- Use `--production` with `PRODUCTION_DATABASE_URL_READONLY` for read-only
  production checks.
- Use `--write-cutover` only after backup evidence exists; it requires
  `--cutover-confirmed` and `--backup-path`.

The preflight helper never mutates data. It reports migration versions, selected
row counts, explicit cutover-gate failures, and a JSON-safe status.

