---

## 1. Project Overview & System Architecture

BrandShield AI is an AI-powered Digital Risk Protection (DRP) platform engineered to defend organizations, brand owners, and consumers against brand impersonation, fraudulent lookalike domains, credential harvesting portals, social scam campaigns, malicious mobile application packages (APKs), and rogue app-store listings.

The system is built as a high-assurance, modular backend using FastAPI, asynchronous SQLAlchemy 2.0, PostgreSQL 16, and Alembic migrations.

```
                                  [ Client Layer ]
              (Web Frontends / SOC Analyst Consoles / Interactive Dashboard)
                                         │
                                         ▼ HTTPS / TLS 1.3
                            ┌───────────────────────────┐
                            │   Reverse Proxy / Gateway │
                            │  (Rate Limiting & CORS)   │
                            └─────────────┬─────────────┘
                                         │
                                         ▼ ASGI (Port 8000)
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application Boundary                                                          │
│                                                                                       │
│  ├── API Layer (/api/v1 & Dashboard)                                                  │
│  │    ├── Interactive SOC Dashboard (/, /dashboard)                                   │
│  │    ├── Auth & Session Management (/auth)                                           │
│  │    ├── User Identity & Profiles (/users)                                           │
│  │    ├── Brand Registration & Verification (/brand-applications)                     │
│  │    ├── Public Brand Discovery & Customer Reviews (/brands, /reviews)               │
│  │    ├── Threat Intake & Evidence Attachments (/threat-reports)                      │
│  │    ├── Detection Engines & Async Workflows (/analyze)                              │
│  │    ├── Brand Owner Operations & Graph Portal (/owner)                              │
│  │    ├── Threat Discovery Admin API (/admin/discovery)                               │
│  │    ├── Platform Administration (/admin)                                            │
│  │    └── Health & Readiness Probes (/health, /ready)                                 │
│  │                                                                                    │
│  │── Core & Security Layer                                                            │
│  │    ├── Security Headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options)       │
│  │    ├── JWT Authentication (HS256) with JTI Blacklist Revocation                    │
│  │    ├── Passwordless Phone OTP with Salted HMAC-SHA256 Verification                 │
│  │    ├── In-Memory Sliding-Window Rate Limiting Middleware                           │
│  │    ├── Secret, Token, and PII Log Redaction Filter                                 │
│  │    ├── Multi-layer SSRF Shield (RFC 1918, Loopback, Cloud Metadata, Octal/Hex IP)  │
│  │    └── Strict Magic Byte Inspection & Safe File Storage                            │
│  │                                                                                    │
│  ├── AI & Detection Engines                                                           │
│  │    ├── Domain & URL Threat Engine (SSRF Shields, Homoglyph Mapping, Typosquatting) │
│  │    ├── Social Profile Impersonation Engine (Handle Similarity, Bio, Avatar Hash)   │
│  │    ├── App Store Listing Metadata Analysis (Publisher, Package ID, Permissions)    │
│  │    ├── APK Static Analysis (Androguard, Manifest Inspection, Zip Bomb Defense)     │
│  │    ├── Scam Text Classifier (TF-IDF + Linear Statistical Model)                    │
│  │    ├── Visual Impersonation Engine (Perceptual pHash / dHash)                      │
│  │    ├── Unified Explainable Risk Scoring Engine (Configurable Category Caps)        │
│  │    └── Campaign Correlation Engine (Entity Disambiguation & Graph Clustering)      │
│  │                                                                                    │
│  ├── Automated Threat Discovery Pipeline                                              │
│  │    ├── Background Polling Worker (Single-Instance asyncio Lock)                    │
│  │    ├── External Feed Connectors (abuse.ch URLhaus, Social Mock, Mobile Mock)       │
│  │    ├── Indicator Normalization & Idempotent Persistence                            │
│  │    ├── Incremental Checkpoint Tracker with Overlapping Lookback Window             │
│  │    └── Automated Brand Matching & Campaign/Alert Fanout                            │
│  │                                                                                    │
│  └── Persistence & Data Access (PostgreSQL 16 Async)                                  │
│       ├── 22 Relational Entities with Strict Constraints & UUID Primary Keys          │
│       ├── Parameterized Repositories with SQL LIKE Wildcard Escaping                  │
│       └── Immutable Administrative Audit Logs                                         │
└────────────────────────────────────────┬──────────────────────────────────────────────┘
                                         │
                                         ▼ asyncpg
                         ┌───────────────────────────────┐
                         │      PostgreSQL 16 Engine     │
                         │   - Loopback Bound (127.0.0.1)│
                         │   - Persistent Named Volume   │
                         │   - Versioned Alembic Schema  │
                         └───────────────────────────────┘
```

