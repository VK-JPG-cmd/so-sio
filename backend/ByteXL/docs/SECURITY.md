# BrandShield AI — Security Architecture & Hardening Guide

## Notice
> [!IMPORTANT]
> **Security Notice**: This document details the threat model, technical defenses, and hardening measures implemented for BrandShield AI Phase 10. Security is an ongoing, defense-in-depth discipline; no system is entirely invulnerable. Continued adherence to secure development lifecycles, dependency vulnerability monitoring, external penetration testing, and operational hygiene is essential.

---

## 1. Threat Model & Architectural Boundaries

BrandShield AI ingests untrusted user inputs (URLs, mobile application packages, brand domain assertions, textual scam reports) from diverse threat environments. The threat model is structured around STRIDE principles across system boundaries:

```
[ Untrusted Client / Attacker ]
           │
           │ (HTTPS / Rate Limited)
           ▼
┌──────────────────────────────────────────────┐
│ FastAPI Application Boundary                 │
│  - JWT & Revocation Blacklist                │
│  - Role-Based Access Control (RBAC)          │
│  - Rate Limiting Middleware                  │
│  - PII & Secret Redaction Logging Filter     │
└──────────────┬───────────────────────────────┘
               │
       ┌───────┴───────────────────────┐
       ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ Threat Analysis Sandbox   │   │ PostgreSQL Database       │
│  - URL Offline Analysis   │   │  - Parameterized Queries  │
│  - SSRF / Rebinding Guard │   │  - LIKE Wildcard Escaping │
│  - APK Zip Bomb & Quota   │   │  - Immutable Audit Logs   │
│  - Non-Executing Worker   │   │  - Localhost (127.0.0.1)  │
└───────────────────────────┘   └───────────────────────────┘
```

### STRIDE Assessment

| Threat Category | Primary Risk Vectors | Architectural Defense |
|---|---|---|
| **Spoofing** | Forged JWTs, unauthorized OTP verification, fake brand registrations | Cryptographically signed tokens (HS256/RS256), salted SHA-256 token hashes, constant-time OTP comparison, DNS TXT challenge verification for brand claims. |
| **Tampering** | Modification of administrative audit trails, parameter tampering in URL analyses, archive traversal | Database-level append-only immutable audit logs (`before_update`/`before_delete` exception hooks), strict Pydantic schemas, zip member path sanitization. |
| **Repudiation** | Denying administrative actions or review status changes | Comprehensive `audit_logs` tracking actor UUID, target resource type, prior and new state diffs, and UTC timestamps. |
| **Information Disclosure** | Cloud metadata extraction via SSRF, stack traces in API errors, credentials in logs | Multi-layer IP & metadata endpoint validator, custom exception-to-HTTP mapping preventing internal traceback leaks, automated log redaction filters. |
| **Denial of Service** | Zip bombs (decompression bombs), unbounded file streaming, brute-force OTP attempts | 50 MB streaming upload limits, archive member compression ratio (<100:1) & uncompressed byte caps (250 MB total, 100 MB single file), sliding-window rate limiters. |
| **Elevation of Privilege** | Cross-user/cross-brand direct object referencing (IDOR), role manipulation | Token role verification (`CUSTOMER`, `BRAND_OWNER`, `ADMIN`), ownership checks on analysis jobs (`creator_user_id`), brand-scoped database queries. |

---

## 2. Security Mitigations Across 9 Backend Domains

### Domain 1: Authentication
1. **JWT Lifecycle & Expiration**:
   - Access tokens are short-lived (default 15 minutes), containing standard claims (`sub`, `role`, `jti`, `exp`, `iat`).
   - Refresh tokens are cryptographically random strings (32 bytes urlsafe base64), stored only as salted SHA-256 hashes with single-use rotation. Old refresh tokens are invalidated upon renewal.
2. **Access Token Revocation**:
   - Implemented thread-safe in-memory JTI revocation cache (`revoke_access_token`, `is_access_token_revoked`). Calling `/api/v1/auth/logout` extracts the active bearer token's JTI and invalidates it immediately, rejecting subsequent calls with `401 Unauthorized`.
