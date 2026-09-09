# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Patchbin is a Django app for cataloging audio cables, adapters, splitters, and
patch cables. Full design and roadmap live in `_docs/plan.md` and
`_docs/backlog.md` — read them before extending the data model, and keep the
backlog checkboxes current as tasks land.

## Commands

All Python commands run through uv:

```bash
uv sync                                   # install deps into .venv
uv run python manage.py migrate           # apply migrations (SQLite)
uv run python manage.py runserver         # dev server -> http://127.0.0.1:8000/admin/
uv run python manage.py test              # full test suite (Django runner)
uv run python manage.py test catalog.tests.ConnectorTypeModelTests.test_slug_is_autofilled_from_name   # one test
uv run python manage.py makemigrations catalog
uv run python manage.py check
uv run python manage.py loaddata sample_catalog demo_user   # populate a fresh DB
```

There is no linter or formatter configured.

## Architecture

- **One project (`patchbin/`), one app (`catalog/`).** `patchbin/urls.py` routes
  only `admin/`; `catalog/views.py` is an empty stub.
- **Admin-first.** The Django admin at `/admin/` is the entire UI for now. Build
  and validate the model through the admin before writing custom views.
- **Data model today:** two lookup models, `ConnectorFamily` 1—* `ConnectorType`.
  The inventory models (`Cable`, `CableEnd`, `StorageLocation`, `Kit`, `Tag`,
  `Manufacturer`) are specified in `_docs/plan.md` but not built.
- **Reference data ships as fixtures, not data migrations.** `catalog/fixtures/`
  holds `sample_catalog.json` (12 families, 36 types) and `demo_user.json`
  (superuser `admin` / `patchbin-admin`, local evaluation only). This is
  deliberate — testers load it with `loaddata`.

## Project-specific gotchas

- **Slugs auto-fill only when blank.** `ConnectorFamily.save()` and
  `ConnectorType.save()` derive `slug` from `name` via `slugify`, but only if
  `slug` is empty, and never rewrite it on rename.
- **`loaddata` bypasses `save()`** (it calls `save_base`), so auto-slug does NOT
  run during a fixture load. Every fixture row must carry an explicit `slug`.
  Regenerate fixtures with `dumpdata catalog --indent 2 -o
  catalog/fixtures/sample_catalog.json`, not by hand.
- **`ConnectorType` is unique per family on both `name` and `slug`.** Two
  distinct names that slugify to the same value collide on the slug constraint.
- **Deleting a `ConnectorFamily` is `PROTECT`ed** while any `ConnectorType`
  references it.
- **Admin inlines:** a field named in `prepopulated_fields` must also be in the
  inline's `fields`, or the parent change page 500s. `ConnectorTypeInline` omits
  `slug` for this reason.
- **`patchbin/settings.py` is stock `startproject` output**: `DEBUG = True`,
  committed `SECRET_KEY`, empty `ALLOWED_HOSTS`. Development only.
- **`db.sqlite3` and `.venv/` are gitignored.**

## Conventions

- In committed docs (`README.md`, `_docs/*.md`, `CLAUDE.md`) and code comments,
  use repo-relative paths — never absolute machine paths (`/home/...`, `~/...`).
