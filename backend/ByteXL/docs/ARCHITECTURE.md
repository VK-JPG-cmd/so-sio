# BrandShield AI — System Architecture & Design Specification

## 1. System Overview

BrandShield AI is an AI-powered Digital Risk Protection (DRP) backend engineered to defend organizations, brand owners, and consumers against brand impersonation, fraudulent domains, visual typosquatting, credential harvesting, social scam campaigns, and malicious mobile application packages (APKs).

The platform provides an authoritative, modular architecture structured around high-assurance security principles: passwordless cryptographic authentication, authoritative DNS domain ownership verification, multi-surface threat detection, explainable risk scoring, entity relationship correlation, immutable administrative audit trails, and tenant-isolated customer/owner portals.

---

## 2. Architectural Topology

```
                                  [ Client Layer ]
              (Web Frontends / SOC Analyst Consoles / Consumer Mobile Apps)
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
│  ├── API Layer (/api/v1)                                                              │
│  │    ├── Auth & Session Management (/auth)                                           │
│  │    ├── User Identity & Profiles (/users)                                           │
│  │    ├── Brand Registration & Verification (/brand-applications)                     │
│  │    ├── Public Brand Discovery & Customer Reviews (/brands, /reviews)               │
│  │    ├── Threat Intake & Evidence Attachments (/threat-reports)                      │
│  │    ├── Detection Engines & Async Workflows (/analyze)                              │
│  │    ├── Brand Owner Operations & Graph Portal (/owner)                              │
│  │    ├── Platform Administration (/admin)                                            │
│  │    └── Health & Readiness Probes (/health, /ready)                                 │
│  │                                                                                    │
│  ├── Core & Cross-Cutting Layer                                                       │
│  │    ├── Security: JWT (HS256), Salted SHA256, JTI Blacklist Revocation              │
│  │    ├── Rate Limiter: In-Memory Sliding-Window Middleware                           │
│  │    ├── Redaction Filter: Secret, PII, and Token Log Sanitization                   │
│  │    ├── File Security: Strict Magic Byte & Anti-Traversal Storage                   │
│  │    └── Canonical Domain Normalization (RFC1035 / FQDN)                             │
│  │                                                                                    │
│  ├── Detection & Scoring Engines (In-Memory / Async Worker Sandbox)                   │
│  │    ├── Domain & URL Analyzer (SSRF Shields, Homoglyph Mapping, Typo-Squatting)     │
│  │    ├── Scam Text Classifier (TF-IDF + Linear SGD / Logistic Model)                 │
│  │    ├── Visual Impersonation Engine (Perceptual pHash / dHash)                      │
│  │    ├── APK Static Inspector (Androguard, Manifest Parsing, Zip Bomb Guards)        │
│  │    ├── Unified Risk Scoring Engine (Configurable Category Caps & Weights)          │
│  │    └── Campaign Correlation Engine (Entity Disambiguation & Clustering)           │
│  │                                                                                    │
│  └── Persistence & Data Access Layer (SQLAlchemy 2.0 Async)                           │
│       ├── Domain ORM Models (UUID PKs, Enums, Strict Foreign Keys)                    │
│       ├── Repositories (Parameterized Queries, LIKE Wildcard Escaping)                │
│       └── Immutable Audit Log Event Listeners                                         │
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

## 3. Layered Design & Separation of Concerns

The repository strictly adheres to a clean separation of concerns:

1. **Presentation & Routing Layer (`app/api/v1/`)**:
   - Manages HTTP status codes, routing, header parsing, request validation, and OpenAPI documentation.
   - Enforces authentication and authorization dependencies (`get_current_active_user`, `require_brand_owner`, `require_admin`).
   - Pure handlers that delegate all business logic to service instances.

2. **Domain Service Layer (`app/services/`)**:
   - Encapsulates business rules, state machines, workflow transitions, and external adapter invocations.
   - Manages domain operations: `AuthService`, `BrandService`, `ReviewService`, `ThreatReportService`, `RiskAssessmentService`, `OwnerPortalService`, `CampaignCorrelationService`.

3. **Detection & AI Analytics Layer (`app/services/detection/` & `app/services/scoring/`)**:
   - Performs deterministic heuristics and statistical pattern classification.
   - Operates with strict execution timeouts and memory quotas.
   - Implements safe, offline URL inspection without triggering outbound malicious payload requests.

4. **Data Access & Repository Layer (`app/repositories/`)**:
   - Encapsulates all SQLAlchemy queries, pagination offset/limits, and database operations.
   - Escapes SQL LIKE wildcards (`escape_like_wildcards`) and parameterizes queries to prevent SQL injection.

5. **Persistence & Migration Layer (`app/models/` & `alembic/`)**:
   - SQLAlchemy DeclarativeBase models defining tables, relationships, and constraints.
   - Version-controlled Alembic migrations providing repeatable zero-downtime schema evolution.

6. **Cross-Cutting Core Layer (`app/core/`)**:
   - Environment configuration with validation on boot (`config.py`).
   - Logging redaction filters scrubbing tokens, passwords, and phone numbers (`logging.py`).
   - Rate limiting sliding-window counters (`rate_limit.py`).
   - File integrity validation and anti-traversal safety (`file_security.py`).

---

## 4. Asynchronous Workflows & Concurrency Model

```
[ User Request: Upload APK ]
              │
              ▼
   FastAPI Route (/analyze/apk)
              │
       Validate File Size (<=50MB) & Sanitize Filename
              │
       Register Job: AnalysisJobRecord (Status: PENDING)
              │
       Spawn Background Task: asyncio.create_task(...)
              │
              ├───────────────────────────────────┐
              ▼                                   ▼
   Return HTTP 202 Accepted              Execute Worker in ThreadPool
   {"job_id": "...", "status": "PENDING"}  (APK Static Analysis)
                                                  │
                                         Inspect Zip Archive & Manifest
                                                  │
                                         Update Job: Status = COMPLETED
                                                  │
                                                  ▼
                                      Available for Client Polling
                                      GET /api/v1/analyze/jobs/{job_id}
```

- **Thread-Safe In-Memory Job Tracker**: `JobTrackerService` manages long-running static analysis workloads. Analysis jobs track `creator_user_id` to eliminate Insecure Direct Object References (IDOR).
- **Non-Blocking IO**: All database interactions use non-blocking asynchronous drivers (`asyncpg`, `aiosqlite`) managed via async session contexts.

---

## 5. Deployment Topology

For local development and hackathon demonstrations, the system runs with two containers:
1. **`api` Service**: FastAPI backend, runs `alembic upgrade head` on startup before launching Uvicorn ASGI server on port `8000`.
2. **`db` Service**: PostgreSQL 16 Alpine container, bound strictly to `127.0.0.1:5432`, backed by persistent Docker named volume `postgres_data`.