3. **OTP Security**:
   - One-Time Passwords use constant-time verification (`hmac.compare_digest`) to prevent timing side channels.
   - Failed attempts commit immediately to the database prior to returning responses, ensuring that failed attempt counters persist even if caller requests trigger rollbacks. Exceeding 5 attempts locks the OTP record permanently.

### Domain 2: Authorization & IDOR Defenses
1. **Role-Based Access Control (RBAC)**:
   - Explicit role dependencies (`get_current_active_user`, `require_admin`, `require_brand_owner`, `require_customer`).
2. **Analysis Job IDOR Defense**:
   - Background analysis jobs record `creator_user_id`. Endpoint `/api/v1/analyze/jobs/{job_id}` verifies that requesting users are either the original creator or system administrators, returning `403 Forbidden` for cross-user attempts.
3. **Brand Context Isolation**:
   - Brand owners are restricted strictly to assets, threat campaigns, and DNS verification records linked to their owned brands.

### Domain 3: URL Analysis & SSRF Prevention
1. **Safe Offline Analysis Policy**:
   - The backend avoids visiting or downloading untrusted URLs during routine scanning; analysis is deterministic and heuristic-driven.
2. **Comprehensive IP Validation (`validate_ip_address`)**:
   - Blocks private RFC1918 IPv4 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), RFC4193 IPv6 (`fc00::/7`), loopback (`127.0.0.0/8`, `::1`), and link-local (`169.254.0.0/16`, `fe80::/10`).
   - Blocks alternative IP formats: decimal integer notation (`2130706433`), hexadecimal notation (`0x7f000001`), octal notation (`017700000001`), and IPv4-mapped IPv6 (`::ffff:127.0.0.1`).
   - Blocks cloud metadata endpoints across AWS, GCP, Azure, and Alibaba (`169.254.169.254`, `100.100.100.200`, `fd00:ec2::254`, `instance-data`, `metadata.google.internal`).
   - Blocks private domain suffixes (`.internal`, `.local`, `.localhost`, `.lan`, `.corp`, `.home`).
3. **Safe Outbound Fetching (`safe_fetch_url`)**:
   - Validates destination IP before connection and re-validates destination IP on every HTTP redirect.
   - Enforces redirect limit (5 max), timeouts (5.0s), and strictly bounded streaming download limits (5 MB max) to prevent unbounded response downloads.

### Domain 4: File Uploads & Archive Safety
1. **Streaming Size Bound**:
   - Upload endpoints (`/api/v1/analyze/apk`) stream incoming chunks with a strict 50 MB threshold, terminating immediately with `ValidationError` (HTTP 400/413) if exceeded, preventing in-memory exhaustion.
