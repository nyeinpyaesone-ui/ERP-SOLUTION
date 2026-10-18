# Changelog

All notable changes to the Modular ERP System are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **StockMovement data corruption**: stock side-effects now apply only on
  creation (idempotent re-save), wrapped in `transaction.atomic`, with DB-level
  `F()` updates and `select_for_update` for outbound movements — no more
  double-applied quantities, orphaned audit rows, or lost concurrent updates.
- **Validation bypass**: negative quantities and insufficient-stock errors are
  enforced in the model layer, so every write path (plain serializer POST,
  adjustment endpoint) is covered; DRF returns proper 400s via
  `get_error_detail()`.
- **Signal architecture**: `ModuleSignalHandler.register_handler` crashed with
  `NameError`/`TypeError` (`weakref` kwarg removed in Django 4.0+); handlers now
  resolve signals by name or object, honour priority ordering, never
  double-connect, and unregister cleanly. Dead trigger name `stock_movement`
  aligned to the emitted `stock_movement_completed`.
- **Production settings**: missing `import os` caused a startup crash;
  `SECRET_KEY` now fails fast instead of falling back to the insecure default.
- **Duplicate URL registration**: inventory routes were registered twice
  (hardcoded + dynamic loader); routing goes solely through `src/api/urls.py`.
- **`manage.py`**: works when invoked as `python src/manage.py ...` (repo root
  added to `sys.path`).
- **Dockerfile**: code landed at `/app/src/src/` due to `WORKDIR /app/src` plus
  `COPY src/ ./src/`; collectstatic failures were masked by `|| true`. Layout
  fixed, silent failure removed, `production` build stage named for CI,
  `trigger_config.yaml` copied into the runtime image.
- **CI test job**: ran pytest from the wrong directory with uninstalled test
  dependencies and broken artifact paths; now runs repo-root with
  `PYTHONPATH`, installs pytest toolchain, and publishes correct coverage
  artifacts.
- **Test suite**: collection crash under pytest ≥ 8 (libtmux plugin autoload)
  resolved; duplicate `addopts` key in `pytest.ini` merged; unused imports and
  shadowed fixtures cleaned; regression tests added for movement idempotency,
  rollback-on-validation-failure, signal handler priority, and module-loader
  reload semantics.
- **Serializers/views**: null-category crash in `ProductSerializer.category_name`
  (now `SerializerMethodField`); N+1 in `Product.total_stock` (single
  aggregate query); `AnonymousUser` crash in `adjust_stock`; server-side
  `performed_by` stamping prevents audit-trail spoofing.

### Changed
- Coverage gate unified at **70%** across `pytest.ini`, pre-commit hooks, and
  `scripts/pre-push-tests.sh` (pre-push previously demanded 80%, always failing
  locally while CI was green).
- Pre-commit Django hooks run from the repo root with
  `DJANGO_SETTINGS_MODULE=config.settings.test` (no DB dependency).
- Security hardening: role-scoped write permissions on inventory viewsets;
  JWT authentication wired for all API write endpoints.
- Dependency floor raised: `Django>=4.2.25` for PYSEC-2026 advisory coverage
  (shipped resolution 4.2.30 unchanged at runtime).

### Known limitations
- Remaining Django advisories list fixes only on the 5.x/6.x lines; migrating
  off the 4.2 LTS is tracked as a future major-version task.
- Runtime `enable_module()` / `disable_module()` cannot mutate the frozen
  `INSTALLED_APPS`/URLconf; a process restart is required (documented in
  `module_loader`).

## [2.0.0]
- Initial modular ERP scaffold: core module loader, inventory module, JWT auth,
  DRF API, CI/CD pipeline, Docker multi-stage builds.

[Unreleased]: https://example.invalid/modular-erp/compare/v2.0.0...HEAD
[2.0.0]: https://example.invalid/modular-erp/releases/tag/v2.0.0
