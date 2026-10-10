# BrandShield AI — Data Dictionary & Database Schema

## Overview
BrandShield AI uses PostgreSQL 16 managed asynchronously via SQLAlchemy 2.0 ORM and version-controlled using Alembic migrations (revisions `001_auth_tables` through `006_brand_owner_portal_and_audit`).

---

## 1. Identity & Session Tables

### `users`
Represents registered platform actors, including Consumers (`CUSTOMER`), Brand Representatives (`BRAND_OWNER`), and Administrators (`ADMIN`).

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `phone_number` | `VARCHAR(32)` | No | — | E.164 phone number. Unique index `ix_users_phone_number`. |
| `phone_verified_at`| `TIMESTAMPTZ` | Yes | `NULL` | Timestamp when phone was verified via OTP. |
| `role` | `VARCHAR(32)` | No | `'CUSTOMER'` | User role (`CUSTOMER`, `BRAND_OWNER`, `ADMIN`). |
| `account_status` | `VARCHAR(32)` | No | `'PENDING_VERIFICATION'` | Lifecycle state (`ACTIVE`, `PENDING_VERIFICATION`, `SUSPENDED`). |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Record last modification timestamp. |

### `otp_verifications`
Short-lived challenges for passwordless authentication.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `phone_number` | `VARCHAR(32)` | No | — | Target phone number. Index `ix_otp_verifications_phone_number`. |
| `hashed_code` | `VARCHAR(128)` | No | — | HMAC-SHA256 salted hash of the 6-digit OTP code. |
| `salt` | `VARCHAR(64)` | No | — | Random cryptographic salt string. |
| `expires_at` | `TIMESTAMPTZ` | No | — | Expiration timestamp (default 5 minutes). |
| `attempts_count` | `INTEGER` | No | `0` | Number of verification attempts used. |
| `max_attempts` | `INTEGER` | No | `5` | Maximum allowable attempts before permanent lockout. |
| `is_used` | `BOOLEAN` | No | `false` | True if code has already been verified. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

### `refresh_tokens`
Long-lived cryptographic refresh tokens with single-use rotation.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `user_id` | `UUID` | No | — | Foreign key to `users.id` (`ON DELETE CASCADE`). |
| `token_hash` | `VARCHAR(128)` | No | — | SHA-256 hash of refresh token string. Unique index. |
| `salt` | `VARCHAR(64)` | No | — | Salt used during hashing. |
| `expires_at` | `TIMESTAMPTZ` | No | — | Expiration timestamp (default 7 days). |
| `is_revoked` | `BOOLEAN` | No | `false` | Revocation status flag. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

---

## 2. Brand Registration & Asset Tables

### `brand_applications`
Brand registration submissions awaiting domain verification and administrative approval.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `applicant_user_id`| `UUID` | No | — | Foreign key to `users.id`. |
| `business_name` | `VARCHAR(255)` | No | — | Official registered legal entity name. |
| `official_domain` | `VARCHAR(255)` | No | — | Normalized lowercase domain (FQDN). |
| `application_status`| `VARCHAR(64)` | No | `'PENDING_DOMAIN_VERIFICATION'` | Status (`PENDING_DOMAIN_VERIFICATION`, `PENDING_REVIEW`, `APPROVED`, `REJECTED`). |
| `review_notes` | `TEXT` | Yes | `NULL` | Internal admin review notes. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last modification timestamp. |

### `domain_challenges`
Cryptographic challenge tokens verified against authoritative DNS TXT records.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `application_id` | `UUID` | No | — | Foreign key to `brand_applications.id`. |
| `challenge_token` | `VARCHAR(128)` | No | — | Cryptographically random hex token. |
| `record_type` | `VARCHAR(16)` | No | `'TXT'` | DNS record type. |
| `record_host` | `VARCHAR(255)` | No | — | Subdomain host (`_brandshield-challenge.<domain>`). |
| `expected_value` | `VARCHAR(255)` | No | — | String `brandshield-verification=<token>`. |
| `is_verified` | `BOOLEAN` | No | `false` | True when DNS record resolves successfully. |
| `verified_at` | `TIMESTAMPTZ` | Yes | `NULL` | Verification timestamp. |
| `expires_at` | `TIMESTAMPTZ` | No | — | Expiration timestamp (default 24 hours). |

