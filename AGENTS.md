# Rebuild working agreement

This checkout is dedicated to the optics ERP rebuild. Do not push, change remotes, or use the legacy database without explicit authorization.

Before every implementation task, read `docs/rebuild/README.md`, `docs/rebuild/PLAN.md`, `docs/rebuild/STATUS.json`, and the relevant architecture decision and acceptance criteria.

## Required workflow
1. Select a task ID from STATUS.json; confirm its dependencies are done; mark it in_progress.
2. Implement new application code in `rebuild/`. Treat `osmBack/` and `osmFront/` as reference code, not an implementation template. Do not copy secrets, media, generated assets, or legacy migrations.
3. Add meaningful automated tests for every completed functional task. Include failure paths and permissions; use PostgreSQL for database behavior, never SQLite as proof of tenancy, constraints, or concurrency.
4. Run the relevant tests. A missing runtime or database means blocked verification, never a passing result. Record exact command, date, outcome, and limitations in TEST_LOG.md.
5. Mark a task done only with passing test evidence and its acceptance criteria met. Update PLAN.md, STATUS.json, CHANGELOG.md, and any changed decision in the same change.
6. Run `pwsh -NoProfile -File scripts/check-rebuild.ps1` before reporting completion.
   Also run `pwsh -NoProfile -File scripts/check-discovery.ps1` after R01. If legacy files change, review their disposition and regenerate the inventory with `-RefreshInventory`; never refresh blindly to conceal unexplained deletions.
7. End each work session by recording the next task and unresolved blockers in STATUS.json.

## Architecture
- Modular Django application, PostgreSQL, server-rendered templates, HTMX, small Alpine.js interactions. Dedicated workflow screens rather than a universal schema-generated UI.
- Keep PDM for Python dependency management and command execution. Create a new tested lock in R03; do not confuse PDM environments with application configuration (.env / process environment). Read ADR 0002.
- Keep business operations in explicit services shared by HTML views and integration APIs. No financial or stock posting side effects in model save().
- Tenant and branch authorization must be explicit and tested. Resolve identity and tenancy before creating the initial application migrations (R02).
- ADR 0003 is binding: each account belongs to exactly one company; identity/auth/sessions live only in tenant schemas, not public. Read ACCESS_MODEL.md and ACCESS_VERIFICATION.md before models or adapters. Pure-policy tests do not prove database/session isolation; R04 must execute I01-I20 as applicable and retain stage-specific checks for later modules.
- ADR 0005: role templates are immutable; use access.services for grants, branch access, member state, and ownership. Do not add raw role CRUD or rely on Django admin/superuser flags for ERP authorization. Provisioning is deployment-only and must remain unavailable to public HTTP. Never expose password-link tokens in logs or URL query strings.
- Financial posting and stock operations require atomicity, concurrency tests, idempotency, and an auditable reversal path. Never delete posted documents to undo transactions.
- External calls use adapters and background delivery with retry/idempotency; never hold database locks across network calls.
- Do not claim ZATCA or insurance compliance from mocks. Record official specifications and sandbox verification separately.
- Before insurance changes read `docs/rebuild/waseel/REVIEW.md`. Raw `Waseel_PI_Document/` and its ZIP contain sample credentials and personal data and are ignored; never commit them or copy real sample values into tests. Keep the sanitized inventory current using `scripts/check_waseel_docs.py` and run `scripts/test_waseel_docs.py` with an available Python interpreter. Missing raw docs must be reported, never replaced by fabricated provider contracts.

## Cleanup
Record each deletion and its reason in CLEANUP.md, check references first, and run affected checks. Keep unresolved domain code until reviewed. Never execute legacy reset/database-deletion scripts. Do not remove migrations as a cleanup operation. Existing tracked environment files must not be copied or printed; new secrets must be ignored by Git.

No task is complete merely because its documentation or test file exists.
