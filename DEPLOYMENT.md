# Deployment and recovery runbook

This repository can build container images for the Next.js frontend and FastAPI API. `deploy/compose.yaml` is a provider-neutral starting point for any container host. It deliberately connects to an externally provisioned PostgreSQL service; it does not create a shared database or supply credentials. Run a release migration with `docker compose --profile release run --rm migrate`, then deploy the API and frontend. `/health` is liveness; `/ready` verifies database connectivity and is the readiness probe. CI provisions its own disposable PostgreSQL service and has no deployment credentials.

## Three isolated environments

Provision three PostgreSQL databases or clusters and three distinct database roles, passwords, secret-manager scopes, and migration histories:

| Environment | Settings | Database requirements |
| --- | --- | --- |
| TEST | `backend/.env.test.example` | Disposable local SQLite or PostgreSQL database named with `test`; never use staging/production credentials. CI uses an ephemeral PostgreSQL 16 service. |
| STAGING | `backend/.env.staging.example` | Persistent PostgreSQL database whose name contains `staging`, separate role and secret scope. Use payment sandbox credentials and realistic non-customer data. |
| PRODUCTION | `backend/.env.production.example` | Protected PostgreSQL database, separately provisioned role and secret scope. Only the production deployment pipeline/operator gets access. |

Supply values through the host secret manager. Never commit populated `.env` files or put production secrets into GitHub Actions. The settings validator rejects SQLite on staging/production, staging URLs without a staging database name, and test URLs targeting staging/production. These are guardrails, not substitutes for distinct hosts, roles, network policies, and cloud IAM. Restrict production database connectivity to production workloads and the explicitly controlled migration job. CI cannot reach production and has no production secret variables.

## SQLite to PostgreSQL transition

Do not point PostgreSQL at a SQLite file or copy the SQLite file. Provision an isolated staging PostgreSQL database, take a consistent SQLite backup, export/import rows with a reviewed data migration that preserves UUIDs, UTC instants, monetary decimal values, uniqueness and foreign-key relationships, then validate row counts and financial/inventory totals. Exercise Alembic on an empty PostgreSQL database first (`cd backend && DATABASE_URL=... alembic upgrade head && alembic check`). Run the data import in staging, compare key totals and identifiers, and execute realistic UAT before scheduling production cutover. Freeze writes, take a final source backup, repeat the import, verify totals, apply any pending Alembic revisions, and switch the production application to the provisioned PostgreSQL URL. Keep the source snapshot read-only until acceptance. This repository does not yet include a general SQLite-to-PostgreSQL data importer; plan and rehearse that mapping before moving existing live data.

Every schema change is an Alembic revision. Verify a clean database migration and `alembic check` in CI; apply the exact image's migration job to staging before production. Back up before destructive/schema-sensitive releases. Never run `create_all()` to provision a deployed schema.

## Domain, HTTPS, browser origins

For the intended topology, publish DNS records for `app.example.com` to the frontend host and `api.example.com` to the API host, following the selected provider's targets. The domain is an example and is not represented as registered or configured. Provision TLS certificates at the ingress/provider, redirect HTTP to HTTPS, and forward only the required proxy headers. Set:

* For the same-origin proxy topology in Compose, build with `NEXT_PUBLIC_API_URL=/api` and set `NEXT_BACKEND_API_URL` to the private API service URL. For separate public subdomains, build with `NEXT_PUBLIC_API_URL=https://api.example.com`; route `api.example.com` to the API ingress and allow `https://app.example.com` in CORS.
* API `CORS_ORIGINS=https://app.example.com` (comma-separated exact origins only).
* `WEBAUTHN_RP_ID=app.example.com` and `WEBAUTHN_ORIGIN=https://app.example.com`; the origin must match the browser page origin exactly.
* Invitation/recovery callback base URL to `https://app.example.com` in the future email provider integration; configure Paystack callback URLs using the provider's dashboard and the production HTTPS origin when that integration exists.

Current authentication returns bearer/refresh tokens in JSON and the frontend manages them; this app does not currently set authentication cookies. If cookie auth is introduced, use `Secure`, `HttpOnly`, an appropriate `SameSite` policy, CSRF protection, and review the cross-subdomain deployment. HTTPS at the edge does not by itself make a cookie-based auth flow secure.

## Current integration readiness

The backend now defines provider-neutral contracts for transactional email, private object storage, payment providers, webhook processing and external error reporting. Paystack mode/key validation prevents test deployments from loading live keys, and the raw-body HMAC-SHA512 webhook verifier is unit tested. These are boundaries, not configured services: there is still no email/storage/payment adapter, Paystack initiation or webhook route, durable webhook idempotency table, or external error-monitoring SDK. Existing notification records are in-app database notifications; invitation/recovery flows do not deliver email. Expense attachments are references, not uploaded files. Do not enter production keys or route real payments to this version. Before enabling these capabilities, implement and test private storage for product images, device images, attachments and supported receipts/documents with MIME/size validation, access control and short-lived signed URLs; an email transport for invitations, activation, account recovery, security and operational notices with delivery, retry and token-redaction behavior; and Paystack TEST/SANDBOX and LIVE/PRODUCTION checkout/reconciliation with separate provider projects and credentials, durable idempotency keys, transactional state changes, duplicate-safe replay and immutable audit records.

## Backups, restore, rollback, disaster recovery

Before launch, select provider-native encrypted PostgreSQL backups with point-in-time recovery. A starting policy is daily snapshots plus continuous WAL/PITR, 35-day retention, and a separately protected monthly archive retained for 12 months; set final RPO/RTO and retention with the business and applicable regulations. Keep backups in a separate account/project with access logging and encryption. Back up object data separately after an object-storage adapter is deployed. Alert on backup failures.

At least quarterly, restore the database and object backup into an isolated recovery environment, verify Alembic state, login, inventory/IMEI traceability, sales/payment/return totals, and record restore duration. Never restore production data into staging without approval and a privacy-safe sanitization process. For application rollback, redeploy the previous immutable image only when its schema remains compatible. Prefer additive expand/migrate/contract revisions; if a migration is irreversible, recovery is restore/PITR and a rehearsed forward fix, not an assumed reverse migration. Record a cutover/rollback owner and decision threshold for each release.

## Release checks and remaining human actions

CI runs backend tests, empty PostgreSQL migration/schema comparison, frontend typecheck/lint/build and dependency audits using disposable credentials only. Before hosting, a human must provision the three isolated PostgreSQL environments and secret scopes, select host/provider, deploy staging, configure DNS/TLS, run staging UAT and restore drill, and then approve production cutover. Object storage, email, payment webhook and external error monitoring require application implementation and provider accounts before they can be marked ready.