2. **Path Traversal & Filename Cleansing**:
   - Sanitizes uploaded filenames removing path separators (`/`, `\`) and directory traversal sequences (`..`).
3. **Zip Bomb & Archive Safety (`APKAnalysisService`)**:
   - Pre-flight ZIP archive inspection validates each archive member.
   - Blocks path traversal inside archive filenames (`..`, absolute paths).
   - Enforces maximum single-entry uncompressed size (100 MB) and cumulative uncompressed size (250 MB).
   - Rejects archives with abnormal decompression ratios (>100:1) to mitigate zip bomb attacks.
4. **Execution Sandbox**:
   - Static analysis is sandboxed in a thread pool with a 30-second timeout; no binaries are executed.

### Domain 5: Database Hardening
1. **SQL Injection Elimination**:
   - All queries use SQLAlchemy ORM or parameterized constructs.
2. **LIKE Wildcard Escaping**:
   - Created `escape_like_wildcards` in repository layer to escape `%`, `_`, and `\` in user search queries, eliminating wildcard injection DoS.
3. **Entity Constraints**:
   - Schema enforcement via UUID primary keys, unique constraints on domains and phone numbers, foreign key constraints with explicit cascade policies.
4. **Credential Protection**:
   - OTP codes and tokens are stored hashed; sensitive fields are excluded from Pydantic serialization models.

### Domain 6: API Security & Hardening
1. **Rate Limiting**:
   - Sliding-window in-memory rate limiting applied to sensitive endpoints (OTP generation, OTP verification) with IP-based client tracking.
2. **Production Mode Security**:
   - Interactive API documentation (`/docs`, `/redoc`, `/openapi.json`) is disabled automatically when `ENVIRONMENT == "production"`.
3. **CORS Hardening**:
   - Restricts `allow_headers` to an explicit safe list (`Authorization`, `Content-Type`, `X-Request-ID`) and exposes correlation headers.
4. **Error Disclosure Prevention**:
   - Centralized exception handlers catch domain and generic exceptions, returning sanitized structured JSON error responses without disclosing internal stack traces or database driver details.
5. **Pagination Bounds**:
   - Pagination parameters enforce upper limits (e.g. `limit <= 100`, `page_size <= 100`) to prevent large result set DoS.

### Domain 7: Logging & PII Redaction
1. **Log Redaction Filter (`RedactionFilter`)**:
   - Automatically inspects all log records.
   - Redacts Bearer tokens (`Bearer [REDACTED_TOKEN]`), JWT tokens (`[REDACTED_JWT]`), database URLs with credentials (`postgresql://user:***@host`), OTP codes (`otp=[REDACTED_OTP]`), and phone numbers (`[REDACTED_PHONE]`).
2. **Data Structure Sanitization**:
   - Provides recursive dictionary scrubber `sanitize_data_structure` for structured payloads before emission to log aggregators.

### Domain 8: Infrastructure Hardening
1. **Container Port Isolation**:
   - In `docker-compose.yml`, PostgreSQL port binding is restricted to `127.0.0.1:5432:5432`, preventing direct exposure to external network interfaces.
2. **Secret Management**:
   - Startup validation ensures production deployments fail fast if default or insecure secrets (`JWT_SECRET_KEY`) are present.
3. **Dependency Maintenance**:
   - Explicit pinned dependency ranges in `pyproject.toml` with `greenlet>=3.0.0` and `python-multipart>=0.0.9`.

### Domain 9: Audit Logging & Immutability
1. **Audit Coverage**:
   - Administrative and security-sensitive operations (brand verification, threat report status updates, review moderation) are logged to `audit_logs` with actor UUID, action name, entity ID, and change diffs.
2. **Database Immutability Enforcement**:
   - SQLAlchemy event listeners (`before_update`, `before_delete`) attached to `AuditLog` raise `PermissionError` on any modification or deletion attempt, preserving audit trail integrity.

---

## 3. Security Regression Test Suite

All security hardening mitigations are backed by automated tests in `tests/integration/test_security_hardening.py` alongside the full test suite.

### Verified Scenarios:
1. `test_access_token_revocation_on_logout`: Invalidation of access token JTI on logout, subsequent requests return 401.
2. `test_otp_bruteforce_lockout_persists`: Failed OTP attempts accumulate persistently across rollbacks and lock after 5 attempts.
3. `test_analysis_job_idor_prevention`: Analysis jobs created by User A return 403 Forbidden when requested by User B.
4. `test_ssrf_ip_and_metadata_validation`: Rejection of integer IPs, IPv4-mapped IPv6, AWS/GCP/Alibaba metadata, loopback, and `.internal` domains.
5. `test_apk_streaming_upload_limit`: Rejection of APK uploads exceeding 50 MB limit.
6. `test_apk_zip_bomb_detection`: Detection and rejection of zip archives with >100:1 compression ratio.
7. `test_apk_path_traversal_detection`: Rejection of archives containing traversal filenames (`../../etc/passwd`).
8. `test_sensitive_data_redaction_filter`: Scrubbing of passwords, JWTs, Bearer tokens, OTPs, and phone numbers from logs.
9. `test_audit_log_immutability`: Verification that updates and deletions on `AuditLog` records raise `PermissionError`.
10. `test_sql_like_wildcard_escaping`: Validation that `%`, `_`, and `\` characters are escaped properly.

### Execution Results:
```text
====================== 151 passed, 7 warnings in 49.04s =======================
```

---

## 4. Unresolved Findings & Risk Register

The following unresolved security findings and architectural considerations remain:

### Medium Severity
1. **In-Memory Revocation & Rate Limiter in Distributed Environments**:
   - *Description*: The active token revocation blacklist and sliding-window rate limiters currently reside in process memory.
   - *Impact*: In a multi-worker or multi-container deployment, token revocation on Worker A will not be recognized by Worker B unless backed by a distributed store.
   - *Remediation*: Back `InMemoryRateLimiter` and `revoked_tokens` cache with a shared Redis or Memcached cluster in production.

2. **Synchronous DNS Lookup in Worker Analysis**:
   - *Description*: DNS resolution on external domains during live background fetches can experience network delays or timeouts.
   - *Impact*: Potential worker starvation or temporary delay if multiple unresolvable domains are processed simultaneously.
   - *Remediation*: Use asynchronous DNS resolution via `aiodns` or offload to background celery/task queues with worker pool concurrency limits.

### Low Severity
1. **Static Pre-Flight MIME Type Validation**:
   - *Description*: File uploads are inspected by file header and content parser (e.g. `zipfile.is_zipfile`), but file content magic bytes are validated post-upload.
   - *Impact*: Malformed files are rejected during parsing rather than at the earliest ingress gateway byte.
   - *Remediation*: Integrate `python-magic` / `libmagic` at the gateway boundary to inspect the first 512 bytes before streaming the remainder.

2. **Database Level Trigger vs Application Listener for Audit Logs**:
   - *Description*: Audit log immutability is enforced via SQLAlchemy ORM event listeners (`before_update`/`before_delete`).
   - *Impact*: If a database administrator executes raw SQL updates directly via `psql` outside the application layer, the ORM listeners will not intercept the query.
   - *Remediation*: Implement PostgreSQL native database triggers (`CREATE TRIGGER ... BEFORE UPDATE OR DELETE ON audit_logs FOR EACH ROW EXECUTE FUNCTION abort_audit_mutation()`) or grant only `INSERT, SELECT` permissions on `audit_logs` to the application database user.

### Informational
1. **Dynamic APK Execution**:
   - *Description*: The current APK analyzer operates strictly in static mode using Androguard and explicitly does not execute untrusted binaries.
   - *Impact*: Dynamic behavior, packed malware, or runtime payload downloading cannot be observed.
   - *Remediation*: If dynamic analysis is added in future phases, execute samples strictly inside dedicated ephemeral virtual machines (e.g., microVMs like Firecracker) with isolated network namespaces.

---

## 5. Production Deployment Recommendations

For production deployments, the following infrastructure controls must be applied:

1. **Reverse Proxy & WAF Configuration**:
   - Deploy behind a reverse proxy (Nginx, Cloudflare, or AWS ALB) terminating TLS 1.3 with strict HSTS (`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`).
   - Configure Web Application Firewall (WAF) rules to filter malicious payloads, large request bodies (>50MB), and known exploit signatures.
2. **Secrets Management**:
   - Do not store production secrets (`JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, etc.) in `.env` files. Inject them securely via cloud secret stores (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault).
3. **Database Permissions**:
   - Principle of Least Privilege: The application database user should only have `SELECT, INSERT, UPDATE, DELETE` on operational tables, and only `SELECT, INSERT` on `audit_logs`. DDL permissions (`CREATE`, `DROP`, `ALTER`) should be restricted to migration execution tools.
4. **Container Security**:
   - Run containers with non-root user accounts (`USER 10001:10001`).
   - Enforce read-only root filesystems (`read_only: true`) with ephemeral tmpfs volumes for temporary scratch directories.
   - Drop all default Linux capabilities (`cap_drop: ["ALL"]`) and add only necessary capabilities.
