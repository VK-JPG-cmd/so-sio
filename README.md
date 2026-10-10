# BrandShield AI — Intelligent Digital Risk & Impersonation Protection

BrandShield AI is an enterprise-grade AI-powered Digital Risk Protection (DRP) platform designed with the **"Soft Intelligence"** design system.

---

## 🛡️ Key System Architecture

### 1. Dual-Portal Unified Experience
* **Portal A — Brand Owner Intelligence Workspace**:
  * **Real-time KPI Overview**: Monitored perimeter assets, detected candidates, open registrar takedowns, and trust score.
  * **Threat Intelligence & Investigation Workspace**: Deep search, multi-vector filtering (Typosquatting, Phishing URLs, Social Impersonation, Rogue APKs), visual UI similarity matrix, and AI evidence locker.
  * **Fast-Track Takedowns**: Automated dispatch of abuse notification packages to domain registrars, hosting providers, and social platforms.
  * **Brand Identity & Domain Verification**: DNS TXT record validator, HTML meta tag checker, and asset health monitoring.
  * **Customer Review & Sentiment Response**: Official verified responses to customer community feedback.
  * **Executive Reports**: Board-ready PDF, CSV, and JSON risk briefs.

* **Portal B — Consumer Protection Portal**:
  * **Instant Link & Domain Safety Scanner**: Real-time AI verdict evaluating URLs against verified brand perimeters and typosquat permutations.
  * **Threat & Scam Reporting Wizard**: Step-by-step reporting with evidence file upload, observed scam tactics, and phone-verified priority queuing.
  * **Live Investigation Tracker (My Reports)**: 5-stage milestone progression (*Submitted &rarr; In Triage &rarr; Under Investigation &rarr; Takedown Initiated &rarr; Resolved*).
  * **Verified Brand Directory**: Authentic domain channels, official social handles, and trust ratings.

---

## 🎨 "Soft Intelligence" Design System

* **Primary Lavender**: `#A98BD0`
* **Deep Purple**: `#70539B`
* **Soft Lavender Surface**: `#F1E8FB`
* **Pale Background**: `#FAF7FF`
* **Soft Pink Accent**: `#F2B8E1`
* **Semantic Threat Colors**:
  * **Low**: `#28856A` (Muted Green)
  * **Medium**: `#D58B32` (Amber)
  * **High**: `#C84D62` (Coral Red)
  * **Critical**: `#8A1C2E` (Dark Red)
* **Custom Mascot ("Aegis / Shieldy")**: Expressive 3D-styled cybersecurity mascot with vector SVG lighting, floating states, and interactive reactions.

---

## 🚀 Getting Started

### Development
```bash
npm install
npm run dev
```

### Run Tests
```bash
npm test
```

### Production Build
```bash
npm run build
```

---

## 🔌 FastAPI Backend Integration

Configure your backend URL in `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The frontend includes a **Demo Sandbox Switcher** in the top navigation allowing instantaneous switching between:
* Mock Sandbox Mode (rich realistic telemetry dataset)
* Live FastAPI Backend Endpoints
* One-click Persona Switcher (Brand Owner vs Customer vs Guest)