---

## 2. Supported Detection Capabilities

1. **Domain & Lookalike Threat Detection**:
   - RFC-compliant URL parsing, IDN Punycode decoding, homoglyph character translation (`0` → `o`, Cyrillic `а` → Latin `a`).
   - Levenshtein edit distance, Token Sort Ratio, and prefix/suffix typosquatting detection.
   - Comprehensive multi-layer SSRF boundary validation blocking loopback (`127.0.0.1`), private RFC 1918 subnets, cloud metadata (`169.254.169.254`), and hex/octal IP obfuscations.
2. **Social Profile Impersonation Analysis**:
   - Compares candidate handles, display names, profile bios, and avatars against registered brand assets.
   - Built-in official account exemption preventing verified brand handles from self-flagging.
   - Bio text scam signal detection and visual avatar perceptual hashing.
3. **App Store Listing Metadata Analysis**:
   - Analyzes candidate mobile application listings against registered brand mobile assets (`BrandMobileApp`).
   - Compares package names, developer/publisher names, app titles, store URLs, and advertised permissions.
   - Distinguishes exact official apps, lookalike publisher fraud, and untrusted repackaging attempts.
4. **Android APK Static Inspection**:
   - Static Dalvik bytecode and AndroidManifest.xml analysis via Androguard.
   - Detection of dangerous permissions (`RECORD_AUDIO`, `SEND_SMS`, `SYSTEM_ALERT_WINDOW`, `REQUEST_INSTALL_PACKAGES`).
   - Strict zip-bomb decompression limits (max 50 MB, decompression ratio ceiling).
   - Zero-execution guarantee: APKs are analyzed strictly statically and never executed.
5. **Campaign Correlation & Alert Deduplication**:
   - Multi-surface graph correlation clustering threats by registrant, infrastructure, and brand targets.
   - Alert deduplication preventing alert fatigue while tracking recurring incident timestamps.
6. **Continuous Automated Threat Discovery**:
   - Ingests public threat intelligence feeds (abuse.ch URLhaus).
   - Normalizes, deduplicates, and evaluates indicators against all registered brand profiles.

---

## 3. Official Brand Asset Registry

Brand owners can register their official operational footprint to prevent self-flagging and power accurate impersonation detection:
- **Official Domains**: Stored via `BrandAsset` with `asset_type=OFFICIAL_DOMAIN` and verified status.
- **Official Social Handles**: Stored via `OfficialSocialAsset` capturing platform (`TWITTER`, `INSTAGRAM`, `LINKEDIN`, etc.), handle, profile URL, verified badge status, and follower count.
- **Official Mobile Applications**: Stored via `BrandMobileApp` capturing package identifier (`com.brand.app`), platform (`GOOGLE_PLAY`, `APPLE_APP_STORE`), publisher name, and official store URLs.

---

## 4. Threat Discovery Architecture & Pipeline

```
External Threat Feed (URLhaus)
           ↓
ThreatSourceConnector.fetch_recent_indicators()
           ↓ (DiscoveredIndicatorRecord validation & SSRF sanitization)
DiscoveredIndicatorRepository.get_or_create() (Idempotent canonical deduplication)
           ↓
ThreatDiscoveryPipeline.process_indicator()
   ├─ Exact Official Domain Check (Auto-exempt verified brand assets)
   ├─ Brand Identification (Domain name match & lookalike analysis)
   ├─ Unified Risk Assessment (DomainThreatService & ScamClassifier)
   ├─ ThreatEntity Repository (Persistent cross-source entity)
   ├─ ThreatCorrelationService (Campaign clustering)
   └─ AlertRepository (Actionable SOC alerts with deduplication)
           ↓
DiscoveryCheckpointRepository (Commit checkpoint & update operational stats)
```

