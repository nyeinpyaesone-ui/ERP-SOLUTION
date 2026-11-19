# Production Readiness Roadmap

## Baseline (2026-11-19)

This roadmap is based on the repository's `main` branch at
`7629454cd50bf312072e94b3a3deb04091f7f37b`. It is an engineering plan,
not a production certification.

### Verified repository state

- Django + Django REST Framework application.
- Inventory is the only business module with models, serializers, views,
  permissions, migrations, and dedicated tests.
- HR, finance, sales, procurement, and manufacturing have module directories
  and app configuration stubs; complete business workflows are not present.
- PostgreSQL and Redis/Celery are declared as intended runtime dependencies.
- A Dockerfile and three GitHub Actions workflow files exist.
- The repository had 31,657 tracked files under `venv/`, tracked Python cache
  artifacts, and a tracked coverage database. These generated files are removed
  by the accompanying repository-hygiene change.
- The last observed main commit is dated 2026-10-18. No open pull requests,
  open issues, or published releases were returned by the inspected GitHub
  endpoints.
- Two enterprise image-publishing workflows reported `startup_failure` on
  the inspected main commit. Their runs had no jobs, so no build or test
  result can be inferred from those runs.
- Existing status documents disagree about test counts, coverage, module
  completeness, and whether deployment is production-ready. Treat those
  claims as unverified until reproduced from a clean checkout.

## Release principle

Do not label the application production-ready until the acceptance criteria
below have passed on a clean checkout and the exact release commit. Keep
business correctness, data integrity, security, and recoverability ahead of
throughput or infrastructure complexity.

## Phase 0 — Repository and delivery hygiene

1. Keep virtual environments, bytecode, coverage files, local databases,
   build output, and secrets out of Git.
2. Use one canonical Python runtime version across local development, CI,
   containers, and deployment.
3. Pin and audit runtime dependencies; introduce a reproducible lock strategy.
4. Remove duplicate image-publishing responsibilities. Use one CI workflow
   for validation and one controlled release workflow for image publication.
5. Validate every workflow with GitHub Actions execution; never use
   `continue-on-error` or `|| true` for required quality/security gates.
6. Build images for the supported deployment architectures and publish
   immutable commit-SHA and version tags. Do not deploy a mutable `latest`
   tag as the release identity.

Acceptance:
- A fresh clone installs from declared dependency files without relying on
  repository-local virtual environments.
- CI starts on pull requests and main-branch pushes.
- Required lint, type, security, unit, migration, and container-build checks
  fail closed.
- The Git tree contains no generated environment or cache artifacts.

## Phase 1 — Runtime and configuration correctness

1. Validate settings at startup: required secret key, database credentials,
   allowed hosts, trusted origins, cache/broker URLs, and production flags.
2. Ensure production logging does not transmit personal data by default.
3. Verify health and readiness endpoints separately; readiness must check
   required dependencies without exposing sensitive details.
4. Verify Docker runtime paths, static assets, non-root execution, signal
   handling, worker count, and health-check URL.
5. Run migrations as a controlled release step, not implicitly in every
   application replica.
6. Add a clean-checkout smoke test for management commands and application
   startup.

Acceptance:
- `manage.py check --deploy` passes with production settings.
- A clean container starts as a non-root user and passes a real HTTP health
  check.
- Database migration status is deterministic and documented.
- Missing required configuration causes a clear startup failure.

## Phase 2 — Inventory correctness and transaction integrity

Inventory is the only implemented business module and should become the
reference implementation before other modules are expanded.

1. Define stock invariants: quantities cannot become negative, reserved
   quantities cannot exceed on-hand quantities, and available stock is
   computed consistently.
2. Make stock movement posting an explicit service-layer operation with a
   single database transaction.
3. Lock or atomically create stock-level rows so concurrent first-time
   outbound movements cannot oversell.
4. Make movement records immutable after posting; use compensating movements
   for corrections instead of editing or deleting audit history.
5. Add idempotency keys for externally retried stock operations.
6. Enforce uniqueness and check constraints in the database, not only in
   serializer validation.
