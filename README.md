# Patchbin

An app for cataloging and managing audio cables, adapters, splitters, and patch
cables: what you own, how each end is terminated, how long it is, where it's
stored, and what condition it's in — plus fast search so you can answer
*"do I have a cable that does X?"*

- [Status](#status)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Managing the catalog](#managing-the-catalog)
- [Sample data](#sample-data)
- [Testing](#testing)
- [Data model](#data-model)
- [Connector families](#connector-families)
- [Roadmap](#roadmap)
- [Project layout](#project-layout)
- [Development notes](#development-notes)

## Status

Early development. What works today:

- `ConnectorFamily` and `ConnectorType` models with an auto-slug and per-family
  uniqueness rules.
- The **Django admin** (`/admin/`) is the interface for now — no custom pages yet.
- Importable sample data: 12 connector families + 36 connector types, plus a
  demo superuser.
- 26 tests covering the models, the admin pages, and the fixtures.

See [`_docs/plan.md`](_docs/plan.md) for the full plan and
[`_docs/backlog.md`](_docs/backlog.md) for the task list.

## Tech stack

| | |
|---|---|
| Language | Python 3.11+ |
| Framework | Django 5.2 |
| Dependency manager | [uv](https://docs.astral.sh/uv/) |
| Database | SQLite (development) |
| Tests | Django test runner (`manage.py test`) |

## Quick start

```bash
uv sync                                 # create .venv and install dependencies
uv run python manage.py migrate         # create the SQLite database

# optional: load the sample catalog + a demo login (admin / patchbin-admin)
uv run python manage.py loaddata sample_catalog demo_user

uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/admin/>.

If you skipped the demo user, create your own login:

```bash
uv run python manage.py createsuperuser
```

## Managing the catalog

Everything is edited through the Django admin at `/admin/`:

- **Connector families** — the top-level taxonomy (XLR, phone jack, RCA, …).
  The family change page lists its connector types inline.
- **Connector types** — a specific connector within a family (XLR3, ¼″ TRS, DB25).
  Filter the list by family or active state; search by name, abbreviation,
  description, or typical uses.

Slugs are filled in automatically from the name if you leave them blank, and are
not changed afterwards if you rename the record.

## Sample data

The repo ships two fixtures in `catalog/fixtures/`:

| Fixture | Contents |
|---|---|
| `sample_catalog.json` | 12 connector families and 36 connector types |
| `demo_user.json` | one superuser — **`admin` / `patchbin-admin`** |

```bash
uv run python manage.py loaddata sample_catalog   # catalog data only
uv run python manage.py loaddata demo_user        # demo login only
```

Load them into a **fresh** database (right after `migrate`). `sample_catalog` is
safe to re-run; `demo_user` overwrites an existing `admin` account.

> [!WARNING]
> `admin` / `patchbin-admin` is a **demo credential for local evaluation only.**
> Change it before exposing the app anywhere:
> `uv run python manage.py changepassword admin` (or delete the user).

To regenerate `sample_catalog.json` after changing the seed data, edit the data
and re-dump:

```bash
uv run python manage.py dumpdata catalog --indent 2 -o catalog/fixtures/sample_catalog.json
```

## Testing

```bash
uv run python manage.py test            # all apps
uv run python manage.py test catalog -v 2
```

`catalog/tests.py` has 26 tests in 6 scenarios:

1. **`ConnectorFamily` model** — slug auto-fill, explicit slug kept, slug stable
   across renames, `__str__`, default ordering, unique name.
2. **`ConnectorType` model** — slug, `__str__` includes the family, name unique
   per family, same name allowed under a different family, slug-collision
   rejection, ordering by family then local sort.
3. **Family deletion** — `PROTECT` blocks deleting a family that still has types;
   succeeds once the types are removed.
4. **Admin** — family/type changelists, the family change page with its inline
   (regression test), the add page, and the `type_count` annotation.
5. **`sample_catalog` fixture** — row counts, every type has a slug and a family,
   family slugs unique, contact counts positive, every family has ≥1 type.
6. **`demo_user` fixture** — the documented `admin` / `patchbin-admin` login
   authenticates and is a superuser.

## Data model

### Implemented

**`ConnectorFamily`** — a physical/electrical connector standard; the top-level
filter for the catalog.

| Field | Type | Notes |
|---|---|---|
| `name` | char | unique |
| `slug` | slug | unique; auto-filled from `name` when blank |
| `description` | text | optional |
| `sort_order` | small int | lower sorts first |

**`ConnectorType`** — a specific connector within a family. Gender, right-angle
vs straight, and locking are deliberately *not* stored here — they belong to an
individual cable end.

| Field | Type | Notes |
|---|---|---|
| `family` | FK → `ConnectorFamily` | `PROTECT` on delete |
| `name` | char | e.g. `XLR3`, `TRS (1/4 in)` |
| `slug` | slug | auto-filled from `name`; unique per family |
| `abbreviation` | char | e.g. `TT`, `TRS` |
| `contact_count` | small int | pins / poles / conductors; nullable |
| `description` | text | optional |
| `typical_uses` | text | common signals or gear |
| `is_active` | bool | retire without deleting |
| `sort_order` | small int | lower sorts first within the family |

Unique constraints: `(family, name)` and `(family, slug)`.

### Planned

Not built yet — see [`_docs/plan.md`](_docs/plan.md):

- **`Cable`** — the inventory item: signal type (mic/line/instrument/speaker/
  digital/data/MIDI), format (analog/AES3/S-PDIF/ADAT/Dante/…), length,
  balanced/shielded, gauge, jacket colour, manufacturer + model, quantity,
  condition, storage location, tags, notes, acquired date/cost.
- **`CableEnd`** — one per connector on a cable (2, or more for splitters/looms):
  connector type, gender, right-angle vs straight, locking, channel/leg label.
- **`Manufacturer`**, **`CableModel`** — optional, for known products.
- **`StorageLocation`** — hierarchical bins / cases / drawers (self-FK).
- **`Kit` / `Loom`** — a named bundle grouping multiple cables.
- **`Tag`** — free-form labels; per-cable printable ID + QR.

## Connector families

The taxonomy seeded by `sample_catalog.json`:

| Family | What it is |
|---|---|
| Phone / jack (TS/TRS/TRRS) | Cylindrical tip-ring-sleeve jack plugs in ¼″, 3.5 mm, 2.5 mm and 4.4 mm (Bantam) sizes |
| XLR | Circular latching connectors, 3–7 pin, plus mini-XLR |
| RCA / phono | Unbalanced coaxial connectors; analog line and coaxial S/PDIF |
| DIN / MIDI | Multi-pin circular DIN, including 5-pin MIDI and MIDI-over-TRS |
| Speaker connectors | High-current unshielded terminations: speakON, banana, spade, bare wire |
| BNC | Bayonet coaxial connectors, 75 Ω (digital sync) and 50 Ω (RF) |
| Optical (TOSLINK / EIAJ) | Fiber connectors for S/PDIF and ADAT, full-size and 3.5 mm mini |
| D-sub multicore | DB25 and friends — 8 channels of analog or AES3 |
| Networked audio | Twisted-pair and fiber for Dante, AES50, AVB |
| USB / data | Digital data connectors for interfaces and USB microphones |
| IEM / headphone detachable | MMCX, 2-pin 0.78 mm, 4.4 mm Pentaconn |
| Bare / pigtail | Unterminated or flying-lead ends for custom terminations |

The family and type lists are ordinary editable rows, not hard-coded — add
oddball or proprietary connectors as needed.

## Roadmap

From [`_docs/backlog.md`](_docs/backlog.md):

1. **Model + admin** — remaining entities (`Cable`, `CableEnd`, `Manufacturer`,
   `StorageLocation`, `Kit`, `Tag`), admin registrations, tests. *(families &
   types done)*
2. **Views & search** — cable list with faceted filters (family, signal type,
   length range, location, condition), text search, detail page.
3. **Data entry & labels** — quick-add form, printable per-cable ID + QR,
   CSV import/export.
4. **Kits & locations** — kit contents view, bulk "move a kit", recursive
   "what's in this location".

## Project layout

| Path | Purpose |
|---|---|
| `patchbin/` | Django project config (settings, urls, wsgi/asgi) |
| `catalog/` | The catalog app: models, admin, tests |
| `catalog/fixtures/` | Importable sample data |
| `catalog/migrations/` | Schema migrations |
| `_docs/plan.md` | Build plan and architecture notes |
| `_docs/backlog.md` | Task list |
| `pyproject.toml`, `uv.lock` | Dependencies |

## Development notes

- Common commands:
  ```bash
  uv run python manage.py makemigrations catalog
  uv run python manage.py migrate
  uv run python manage.py shell
  uv run python manage.py test
  ```
- The database (`db.sqlite3`) and `.venv/` are gitignored; the fixtures are the
  portable way to share catalog data.
- `DEBUG` is on by default (development settings). Don't deploy as-is.
