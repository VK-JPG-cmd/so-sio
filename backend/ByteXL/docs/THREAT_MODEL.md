# BrandShield AI — Threat Model & Security Posture (STRIDE Analysis)

## 1. Scope & Primary Assets

BrandShield AI protects high-value brand equity and consumers against digital threats while processing untrusted external inputs. The primary assets protected include:

1. **User Identity & Cryptographic Secrets**: Passwords, OTP verification salts, JWT signing keys (`JWT_SECRET_KEY`), and active refresh tokens.
2. **Brand Ownership Assertions**: Legitimate associations between real-world brand entities and their authorized controllers.
3. **Audit Trail Integrity**: Administrative and forensic activity records tracking verification, moderation, and incident investigation.
4. **Threat Intelligence Graph**: Correlated attacker infrastructure, campaign memberships, and reporter evidence artifacts.
5. **Operational Availability**: API resilience against distributed volumetric DoS, zip bombs, and slow-read exhaustion attacks.

---

## 2. Trust Boundaries & Threat Actors

```
[ External Untrusted Internet ]
              │
    Boundary 1: TLS 1.3 / Reverse Proxy / Rate Limiting Gateway
              ▼
[ Application Process & Memory Space (FastAPI) ]
              │
    Boundary 2: Authentication & Role Verification (RBAC / JTI Blacklist)
              ▼
[ Internal Service & Worker Boundary (In-Memory Sandbox) ]
              │
    Boundary 3: Localhost-Only Persistence (127.0.0.1 / PostgreSQL 16)
              ▼
[ Database Storage & File Attachments Volume ]
```

### Threat Actors
- **External Phishing / Scammer Operator**: Seeks to bypass domain checks, inject false evidence, harvest victim credentials, or exhaust server resources using zip bombs.
- **Malicious Consumer / Competitor**: Attempts to submit fraudulent brand applications, tamper with competitor reviews, or enumerate private threat reports.
- **Compromised Brand Owner**: Attempts privilege escalation to modify other brands' assets or access competitor alerts (Cross-Tenant IDOR).
- **Network Attacker / Man-in-the-Middle**: Seeks to intercept unencrypted traffic or forge tokens.

---

## 3. STRIDE Threat Analysis Matrix

| Threat Category | Potential Attack Vectors | Technical Defenses & Hardening Mitigations | Status |
|---|---|---|---|
| **Spoofing (Identity)** | • Forged JWT tokens<br>• Brute-force OTP verification<br>• Brand domain ownership spoofing<br>• Refresh token reuse | • HS256 HMAC cryptographic signing with minimum 32-character key validation on startup.<br>• Constant-time HMAC comparison (`hmac.compare_digest`).<br>• Maximum 5 OTP attempts with immediate DB commits surviving rollbacks.<br>• Authoritative DNS TXT challenge tokens tied to random salts.<br>• Single-use refresh token rotation; token reuse revokes entire family. | **Mitigated** |
| **Tampering (Integrity)** | • Tampering with audit logs<br>• Path traversal in uploaded files<br>• Archive zip bombs<br>• Modifying approved brand verification status | • Database-level SQLAlchemy event listeners (`before_update`, `before_delete`) block all modifications or deletions on `audit_logs`.<br>• Filename sanitization stripping directory traversal (`..`, `/`, `\`).<br>• Pre-flight archive checks enforce max 100MB single entry, 250MB total, and 100:1 maximum decompression ratio.<br>• Brand metadata PATCH endpoint strictly rejects direct edits to `verification_status`. | **Mitigated** |
| **Repudiation** | • Denying brand verification approvals<br>• Denying review moderation decisions<br>• Denying alert incident investigations | • Immutable `audit_logs` record actor UUID, brand ID, action category, entity identifier, and complete JSON state diffs.<br>• Comprehensive timestamps with UTC timezone enforcement. | **Mitigated** |
| **Information Disclosure** | • Cloud metadata leakage via SSRF<br>• Leaking secrets or tokens in logs<br>• Exposing internal stack traces<br>• Cross-tenant data leakage | • Multi-layer SSRF validator blocks AWS/GCP/Alibaba metadata (`169.254.169.254`, `100.100.100.200`, `fd00:ec2::254`, `instance-data`), RFC1918 private IPs, decimal/hex IP encodings, and `.internal`/`.local` suffixes.<br>• Custom `RedactionFilter` scrubs Bearer tokens, JWTs, OTPs, passwords, DB URLs, and phone numbers from logs.<br>• Centralized exception handlers catch domain errors, returning sanitized JSON without tracebacks.<br>• Strict brand-scoped queries and user ownership checks. | **Mitigated** |
| **Denial of Service** | • Large APK streaming uploads<br>• OTP endpoint flooding<br>• Wildcard `%` SQL table scan DoS<br>• Excessive unbounded pagination | • Streaming chunk reader limits APK uploads strictly to 50 MB, terminating immediately upon breach.<br>• In-memory sliding-window rate limiters guard OTP generation and verification.<br>• Helper `escape_like_wildcards` escapes `%`, `_`, and `\` in keyword search queries.<br>• Pagination limits enforce maximum 100 items per request. | **Mitigated** |
| **Elevation of Privilege** | • Customer accessing brand owner dashboard<br>• Brand Owner A accessing Brand Owner B's resources<br>• Viewing other users' background analysis jobs (IDOR) | • Fast, server-enforced role dependencies (`require_admin`, `require_brand_owner`, `require_customer`).<br>• `verify_brand_ownership` dependency validates brand context against caller UUID before executing owner actions.<br>• `AnalysisJobRecord` validates `creator_user_id` against caller before returning job details. | **Mitigated** |

---

## 4. Residual Risks & Security Notes

> [!NOTE]
> **Operational Considerations**:
> - **In-Memory Cache in Multi-Instance Deployments**: Token revocation and sliding-window rate limits currently reside in process memory. In a distributed multi-pod environment, back the revocation store and rate limiter with a shared Redis cluster.
> - **Continuous Patching**: Operating system packages, Python libraries, and container base images must be continuously scanned using tools such as Dependabot, Trivy, or Snyk.
> - **Independent Testing**: Perform periodic third-party penetration testing and threat model reassessments before exposing public production workloads.
