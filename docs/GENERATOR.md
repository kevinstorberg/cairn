# Resource Generator

The `cairn` console command scaffolds a conventional CRUD resource through the
same layers the template expects downstream apps to use.

Source of truth:

- CLI dispatcher: `scripts/cli.py`
- Generate script: `scripts/generate.py`
- Parser and file planner: `lib/cairn/generator/`
- Router auto-registration: `src/routers/registry.py`
- Layer conventions: `docs/REPOSITORIES_SERVICES.md`

Example shape:

```bash
cairn generate resource project name:string status:enum[planned,active,done]
```

Use `--dry-run` to inspect planned files. Normal generation writes model,
schema, repository, service, router, migration stub, focused tests, and resource
docs. Existing files fail closed unless `--force` is passed.

Generated routers call `register_router()`, so app startup discovers them
without repeated edits to `src/app.py`. Generated migration files are reviewable
stubs; inspect them before applying migrations in a real app.

Generator v1 is intentionally narrow: field parsing, naming, rendering, and
conflict detection are pure Python modules. It does not add relationships,
custom indexes, auth scopes, graph nodes, or jobs. Add those by extending the
generated service/repository/router layers instead of duplicating framework
plumbing.

