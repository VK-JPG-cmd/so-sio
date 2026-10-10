"""
Central scoring configuration and versioning for BrandShield AI Risk Scoring Engine.
Stores rule versions, category weight caps, severity thresholds, and recommendations.
"""

from typing import Dict, List
from app.models.enums import RiskSeverity

# Scoring rule version tracked in every assessment record
SCORING_RULE_VERSION = "1.0.0-rules-baseline"

# Category weight caps (Total maximum sum = 100.0 points)
# NOTE: These represent initial engineering weights, not calibrated mathematical probabilities.
CATEGORY_WEIGHT_CAPS: Dict[str, float] = {
    "DOMAIN_SIMILARITY": 25.0,
    "VISUAL_SIMILARITY": 25.0,
    "SCAM_AND_CREDENTIAL_HARVESTING": 25.0,
    "THREAT_INTELLIGENCE": 15.0,
    "REDIRECT_AND_INFRASTRUCTURE": 10.0,
}

# Severity classification boundaries (0 to 100)
# - LOW: 0.0 <= score < 30.0
# - MEDIUM: 30.0 <= score < 60.0
# - HIGH: 60.0 <= score < 80.0
# - CRITICAL: 80.0 <= score <= 100.0
SEVERITY_THRESHOLDS = {
    RiskSeverity.CRITICAL: 80.0,
    RiskSeverity.HIGH: 60.0,
    RiskSeverity.MEDIUM: 30.0,
    RiskSeverity.LOW: 0.0,
}

# Standard ethical and mathematical disclaimer
SCORING_METHODOLOGY_DISCLAIMER = (
    "This risk assessment score (0-100) is a deterministic heuristic composite based on "
    "detected indicators across configured signal categories. It does NOT represent a calibrated "
    "probability of fraud or compromise. Missing data or unanalyzed signals are strictly recorded as "
    "unavailable and do NOT increase the risk score. Scores do not constitute automated legal accusations "
    "or proof of malicious intent; human review is required before taking enforcement actions."
)

# Standard recommendations catalog based on risk findings
STANDARD_RECOMMENDATIONS = {
    "VERIFY_DOMAIN_OWNERSHIP": {
        "action": "VERIFY_DOMAIN_OWNERSHIP",
        "title": "Verify Domain Ownership",
        "description": "Cross-reference registrar WHOIS and issue an authoritative DNS TXT ownership challenge to confirm domain legitimacy.",
    },
    "COLLECT_ADDITIONAL_EVIDENCE": {
        "action": "COLLECT_ADDITIONAL_EVIDENCE",
        "title": "Collect Additional Evidence",
        "description": "Gather further artifacts, full headers, server SSL certificates, or user incident reports to strengthen analysis.",
    },
    "ESCALATE_MANUAL_REVIEW": {
        "action": "ESCALATE_MANUAL_REVIEW",
        "title": "Escalate for Manual Review",
        "description": "Refer the threat report to senior brand protection analysts for manual inspection and verification.",
    },
    "MONITOR_REPEATED_IMPERSONATION": {
        "action": "MONITOR_REPEATED_IMPERSONATION",
        "title": "Monitor for Repeated Impersonation",
        "description": "Establish continuous monitoring for recurring name variations, DNS record alterations, or social profile handle shifts.",
    },
    "REQUEST_TAKEDOWN_REVIEW": {
        "action": "REQUEST_TAKEDOWN_REVIEW",
        "title": "Request Takedown Review",
        "description": "Sufficient corroborating evidence detected. Prepare an abuse takedown notice for registrar, hosting provider, or platform abuse desks.",
    },
    "ROUTINE_MONITORING": {
        "action": "ROUTINE_MONITORING",
        "title": "Maintain Routine Monitoring",
        "description": "Risk indicators remain below actionable thresholds. Maintain standard observational monitoring without escalation.",
    },
}
