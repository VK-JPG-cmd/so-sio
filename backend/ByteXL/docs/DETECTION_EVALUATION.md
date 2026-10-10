# BrandShield AI — Detection Quality Evaluation & Benchmark Report

**Date:** October 10, 2026  
**Evaluation Phase:** Phase 4 — Look-Alike Detection, False-Positive Reduction, and Cross-Module Consistency  
**Evaluator Roles:** Senior Python Engineer, Application Security Engineer, Machine Learning Evaluation Engineer  
**Workspace:** `c:\ByteXL`  
**Execution Environment:** Python 3.11.9 / Pytest 9.1.1 / RapidFuzz / tldextract  

---

## 1. Executive Summary

As part of Phase 4 hardening, the BrandShield AI threat detection pipeline was evaluated using a reproducible, deterministic synthetic benchmarking harness (`scripts/evaluate_detection.py` and `app/evaluation/dataset.py`).

The evaluation tested three core detection engines across **35 labeled synthetic test cases**:
1. **Domain Threat Detection** (`DomainAnalysisService`)
2. **Social Profile Impersonation Detection** (`ProfileAnalysisService`)
3. **App Store Listing Metadata Detection** (`AppMetadataAnalysisService`)

### Aggregate Pipeline Benchmark Results

| Metric | Result | Target Benchmark | Status |
|:---|:---:|:---:|:---:|
| **Overall Precision** | **100.00%** | $\ge 90.00\%$ | EXCEEDED |
| **Overall Recall** | **100.00%** | $\ge 90.00\%$ | EXCEEDED |
| **Overall F1 Score** | **100.00%** | $\ge 90.00\%$ | EXCEEDED |
| **False Positive Rate (FPR)** | **0.00%** | $\le 5.00\%$ | EXCEEDED |
| **Overall Accuracy** | **100.00%** | $\ge 95.00\%$ | EXCEEDED |

---

## 2. Evaluation Methodology & Ground Truth Definitions

### Evaluation Protocol
- **Deterministic Fixtures**: All candidates were evaluated against verified reference profile `AcmePay` (official domain `acmepay.example`, official handle `@acmepay`, official app `com.acmepay.wallet` published by `AcmePay Technologies`).
- **Binary Classification Policy**:
  - `Positive (Malicious)`: Candidate exhibits brand impersonation, typosquatting, credential harvesting lures, publisher mismatches, homoglyph spoofing, or compromised asset signals with `risk_score >= 25.0` (MEDIUM, HIGH, or CRITICAL severity).
  - `Negative (Benign)`: Candidate is either an authenticated, legitimate official brand asset (`is_official == True` with `risk_score == 0.0`) or an unrelated legitimate entity exhibiting no technical brand exploitation.
- **Safety & Ethical Invariant**: No real personal data or live social media scrapers were used. Synthetic labels were authored deterministically to measure boundary conditions.

---

## 3. Module-by-Module Evaluation Results

### A. Domain Threat Detection (`DomainAnalysisService`)

- **Sample Size**: 12 labeled domains
- **Test Categories**:
  - Legitimate Official (`acmepay.example`)
  - Legitimate Unrelated (`nature-photography-blog.com`, `classic-auto-repair.org`, `baking-bread-recipes.net`, `global-shipping-track.com`)
  - Lookalike Typo (`acmepaay.com`, `acmepya.com`)
  - Brand Modifier Lures (`acmepay-login-support.com`, `acmepay-secure-wallet.net`, `verify-acmepay.xyz`)
  - Unicode Homoglyphs (`аcmеpаy.com` using Cyrillic lookalikes)
  - Threat Intel IOC (`malicious-phish-kit.com`)

#### Domain Confusion Matrix

```
                 Actual Positive    Actual Negative
Pred. Positive         7 (TP)             0 (FP)
Pred. Negative         0 (FN)             5 (TN)
```

- **Precision**: 100.00%
- **Recall**: 100.00%
- **F1 Score**: 100.00%
- **False Positive Rate (FPR)**: 0.00%
- **Key Observation**: PSL-aware extraction using `tldextract` with second-level domain (SLD) fallbacks for test TLDs (`.example`) eliminated correlation floors, preventing unrelated domains from matching `AcmePay`.

---

### B. Social Profile Impersonation Detection (`ProfileAnalysisService`)

- **Sample Size**: 12 labeled profiles
- **Test Categories**:
  - Legitimate Official (`@acmepay` with official domain link)
  - Legitimate Official with Missing Link (`@acmepay` with empty links)
  - Legitimate Unrelated (`@nature_photography_2026`, `@classic_cars_daily`, `@baking_bread_today`)
  - Lookalike Typo (`@acmepayy`, `@acme_pay`, `@acmepya`)
  - Modifier + Bio Support Claim (`@acmepay_support` linking to `http://acmepay-helpdesk.top`)
  - Unicode Homoglyphs (`@АсmеPау` with Cyrillic characters)
  - Reused Logo Avatar (`@acmepay_alerts` with brand logo perceptual hash)
  - Compromised Official Handle (`@acmepay` linking off-domain to `http://attacker-c2-redirect.net`)

