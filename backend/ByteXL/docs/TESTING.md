# BrandShield AI — Testing Strategy & Execution Guide

## 1. Testing Philosophy & Architecture

BrandShield AI maintains high test coverage across unit, integration, security hardening, and end-to-end suites. All tests operate under strict isolation invariants:
- **Zero Live Malicious Traffic**: Tests never visit, crawl, or download payloads from live malicious websites.
- **Deterministic Mocking**: External services (SMS OTP gateways, authoritative DNS TXT resolution) use isolated, thread-safe in-memory stores (`MockOTPProvider`, `MockDNSResolver`).
- **Transactional Database Isolation**: Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) configured with `StaticPool` and automatic schema creation/teardown per test function.
- **Fast Feedback**: The entire 151-test suite executes in under 50 seconds on standard developer machines.

---

## 2. Test Suite Organization

```
tests/
├── conftest.py                             # Async engine, session fixtures, mock providers
├── unit/                                   # Isolated unit test suites (No HTTP / API overhead)
│   ├── test_campaign_correlation.py        # Entity clustering & disambiguation algorithms
│   ├── test_config.py                      # Pydantic settings parsing & production validation
│   ├── test_domain.py                      # Domain normalization & FQDN validation
│   ├── test_domain_and_url_analysis.py     # SSRF shields, homoglyph mapping, URL parsing
│   ├── test_exceptions.py                  # Domain exception hierarchy mapping
│   ├── test_file_security.py               # Magic byte inspection & anti-traversal
│   ├── test_image_and_apk_analysis.py      # Perceptual image hashing & Androguard static logic
│   ├── test_risk_scoring_engine.py         # Category weight caps, missing signals, score bounds
│   └── test_scam_text_classifier.py        # TF-IDF statistical classification & urgency rules
│
└── integration/                            # API & database integration test suites
    ├── test_auth_otp.py                    # Phone OTP authentication, rate limiting, timing
    ├── test_auth_tokens.py                 # Refresh token rotation and JTI logout revocation
    ├── test_brand_applications.py          # Brand registration, DNS challenge, admin review
    ├── test_brands_and_assets.py           # Brand asset metadata & public discovery
    ├── test_customer_portal_api.py         # Brand discovery, customer reviews, threat intake
    ├── test_e2e_resilience_and_operations.py # Migrations, background jobs, deduplication, RBAC
    ├── test_e2e_workflows.py               # Complete Workflows A, B, and C end-to-end
    ├── test_health.py                      # Liveness probe endpoint
    ├── test_owner_portal_api.py            # Owner dashboard aggregation, audit logs, alerts
    ├── test_owner_threats_and_campaigns_api.py # Campaign listing, alerts, correlation graph
    ├── test_readiness.py                   # Dependency readiness probe with DB ping
    ├── test_reviews_and_threat_reports.py  # Review moderation, threat reports, evidence
    ├── test_risk_assessment_api.py         # Risk scoring API, explainability breakdowns
    ├── test_security_hardening.py          # Phase 10 regression tests (SSRF, zip bomb, IDOR)
    ├── test_startup.py                     # Application startup and lifecycle events
    └── test_users_and_roles.py             # User profile, role enforcement, suspended state
```

---

## 3. How to Run the Tests

### 3.1. Run Entire Test Suite
Activate the Python virtual environment and run pytest:

```bash
# On Windows (PowerShell)
.venv\Scripts\python.exe -m pytest -v

# On Linux / macOS
.venv/bin/python -m pytest -v
```

### 3.2. Run Only Unit Tests
```bash
.venv\Scripts\python.exe -m pytest tests/unit -v
```

### 3.3. Run Only End-to-End Workflow Tests
```bash
.venv\Scripts\python.exe -m pytest tests/integration/test_e2e_workflows.py tests/integration/test_e2e_resilience_and_operations.py -v
```

### 3.4. Run with Test Summary & Durations
```bash
.venv\Scripts\python.exe -m pytest --durations=10
```

---

## 4. Actual Verified Test Results

The full test suite was executed against the repository:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\ByteXL
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO
collected 151 items

tests\integration\test_auth_otp.py .........                             [  5%]
tests\integration\test_auth_tokens.py ..                                 [  7%]
tests\integration\test_brand_applications.py .........                   [ 13%]
tests\integration\test_brands_and_assets.py ..                           [ 14%]
tests\integration\test_customer_portal_api.py ........                   [ 19%]
tests\integration\test_e2e_resilience_and_operations.py .......          [ 24%]
tests\integration\test_e2e_workflows.py ...                              [ 26%]
tests\integration\test_health.py .                                       [ 27%]
tests\integration\test_owner_portal_api.py ......                        [ 31%]
tests\integration\test_owner_threats_and_campaigns_api.py ...            [ 33%]
tests\integration\test_readiness.py ...                                  [ 35%]
tests\integration\test_reviews_and_threat_reports.py .............       [ 43%]
tests\integration\test_risk_assessment_api.py ...                        [ 45%]
tests\integration\test_security_hardening.py ..........                  [ 52%]
tests\integration\test_startup.py ..                                     [ 53%]
tests\integration\test_threat_detection_api.py .......                   [ 58%]
tests\integration\test_users_and_roles.py .......                        [ 62%]
tests\unit\test_campaign_correlation.py .......                          [ 67%]
tests\unit\test_config.py ......                                         [ 71%]
tests\unit\test_domain.py ..                                             [ 72%]
tests\unit\test_domain_and_url_analysis.py .........                     [ 78%]
tests\unit\test_exceptions.py ....                                       [ 81%]
tests\unit\test_file_security.py .......                                 [ 86%]
tests\unit\test_image_and_apk_analysis.py ........                       [ 91%]
tests\unit\test_risk_scoring_engine.py .........                         [ 97%]
tests\unit\test_scam_text_classifier.py ....                             [100%]

====================== 151 passed, 7 warnings in 49.04s =======================
```

- **Total Tests**: `151`
- **Passed**: `151`
- **Failed**: `0`
- **Skipped**: `0`
