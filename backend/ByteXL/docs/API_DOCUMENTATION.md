# BrandShield AI — API Documentation Reference

## Overview
BrandShield AI exposes a RESTful HTTP/JSON API under the `/api/v1` namespace.

- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive OpenAPI Documentation (Swagger UI)**: `http://localhost:8000/docs` *(Enabled in non-production environments)*
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI JSON Specification**: `http://localhost:8000/openapi.json`

---

## Standard Headers & Authentication

### Authentication Header
Protected endpoints require a standard Bearer access token issued via the OTP verification endpoint:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### Standard Response Envelope
Successful responses return serialized JSON data. Paginated responses additionally emit standard headers:
- `X-Total-Count`: Total number of records matching query criteria.
- `X-Page`: Current page number (1-indexed).
- `X-Page-Size`: Maximum number of records per page.

### Standard Error Response Format
All application and client errors return a structured JSON response:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description of the error.",
    "details": { "field": "reason" },
    "request_id": "req-12345678"
  }
}
```

---

## 1. Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `POST` | `/api/v1/auth/otp/start` | Public (Rate Limited) | Initiates passwordless OTP authentication for a phone number. |
| `POST` | `/api/v1/auth/otp/verify` | Public (Rate Limited) | Verifies 6-digit OTP code, returns access and refresh tokens. |
| `POST` | `/api/v1/auth/refresh` | Public | Rotates single-use refresh token and issues a new token pair. |
| `POST` | `/api/v1/auth/logout` | Authenticated | Revokes the user refresh token and blacklists active access token JTI. |

#### Example: `POST /api/v1/auth/otp/start`
**Request:**
```json
{
  "phone_number": "+14155551234"
}
```
**Response (200 OK):**
```json
{
  "message": "OTP verification code sent successfully.",
  "phone_number": "+14155551234",
  "expires_in_seconds": 300
}
```

#### Example: `POST /api/v1/auth/otp/verify`
**Request:**
```json
{
  "phone_number": "+14155551234",
  "code": "123456"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "phone_number": "+14155551234",
    "role": "CUSTOMER",
    "account_status": "ACTIVE"
  }
}
```

---

## 2. User Profile Endpoints (`/api/v1/users`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | Authenticated | Returns profile of currently authenticated user. |
| `GET` | `/api/v1/users/me/reviews` | Authenticated | Returns paginated list of reviews submitted by caller. |
| `GET` | `/api/v1/users/me/threat-reports` | Authenticated | Returns paginated list of threat reports submitted by caller. |

---

## 3. Brand Applications (`/api/v1/brand-applications`) & Admin (`/api/v1/admin`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `POST` | `/api/v1/brand-applications` | Authenticated | Submits new official brand registration application. |
| `GET` | `/api/v1/brand-applications/me` | Authenticated | Returns brand applications created by caller. |
| `POST` | `/api/v1/brand-applications/{id}/domain-challenge` | Brand Owner | Generates unique DNS TXT challenge token and verification host. |
| `POST` | `/api/v1/brand-applications/{id}/verify-domain` | Brand Owner | Resolves live/mock DNS TXT records to confirm domain ownership. |
| `POST` | `/api/v1/admin/brand-applications/{id}/review` | Admin Only | Administratively approves or rejects application, creating verified brand. |

#### Example: `POST /api/v1/brand-applications/{id}/domain-challenge`
**Response (200 OK):**
```json
{
  "application_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "record_type": "TXT",
  "record_host": "_brandshield-challenge.example.com",
  "expected_record_value": "brandshield-verification=7b2c9a...",
  "challenge_token": "7b2c9a...",
  "expires_at": "2026-10-11T12:00:00Z"
}
```

---

## 4. Public Brands & Reviews (`/api/v1/brands`, `/api/v1/reviews`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `GET` | `/api/v1/brands` | Public | Discovers verified brands with search keyword and pagination. |
| `GET` | `/api/v1/brands/{id}` | Public | Retrieves public brand metadata, assets, and published reviews. |
| `POST` | `/api/v1/brands/{id}/reviews` | Customer | Submits customer review and rating (1–5 stars) for brand. |
| `PATCH` | `/api/v1/reviews/{id}` | Admin Only | Moderates customer review (transitions to `PUBLISHED` or `REJECTED`). |

---

## 5. Threat Reports & Evidence (`/api/v1/threat-reports`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `POST` | `/api/v1/threat-reports` | Authenticated | Submits report on suspicious domain, URL, scam text, or profile. |
| `GET` | `/api/v1/threat-reports/{id}` | Submitter / Admin | Retrieves threat report details and status. |
| `PATCH` | `/api/v1/threat-reports/{id}` | Admin Only | Transitions threat report status across investigation lifecycle. |
| `POST` | `/api/v1/threat-reports/{id}/evidence` | Submitter / Admin | Uploads supporting artifact (screenshot, header, log, document). |
| `GET` | `/api/v1/threat-reports/{id}/evidence/{evidence_id}` | Submitter / Admin | Securely downloads evidence file with safety headers. |
| `POST` | `/api/v1/threat-reports/{id}/analyze` | Submitter / Admin | Executes unified AI threat scoring and updates report status. |
| `GET` | `/api/v1/threat-reports/{id}/assessment` | Submitter / Admin | Retrieves persisted explainable risk assessment report. |

#### Example: `POST /api/v1/threat-reports`
**Request:**
```json
{
  "brand_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "target_type": "DOMAIN",
  "target_value": "example-login-verify.com",
  "description": "Suspicious domain mimicking legitimate brand portal for credential theft."
}
```
**Response (201 Created):**
```json
{
  "id": "8f3b2a1c-...",
  "target_type": "DOMAIN",
  "target_value": "example-login-verify.com",
  "status": "SUBMITTED",
  "created_at": "2026-10-10T10:30:00Z"
}
```

---

## 6. Threat Detection & Async Job Inspection (`/api/v1/analyze`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `POST` | `/api/v1/analyze/url` | Authenticated | Synchronous safe offline URL and domain threat analysis. |
| `POST` | `/api/v1/analyze/text` | Authenticated | Evaluates textual message for urgency, scam, and financial lure patterns. |
| `POST` | `/api/v1/analyze/profile` | Authenticated | Inspects social profile handles and avatars for impersonation. |
| `POST` | `/api/v1/analyze/apk` | Authenticated | Submits Android APK package for static analysis (HTTP 202). |
| `GET` | `/api/v1/analyze/jobs/{job_id}` | Submitter / Admin | Tracks status, timing, and results of an async analysis task. |

---

## 7. Brand Owner Portal (`/api/v1/owner`)

*All owner portal endpoints enforce strict brand ownership. Accessing another brand's portal returns HTTP 403 Forbidden.*

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `GET` | `/api/v1/owner/brands/{brand_id}/dashboard` | Brand Owner | Aggregated threat report metrics, severity breakdown, and trends. |
| `GET` | `/api/v1/owner/brands/{brand_id}/threats` | Brand Owner | Filterable, paginated, and sortable list of brand threats. |
| `GET` | `/api/v1/owner/brands/{brand_id}/campaigns` | Brand Owner | Active campaigns clustering related threat entities. |
| `GET` | `/api/v1/owner/brands/{brand_id}/alerts` | Brand Owner | Active incident alerts generated for the brand. |
| `PATCH` | `/api/v1/owner/alerts/{alert_id}` | Brand Owner | Updates alert resolution status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`) and logs audit trail. |
| `GET` | `/api/v1/owner/brands/{brand_id}/graph` | Brand Owner | Interactive correlation graph containing entity nodes and edges. |
| `GET` | `/api/v1/owner/brands/{brand_id}/audit-logs` | Brand Owner | Immutable administrative and security audit trail records. |
| `POST` | `/api/v1/owner/reviews/{review_id}/reply` | Brand Owner | Publishes official brand owner response to a customer review. |
| `PATCH` | `/api/v1/owner/brands/{brand_id}` | Brand Owner | Updates official brand display name and metadata. |
| `POST` | `/api/v1/owner/brands/{brand_id}/assets` | Brand Owner | Uploads and registers official brand logo or asset. |

---

## 8. Health & Diagnostics (`/api/v1/health`, `/api/v1/ready`)

| Method | Endpoint | Access | Summary |
|---|---|---|---|
| `GET` | `/api/v1/health` | Public | Fast process liveness probe confirming ASGI application availability. |
| `GET` | `/api/v1/ready` | Public | Dependency readiness probe pinging PostgreSQL database connection (Returns 200 OK or 503 Service Unavailable). |