#### Social Profile Confusion Matrix

```
                 Actual Positive    Actual Negative
Pred. Positive         7 (TP)             0 (FP)
Pred. Negative         0 (FN)             5 (TN)
```

- **Precision**: 100.00%
- **Recall**: 100.00%
- **F1 Score**: 100.00%
- **False Positive Rate (FPR)**: 0.00%
- **Key Observation**: Preserved official account exemptions while ensuring compromised official accounts linking to external attacker infrastructure are penalized (+25.0 points) rather than granted blind immunity.

---

### C. App Store Listing Metadata Detection (`AppMetadataAnalysisService`)

- **Sample Size**: 11 labeled mobile app listings
- **Test Categories**:
  - Legitimate Official (`AcmePay Wallet`, `com.acmepay.wallet`, `AcmePay Technologies`)
  - Legitimate Unrelated (`Zen Meditation Timer`, `com.zenstudios.meditation`, `Zen Studios`)
  - Legitimate Unrelated with Common Keyword (`Crypto Secure Notes`, `com.secnotes.notes`, `NoteLabs`)
  - Legitimate Unrelated Missing Data (`Classic Radio Streamer`, missing publisher/desc)
  - Similar Name + Package Lookalike (`AcmePay Secure Wallet`, `com.acmepay.wallet.scam`)
  - Package Typosquatting (`AcmePay Wallet`, `com.acmepayy.wallet`)
  - Homoglyph Name (`АсmеPау Wallet`, `com.payment.fakeacmepay`)
  - Publisher Mismatch on Official Package (`AcmePay Wallet`, `com.acmepay.wallet`, `Unauthorized Rogue Publisher`)
  - Credential Harvesting Description (`AcmePay Quick Pay`, soliciting passwords/seed phrases)
  - Platform Store URL Host Mismatch (`AcmePay Client`, declared Android but linking to Apple App Store)
  - Unauthorized Logo Reuse (`AcmePay Assistant`, matching registered logo perceptual hash)

#### App Metadata Confusion Matrix

```
                 Actual Positive    Actual Negative
Pred. Positive         7 (TP)             0 (FP)
Pred. Negative         0 (FN)             4 (TN)
```

- **Precision**: 100.00%
- **Recall**: 100.00%
- **F1 Score**: 100.00%
- **False Positive Rate (FPR)**: 0.00%
- **Key Observation**: Boundary-aware package component tokenization stripped generic `com.` prefixes, ensuring unrelated applications are never correlated with brands based merely on shared package namespaces.

---

## 4. Overall Pipeline Confusion Matrix

```
===================================================================
                      Actual Positive (21)   Actual Negative (14)
Pred. Positive (21)          21 (TP)                 0 (FP)
Pred. Negative (14)           0 (FN)                14 (TN)
===================================================================
```

- **Total Evaluated Samples**: 35
- **Accuracy**: $100.00\%$
- **Precision**: $100.00\%$
- **Recall**: $100.00\%$
- **F1 Score**: $100.00\%$
- **False Positive Rate**: $0.00\%$

---

## 5. Architectural Improvements in Phase 4

1. **Standardized Normalization (`app/core/normalization.py`)**:
   - Centralized NFKC Unicode normalization, whitespace collapsing, and case standardization.
   - Platform-aware handle extraction (supporting Twitter/X, Instagram, and LinkedIn profile URLs).
   - Component-aware Android package and iOS bundle identifier parsing.
2. **Unified Look-Alike & String Similarity Service (`app/services/detection/similarity.py`)**:
   - Eliminated artificial similarity floors caused by unconstrained `fuzz.partial_ratio`.
   - Introduced boundary-aware token matching distinguishing brand modifiers from unrelated words.
   - Built component-by-component Android package comparison ignoring generic `com.` namespace prefixes.
3. **Official Asset Compromise Defense**:
   - Detection engines audit verified assets for independent suspicious signals (off-domain redirect links, credential lures, store URL platform mismatches, active threat feed IOC matches).
   - Official status does not mask potential account or domain compromises.

---

## 6. Known Limitations

1. **Synthetic Dataset Size**: The benchmark consists of 35 curated fixtures. While covering critical boundary cases (typos, homoglyphs, modifiers, missing data, unrelated apps), it does not represent real-world attack distribution or operational volume.
2. **No Live Crawling**: Evaluation relies on submitted metadata payloads. Live app store scraping and social media platform monitoring are not configured.
3. **Static Analysis Only**: Binary mobile app evaluation is strictly static (Androguard); dynamic detonation in sandboxes is not performed.
