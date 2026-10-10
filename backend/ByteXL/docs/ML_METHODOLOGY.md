# BrandShield AI — Threat Detection & Machine Learning Methodology

## 1. Overview & Detection Pipeline

BrandShield AI employs a hybrid threat detection architecture combining deterministic cryptographic heuristics, lexical pattern analysis, statistical machine learning, and static binary inspection across five distinct attack surfaces:

```
[ Input Threat Surface ]
    ├── Target Domain: Lexical Typosquatting & Homoglyphs
    ├── Target URL: Structural Path, Credential Harvesters & SSRF Shields
    ├── Scam Text: TF-IDF Statistical Classifier & Urgency Heuristics
    ├── Social Profile / Avatar: Perceptual Image Hashing (pHash / dHash)
    └── Android APK Package: Static Manifest & Permission Risk Inspection
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ Unified Risk Scoring & Explainability Engine (v1.0.0) │
│  - Evaluates Detected Threat Signals                   │
│  - Applies Category Caps & Weight Enforcements        │
│  - Handles Missing Signals without Penalizing Scores   │
│  - Maps Actionable Defensive Recommendations           │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
           [ Composite Risk Report ]
     Score: 0.0 – 100.0 | Severity: LOW/MED/HIGH/CRIT
```

---

## 2. Detection Methodologies by Threat Vector

### 2.1. Domain Name Analysis & Typosquatting
- **Homoglyph & Confusable Character Mapping**: Internationalized Domain Names (IDNs) and Cyrillic/Greek lookalikes (e.g., `а` [U+0430] vs `a` [U+0061]) are mapped to ASCII canonical equivalents.
- **Lexical Similarity Scoring**: RapidFuzz ratio, partial ratio, and token sort ratio evaluate the similarity between the target hostname and registered brand profiles.
- **Typosquatting Strategies Detected**:
  - Omission (e.g., `brand` → `brnd`)
  - Transposition (e.g., `brand` → `barnd`)
  - Replacement (adjacent keyboard characters)
  - Addition (e.g., `brand-login`, `brand-verify`)
  - TLD Swapping (e.g., `.com` → `.co`, `.cm`, `.org`)

### 2.2. URL Threat & Structural Analysis
- **SSRF Defenses & Safe Inspection**: URLs are inspected strictly offline by default; outbound requests are prohibited in the main API process. Safe fetching (`safe_fetch_url`) is isolated with strict redirect caps, bounded streaming reads, and destination IP re-verification.
- **Credential Harvesting Indicators**: Inspects query parameters for credential lure keys (`token`, `auth`, `pass`, `password`, `login`, `redirect_uri`).
- **Suspicious Path Patterns**: Flags high-risk path segments (`wp-login.php`, `banking`, `wallet`, `cpanel`, `recovery`, `session`).

### 2.3. Scam Text Classification (Statistical ML)
- **Feature Extraction**: Text is tokenized using a sub-linear TF-IDF vectorizer (`TfidfVectorizer(ngram_range=(1, 2), max_features=5000)`).
- **Classification Engine**: A calibrated Linear SGD/Logistic Regression classifier trained on synthetic and curated financial lure, lottery, urgent verification, and imposter message corpora.
- **Heuristic Urgency Boosters**: Emits explicit signal bonuses if high-urgency keywords (`urgent`, `action required`, `account suspended`, `click here immediately`, `wire transfer`) are present in short-horizon messages.

### 2.4. Perceptual Image & Logo Impersonation
- **Dual Perceptual Hashing**: Computes both Difference Hash (dHash) and Perceptual Hash (pHash) on normalized 64x64 grayscale transforms using Pillow and ImageHash.
- **Hamming Distance Matcher**:
  - Distance $\le 5$: Direct visual match (impersonation score: 95%).
  - Distance $\le 10$: High visual lookalike (impersonation score: 75%).
  - Distance $> 15$: Benign or unrelated graphic.

### 2.5. Mobile Application (APK) Static Inspection
- **Non-Executing Static Analysis**: Analyzes Android packages using Androguard without executing untrusted bytecode.
- **Permission Matrix**: Declared permissions are matched against dangerous and signature-level Android permissions (`READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `SYSTEM_ALERT_WINDOW`, `REQUEST_INSTALL_PACKAGES`, `RECORD_AUDIO`, `CAMERA`).
- **Archive Safety**: Pre-flight inspection protects against zip bombs (max 100MB per entry, 250MB total uncompressed, >100:1 ratio detection) and path traversal (`..` inside archive members).

---

## 3. Explainable Risk Scoring Engine

### 3.1. Category Weight Caps & Invariants
To prevent a single noisy heuristic from generating disproportionate false positives, category contributions are strictly bounded:

| Risk Category | Category Cap | Key Trigger Signals |
|---|---|---|
| **Domain Similarity** | 35.0 pts | Exact homoglyph match, high RapidFuzz similarity ($>85\%$), typosquatting. |
| **URL Structure & SSRF**| 25.0 pts | SSRF to loopback/metadata, suspicious path indicators, credential query params. |
| **Scam Text Patterns** | 25.0 pts | ML scam probability $>0.75$, urgency keywords, financial lure language. |
| **Visual Impersonation**| 25.0 pts | Perceptual logo similarity (Hamming distance $\le 8$). |
| **APK Binary Risks** | 35.0 pts | Missing certificate signature, excessive sensitive permissions, package name spoofing. |

### 3.2. Missing Signal Invariant
If a threat report only contains a domain and has no attached APK or logo graphic:
- Unavailable signal categories are documented explicitly in `explanation_json["unavailable_signals"]`.
- The engine does **not** penalize the overall risk score or reduce confidence due to missing modalities.

### 3.3. Severity Thresholds
$$\text{Composite Score} = \min\left(100.0, \sum \min(\text{score}_{\text{cat}}, \text{cap}_{\text{cat}})\right)$$

| Score Range | Severity Level | Recommended Action |
|---|---|---|
| **0.0 – 29.9** | `LOW` | Log event; standard continuous passive monitoring. |
| **30.0 – 59.9** | `MEDIUM` | Flag for review; request automated follow-up telemetry. |
| **60.0 – 84.9** | `HIGH` | Escalate to SOC queue; notify authorized brand owner. |
| **85.0 – 100.0** | `CRITICAL` | Trigger immediate alert; recommend registrar abuse takedown review. |

---

## 4. Limitations & Edge Cases

1. **Static APK Analysis Limits**: Obfuscated bytecode, packed Dalvik executables (e.g., DexGuard), or dynamic payloads downloaded at runtime cannot be fully inspected by static parsing alone.
2. **Offline URL Limitations**: Because the API avoids outbound visits to untrusted hosts during ingestion, dynamic DOM changes, cloaking, and JavaScript-based evasions require external crawler sandboxes.
3. **ML Classifier Boundaries**: Statistical text classification relies on training distribution vocabulary; highly novel zero-day phrasing or non-English scam scripts may require supplementary rule updates.
