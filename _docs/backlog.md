# Patchbin — Backlog

Small starter backlog for building Patchbin in Django. Ordered roughly by
dependency. See `plan.md` for context.

## Milestone 1 — Model + admin

- [x] Add `ConnectorFamily` and `ConnectorType` models (`catalog/models.py`)
- [ ] Add `Cable` model with signal type + format `TextChoices`, length, and
      physical attributes
- [ ] Add `CableEnd` model (FK to `Cable`, connector type, gender, angle, locking)
- [ ] Add `Manufacturer`, `CableModel`, `StorageLocation` (self-FK for hierarchy)
- [ ] Add `Kit` and `Tag` models; wire M2M to `Cable`
- [x] `makemigrations` + `migrate` — `catalog/0001_initial.py` created + applied
- [x] Register models in `catalog/admin.py` with list filters and search fields
      — `ConnectorFamily` + `ConnectorType` done (types inline on family);
      add `Cable` / `CableEnd` (inline) as those models land
- [x] ~~Data migration~~ **Fixture** seeding connector families and common
      connector types — `catalog/fixtures/sample_catalog.json` (12 families,
      36 types), loadable by testers via `manage.py loaddata sample_catalog`
- [x] Tests for what exists so far — `catalog/tests.py`, 26 tests:
      slug auto-fill, `__str__`, per-family uniqueness (name + slug), `PROTECT`
      on family delete, ordering, admin pages render (+ inline regression),
      `type_count` annotation, `sample_catalog` + `demo_user` fixture integrity
- [ ] Extend model tests as `Cable`/`CableEnd` land: end-count validation,
      length formatting

## Milestone 2 — Views & search

- [ ] Cable list view with pagination
- [ ] Faceted filters: family, signal type, length range, location, condition
- [ ] Text search across manufacturer, model, notes, tags
- [ ] Cable detail view showing both ends, location, kit membership

## Milestone 3 — Data entry & labels

- [ ] Quick-add form (single page: two ends + length + location)
- [ ] Printable label view: per-cable ID + QR linking to the detail page
- [ ] CSV export of the full inventory
- [ ] CSV import with validation and a dry-run preview

## Milestone 4 — Kits & locations

- [ ] Kit detail view: list contents, total length, missing items
- [ ] Bulk action: move all cables in a kit to a new location
- [ ] "What's in this location" view (recursive)

## Housekeeping

- [x] `README.md`: setup + run instructions using `uv` (+ sample-data import)
- [x] `demo_user` fixture — superuser `admin` / `patchbin-admin` for evaluation
- [ ] Rotate/remove the demo `admin` password before any non-local deployment
- [ ] Base template + minimal CSS
- [ ] `pytest` or Django test config in CI