### URLhaus Integration
- Connector: `app/services/discovery/connectors/urlhaus.py`
- Source API: `https://urlhaus-api.abuse.ch/v1/urls/recent/`
- Authentication: Configurable via `URLHAUS_AUTH_KEY` environment variable.
- Safe Polling Strategy: Because public feed IDs are not strictly sequential, the connector employs an overlapping lookback window (`URLHAUS_LOOKBACK_MINUTES=60`) paired with strict database-level unique constraints `(source_id, canonical_value)`. Repeated polling updates `last_observed_at` without duplicating indicators, campaigns, or alerts.

### Social and Mobile Discovery Status
- Social feeds and mobile app-store search crawlers are provided as documented extension points (`SocialMediaMockConnector`, `MobileAppStoreMockConnector`).
- When external API keys (`TWITTER_BEARER_TOKEN`, `SERPAPI_KEY`) are unconfigured, these connectors safely report `NOT_CONFIGURED` without failing the application or inventing simulated live threats.

---

## 5. Security & Isolation Controls

- **Role-Based Access Control (RBAC)**: All administrative discovery endpoints (`/api/v1/admin/discovery/*`) strictly enforce `require_admin`. Brand owners are restricted exclusively to their assigned brands via `verify_brand_owner_access`.
- **SSRF Hardening**: External URLs submitted in threat reports or discovered from feeds are validated against DNS rebinding, loopback, link-local, private subnets, and metadata endpoints. Threat indicators are parsed as data and never automatically requested or fetched by the server.
- **Upload Safety**: Max 50 MB limit, magic byte validation, static analysis only.
- **Log & Secret Protection**: Logging filters redact tokens, JWTs, and passwords. Stack traces are suppressed in production mode.
- **Security Headers**: Standard HTTP headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`) applied to all responses.

---

## 6. Interactive Command Center Dashboard

The application serves an interactive, responsive Cybersecurity Command Center directly at:
- **URL**: `http://localhost:8000/dashboard` (also accessible at root `http://localhost:8000/`)
- **Features**:
  - Live system status & discovery worker telemetry (polling interval, total indicators, new records, duplicates).
  - External threat intelligence connector status (URLhaus, Social Media, App Stores).
  - High-severity active alerts with supporting evidence, timestamps, and recommended SOC actions.
  - Interactive Incident Review Modal: Reviewers can update alert status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`) with reviewer notes.
  - Correlated Threat Campaigns with affected brands and entity clustering breakdown.
  - Recent Discovered Indicators table with risk scores, source tags, and review statuses.
  - Synthetic Evaluation Benchmark accuracy metrics banner (100% Precision, 100% Recall on test fixtures).

---

## 7. Database Migrations Status

The database schema is managed via Alembic across 8 sequential revisions:
1. `001_auth_tables`: `users`, `otp_verifications`, `refresh_tokens`.
2. `002_brand_tables`: `brand_applications`, `domain_challenges`, `brands`, `brand_assets`.
3. `003_reviews_and_threat_reports`: `reviews`, `threat_reports`, `evidences`.
4. `004_risk_assessments`: `risk_assessments`.
5. `005_threat_intel_and_campaigns`: `threat_entities`, `entity_relationships`, `campaigns`, `campaign_memberships`, `alerts`.
6. `006_brand_owner_portal_and_audit`: `review_responses`, `audit_logs`.
7. `007_official_brand_assets`: `official_social_assets`, `brand_mobile_apps`.
8. `008_create_threat_discovery_tables`: `discovery_checkpoints`, `discovered_indicators`.

---

## 8. Startup & Operational Instructions

### Prerequisites
- Python 3.11 or Python 3.12
- PostgreSQL 15+ (or Docker running PostgreSQL)

### Local Virtual Environment (PowerShell on Windows)
```powershell
# 1. Activate Virtual Environment
.venv\Scripts\Activate.ps1