7. Test transfer atomicity, rollback, concurrent updates, duplicate requests,
   permission boundaries, and audit attribution.
8. Ensure list and summary endpoints use database aggregation and bounded
   query counts.

Acceptance:
- Concurrency tests prove no overselling or lost updates.
- Duplicate requests cannot apply a movement twice.
- Failed transfers leave both warehouses unchanged.
- Posted movement history is auditable and cannot be silently rewritten.

## Phase 3 — Identity, authorization, and auditability

1. Implement authentication lifecycle, password/session/token policies, and
   account recovery.
2. Define role and permission matrices per business action and data scope.
3. Enforce tenant/branch/warehouse scoping in querysets and services.
4. Record actor, timestamp, request/correlation ID, action, target, and
   before/after metadata for sensitive operations.
5. Add rate limits and security tests for authentication and privileged APIs.
6. Review secrets, dependency vulnerabilities, container permissions, and
   GitHub Actions least-privilege permissions.

Acceptance:
- Anonymous and unauthorized access is denied consistently.
- Cross-tenant and cross-branch access tests prove isolation.
- Sensitive operations produce immutable audit evidence.
- No credentials or personal data are written to logs.

## Phase 4 — Business modules and API contracts

Implement modules incrementally, with migrations, service layer, API,
permissions, tests, and documentation in each change.

Recommended order:
1. Sales and customer balances.
2. Procurement and supplier balances.
3. Finance ledger and accounting controls.
4. HR and payroll only after the required business/legal rules are specified.
5. Manufacturing after inventory and procurement contracts stabilize.

Define API versioning, pagination, filtering, validation, error schemas,
OpenAPI generation, and backward-compatibility policy before broad integration.
Do not enable empty modules merely because a directory exists.

Acceptance:
- Each module has end-to-end workflows, permission tests, migration tests,
  and documented integration contracts.
- Financial postings are balanced and reversible through auditable entries.
- Cross-module events are idempotent and do not replace transactional
  correctness.

## Phase 5 — User interface and operational workflows

The inspected source tree does not establish a working frontend. Choose and
document the frontend architecture before introducing a separate application.
Implement role-aware workflows, responsive layouts, error states, and
accessible forms against the versioned API.

For Myanmar business operations, specify language, currency, timezone,
number/date formatting, branch workflows, local payment integration, and
offline/retry behavior as explicit product requirements.

Acceptance:
- Core user journeys work from browser UI through API to persistent database.
- Browser tests cover authentication, sales, inventory, receiving, and daily
  operational closing.
- API failures and retry behavior do not duplicate financial or stock effects.

## Phase 6 — Release, deployment, and operations

1. Build once; promote the same immutable image digest through staging and
   production.
2. Require successful CI, migration review, staging smoke tests, and an
   authorized production approval.
3. Use backward-compatible expand/contract migrations for zero/low-downtime
   changes.
4. Verify backups with scheduled restore drills, not backup-job success alone.
5. Define rollback boundaries for application images and database migrations.
6. Add structured logs, metrics, traces, correlation IDs, alert thresholds,
   and operational runbooks.
7. Run load tests against representative ERP transactions and database sizes.

Acceptance:
- A documented staging deployment and rollback have been exercised.
- A database restore drill has succeeded and recovery objectives are recorded.
- Alerts detect application, database, queue, and backup failures.
- Release evidence identifies the exact commit and image digest.

## Required engineering workflow

For every change:

1. Inspect current implementation and its callers.
2. Write a focused issue or acceptance criteria.
3. Create a short-lived feature branch from the latest `main`.
4. Implement the smallest coherent change with tests and migration review.
5. Run formatting, lint, type, security, unit, integration, and build checks.
6. Review the diff for data loss, permission regressions, secret exposure,
   and unintended scope.
7. Open a pull request with test evidence and deployment notes.
8. Merge only after required checks and human review pass.
9. Verify the merged commit and deployment artifact; record the result.

## Current release decision

**Not approved for production deployment.** The repository has a useful Django
and inventory foundation, but its module coverage, CI/CD startup failures,
tracked runtime artifacts, security posture, end-to-end workflows, and
operational recovery are not yet demonstrated to production standards.