### `brands`
Authoritative verified brand records.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `application_id` | `UUID` | No | — | Unique foreign key to `brand_applications.id`. |
| `owner_user_id` | `UUID` | No | — | Foreign key to `users.id`. |
| `display_name` | `VARCHAR(255)` | No | — | Public brand title. |
| `official_domain` | `VARCHAR(255)` | No | — | Unique verified domain name. |
| `verification_status`| `VARCHAR(32)`| No | `'VERIFIED'` | Verification status (`VERIFIED`, `REVOKED`, `SUSPENDED`). |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update timestamp. |

### `brand_assets`
Official digital assets (logos, mobile packages, social handles) linked to verified brands.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `brand_id` | `UUID` | No | — | Foreign key to `brands.id`. |
| `asset_type` | `VARCHAR(32)` | No | — | Asset type (`LOGO`, `DOMAIN`, `SOCIAL_HANDLE`, `APP_PACKAGE`). |
| `asset_value` | `VARCHAR(1024)`| No | — | Asset URL, filename, or handle value. |
| `content_hash` | `VARCHAR(128)` | Yes | `NULL` | Perceptual or SHA-256 fingerprint hash. |
| `is_active` | `BOOLEAN` | No | `true` | Active status indicator. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

---

## 3. Customer Engagement Tables

### `reviews`
Customer feedback submissions subjected to moderation.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `brand_id` | `UUID` | No | — | Foreign key to `brands.id`. |
| `author_user_id` | `UUID` | No | — | Foreign key to `users.id`. |
| `rating` | `INTEGER` | No | — | Rating integer from 1 to 5. |
| `body` | `TEXT` | No | — | Review content (10–5000 characters). |
| `status` | `VARCHAR(32)` | No | `'PENDING_MODERATION'`| Moderation state (`PENDING_MODERATION`, `PUBLISHED`, `REJECTED`). |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

### `review_responses`
Official brand owner responses to published customer reviews.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `review_id` | `UUID` | No | — | Unique foreign key to `reviews.id` (`ON DELETE CASCADE`). |
| `brand_id` | `UUID` | No | — | Foreign key to `brands.id`. |
| `responder_user_id`| `UUID` | No | — | Foreign key to `users.id`. |
| `response_text` | `TEXT` | No | — | Response message content. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

---

## 4. Threat Intelligence & Scoring Tables

### `threat_reports`
Intake reports submitted by consumers or automated sensors.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `brand_id` | `UUID` | Yes | `NULL` | Optional targeted brand foreign key. |
| `reporter_id` | `UUID` | No | — | Submitting user foreign key (`users.id`). |
| `target_type` | `VARCHAR(32)` | No | — | Target type (`DOMAIN`, `URL`, `SCAM_TEXT`, `SOCIAL_PROFILE`, `APK`). |
| `target_value` | `VARCHAR(2048)`| No | — | Target address or message string. |
| `description` | `TEXT` | No | — | Reporter context description. |
| `status` | `VARCHAR(32)` | No | `'SUBMITTED'` | State (`SUBMITTED`, `ANALYZING`, `UNDER_REVIEW`, `CONFIRMED`, `BENIGN`, `RESOLVED`). |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

### `evidences`
Secure file attachments associated with threat reports.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `report_id` | `UUID` | No | — | Foreign key to `threat_reports.id`. |
| `evidence_type` | `VARCHAR(32)` | No | `'SCREENSHOT'` | Type (`SCREENSHOT`, `DOCUMENT`, `EMAIL_HEADER`, `LOG_SNIPPET`). |
| `storage_key` | `VARCHAR(1024)`| No | — | Isolated filesystem path key. |
| `sha256` | `VARCHAR(64)` | No | — | Cryptographic SHA-256 digest. |
| `original_filename`| `VARCHAR(255)`| No | — | Sanitized original filename. |
| `file_size` | `INTEGER` | No | — | Byte size of file. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |

### `risk_assessments`
Authoritative explainable risk scoring reports.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `report_id` | `UUID` | Yes | `NULL` | Foreign key to `threat_reports.id`. |
| `entity_id` | `VARCHAR(512)` | Yes | `NULL` | Optional canonical entity identifier. |
| `model_version` | `VARCHAR(64)` | No | `'1.0.0'` | Rule configuration schema version. |
| `risk_score` | `FLOAT` | No | `0.0` | Composite risk score (0.0 to 100.0). |
| `severity` | `VARCHAR(32)` | No | `'LOW'` | Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `confidence` | `FLOAT` | Yes | `1.0` | Statistical confidence metric. |
| `explanation_json` | `JSON` | No | `{}` | Evaluated signal weights and missing category breakdown. |
| `indicators_json` | `JSON` | No | `[]` | List of detected threat signals. |
| `recommendation_json`| `JSON` | No | `[]` | Actionable mitigation steps. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Assessment generation timestamp. |

---

## 5. Correlation & Campaign Tables

### `threat_entities`
Canonical deduplicated infrastructure nodes.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `entity_type` | `VARCHAR(64)` | No | — | Type (`DOMAIN`, `IP`, `URL`, `APP_PACKAGE`, `PHONE`, `EMAIL`). |
| `canonical_value` | `VARCHAR(2048)`| No | — | Normalized value string. Unique constraint with `entity_type`. |
| `first_seen_at` | `TIMESTAMPTZ` | No | `now()` | First observation timestamp. |
| `last_seen_at` | `TIMESTAMPTZ` | No | `now()` | Most recent observation timestamp. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation timestamp. |

### `entity_relationships`
Discovered linkages between infrastructure entities.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `source_entity_id` | `UUID` | No | — | Foreign key to `threat_entities.id`. |
| `target_entity_id` | `UUID` | No | — | Foreign key to `threat_entities.id`. |
| `relationship_type`| `VARCHAR(64)` | No | — | Linkage category (`RESOLVES_TO`, `HOSTS`, `DISTRIBUTES`, `SAME_CLUSTER`). |
| `relationship_status`| `VARCHAR(32)`| No | `'CANDIDATE'` | Status (`CANDIDATE`, `CONFIRMED`, `DISMISSED`). |
| `confidence` | `FLOAT` | Yes | `0.5` | Linkage confidence metric. |
| `evidence_details` | `JSON` | Yes | `NULL` | Supporting metadata diff. |

### `campaigns` & `campaign_memberships`
Aggregated threat campaigns clustering related attack nodes.

- `campaigns`: Grouping entity with `id`, `brand_id`, `title`, `status`, `risk_score`, `description`, `created_at`, `updated_at`.
- `campaign_memberships`: Join table linking `campaign_id` to `entity_id` with `relationship_reason`.

### `alerts`
Actionable security alerts surfaced on the brand owner portal.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `brand_id` | `UUID` | No | — | Foreign key to `brands.id`. |
| `campaign_id` | `UUID` | Yes | `NULL` | Optional linked `campaigns.id`. |
| `severity` | `VARCHAR(32)` | No | `'MEDIUM'` | Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `status` | `VARCHAR(32)` | No | `'OPEN'` | Incident status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`). |
| `title` | `VARCHAR(255)` | No | — | Alert headline. |
| `description` | `TEXT` | No | — | Incident summary details. |
| `dedup_fingerprint`| `VARCHAR(64)` | No | — | Unique hash string preventing redundant alerts. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last modification timestamp. |

---

## 6. Audit Logging Table

### `audit_logs`
Immutable administrative and security operation audit trail. Any SQL `UPDATE` or `DELETE` attempt is strictly intercepted and blocked by SQLAlchemy event listeners.

| Column | Type | Nullable | Default | Description / Constraints |
|---|---|---|---|---|
| `id` | `UUID` | No | `uuid4()` | Primary key. |
| `actor_user_id` | `UUID` | No | — | Foreign key to `users.id`. |
| `brand_id` | `UUID` | Yes | `NULL` | Optional context brand foreign key. |
| `action` | `VARCHAR(128)` | No | — | Action name (`ALERT_STATUS_UPDATE`, `BRAND_APPLICATION_APPROVE`, etc.). |
| `entity_type` | `VARCHAR(64)` | No | — | Affected entity type (`ALERT`, `BRAND`, `REVIEW`). |
| `entity_id` | `VARCHAR(128)` | No | — | Identifier string of modified entity. |
| `details` | `JSON` | No | `{}` | State diff before and after action. |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Event occurrence timestamp. |