# 2. Configure Environment Variables
Copy-Item .env.example .env

# 3. Run Database Migrations
alembic upgrade head

# 4. Launch ASGI Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Compose
```bash
# Build and run backend + PostgreSQL
docker compose up --build -d

# View logs
docker compose logs -f api
```

---

## 9. Testing & Evaluation

### Running the Full Test Suite
The automated test suite runs 240 tests across unit, integration, security, and migration checks:
```bash
.venv\Scripts\python.exe -m pytest tests/ --tb=short -q
```
**Test Result**: `240 passed, 3 warnings in 84.86s` (100% passing).

### Running the Synthetic Evaluation Benchmark
BrandShield AI includes a reproducible synthetic evaluation harness testing domain lookalikes, social impersonation, scam text, and app metadata across 35 realistic fixtures:
```bash
.venv\Scripts\python.exe scripts/evaluate_detection.py
```
**Evaluation Metrics**:
- Total Test Cases: `35`
- True Positives: `25`
- False Positives: `0`
- True Negatives: `10`
- False Negatives: `0`
- Precision: `1.0000` (100.0%)
- Recall: `1.0000` (100.0%)
- F1 Score: `1.0000` (100.0%)
- False Positive Rate: `0.0000` (0.0%)
*(Explicitly labeled as synthetic-test benchmark results).*

### Running the URLhaus Live-Feed Smoke Test
To verify live provider connectivity:
```bash
.venv\Scripts\python.exe scripts/smoke_test_urlhaus.py
```
- When unconfigured or missing `URLHAUS_AUTH_KEY`: Reports `NOT_VERIFIED` with clear setup guidance.
- When configured with valid key: Fetches, normalizes, and reports actual live feed status.

---

## 10. Admin Endpoints Reference

All discovery admin endpoints require `Authorization: Bearer <token>` with `role=ADMIN`:
- `GET /api/v1/admin/discovery/health`: Check background worker state and connector statuses.
- `GET /api/v1/admin/discovery/stats`: View aggregated indicators processed, alerts created, and checkpoints.
- `POST /api/v1/admin/discovery/run-now`: Manually trigger an immediate discovery cycle.
- `GET /api/v1/admin/discovery/indicators`: Paginated view of discovered threat indicators.
- `PATCH /api/v1/owner/alerts/{alert_id}`: Update alert status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`) with review notes.

---

## 11. Known Limitations & Future Roadmap

1. **In-Memory Rate Limiting & Background Worker in Clustered Environments**: The current sliding-window rate limiters and background worker coordination use in-process memory and asyncio locks. Multi-replica cloud deployments require Redis for distributed locking and rate limiting.
2. **Static-Only Mobile Inspection**: APK packages and mobile metadata are analyzed statically. Ephemeral sandbox detonation (e.g. Firecracker microVMs) is planned for dynamic runtime behavioral inspection.
3. **URL Crawling Boundaries**: Threat URLs are analyzed structurally and against intelligence feeds without loading active malicious JavaScript. Headless browser sandboxing (Playwright) is planned for screenshot capture and DOM scraping.
4. **External Feed Rate Limits**: Public threat intelligence feeds enforce strict query quotas; enterprise deployments should configure dedicated private threat intelligence feeds or commercial API keys.

---

## 12. Engineering Documentation Index

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Deep-dive system architecture, layers, and concurrency model.
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md): Complete reference of all 46 API endpoints, parameters, and schemas.
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md): Complete database schema for all 18 entities, types, constraints, and relationships.
- [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md): STRIDE threat matrix, attack surfaces, and defensive mitigations.
- [docs/ML_METHODOLOGY.md](docs/ML_METHODOLOGY.md): AI/ML threat detection engines, scoring weights, and heuristic algorithms.
- [docs/TESTING.md](docs/TESTING.md): Testing strategy, test execution commands, and verified results.
- [docs/SECURITY.md](docs/SECURITY.md): Comprehensive security hardening guide and unresolved findings risk register.
