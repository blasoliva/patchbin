# Patchbin — Build Plan

## Goal

A personal/small-studio app for cataloging audio cables, adapters, splitters, and
patch cables: what you own, how each end is terminated, how long it is, where it's
stored, and what condition it's in — plus fast search so you can answer "do I have
a cable that does X?"

## Current status

- Django 5.2 project scaffolded with `uv` (`.venv/`, `uv.lock`).
- Config module: `patchbin/`. App: `catalog/` (registered).
- `ConnectorFamily` + `ConnectorType` models, migration `catalog/0001_initial`
  applied, both registered in the admin (types inline on family).
- Sample data as loadable fixtures: `catalog/fixtures/sample_catalog.json`
  (12 families, 36 types) and `demo_user.json` (superuser `admin` / `patchbin-admin`).
- Operational screen today = the Django admin at `/admin/`.
- `catalog/tests.py`: 26 tests (models, admin, fixtures) — `uv run python manage.py test`.

## Data model (in design — see the numbered design discussion)

Lookup tables (editable in-app, not hard-coded):

- **ConnectorFamily** — physical/electrical standard (XLR, Phone/jack, RCA, DIN,
  speakON, BNC, optical, D-sub multicore, networked audio, USB, IEM, Euroblock, bare).
- **ConnectorType** — a specific member of a family: pole/pin count, variant.
  Gender, angle, and locking are chosen per cable end, not stored here.

Core records:

- **Cable** — the inventory item. Signal type (mic/line/instrument/speaker/digital/
  data/MIDI), format (analog/AES3/S-PDIF/ADAT/Dante/…), length, balanced/shielded,
  gauge, jacket colour, manufacturer + model, quantity, condition, storage location,
  labels, notes, acquired date/cost.
- **CableEnd** — one per connector on a cable (usually 2, more for splitters/looms):
  connector type, gender, right-angle vs straight, locking, channel/leg label.

Supporting:

- **Manufacturer**, **CableModel** (SKU) — optional, for known products.
- **StorageLocation** — hierarchical bins/cases/drawers.
- **Kit / Loom** — a named bundle grouping multiple cables (stage snake, gig bag).
- **Label / Tag** — free-form tags; per-cable printable ID + QR.

## Architecture decisions

- **Admin-first**: build the Django admin into a usable data-entry tool before any
  custom UI. Validates the model cheaply.
- Lookup tables seeded via a data migration / fixture so a fresh install is usable.
- Keep signal/format as `TextChoices`, connector families/types as real rows.
- Custom front end (list + filters + quick-add) comes after the model is stable.
- No auth beyond Django's default for v1 (single user / trusted LAN).

## Build phases

1. **Model + admin** — entities above, admin registrations, seed data, tests.
2. **Search & filter** — list view with faceted filters (family, signal, length
   range, location, condition) and text search.
3. **Quick-add flow** — a streamlined form for adding a cable in a few keystrokes.
4. **Labels** — printable per-cable ID + QR that deep-links to the cable page.
5. **Kits/looms + location tracking** — group cables, move a whole kit between
   locations, "what's in this case" view.
6. **Import/export** — CSV in/out for bulk entry and backup.

## Out of scope for v1

- Multi-user accounts, permissions, sharing.
- Barcode scanning via camera (QR deep-link only).
- Cable testing / continuity logs.
- Mobile app (responsive web only).
