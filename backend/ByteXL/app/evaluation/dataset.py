"""
Synthetic Evaluation Dataset for BrandShield AI Detection Pipeline.
Contains labeled test fixtures covering:
- Legitimate official accounts, domains, and applications
- Legitimate unrelated accounts, domains, and applications
- Look-alike names, handles, and package identifiers
- Unicode homoglyph confusables
- Added modifier keywords (support, secure, login, wallet, official)
- Publisher mismatches and credential harvesting lures
- Missing metadata variations
- Compromised official assets with independent malicious indicators

Ground Truth Labels:
- is_malicious: True (Threat / Impersonation / Lure / Compromise)
- is_malicious: False (Legitimate Official or Legitimate Unrelated)
"""

from typing import Any, Dict, List
import uuid
from app.services.detection.brand_intelligence import (
    OfficialMobileAppProfile,
    OfficialSocialAccountProfile,
    VerifiedBrandProfile,
)

# Reference brand for synthetic testing
EVAL_BRAND_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
EVAL_BRAND = VerifiedBrandProfile(
    brand_id=EVAL_BRAND_ID,
    display_name="AcmePay",
    official_domain="acmepay.example",
    known_names=["AcmePay"],
    known_social_handles=["acmepay"],
    approved_keywords=["acmepay", "wallet"],
    logo_storage_keys=["brands/acme/logo.png"],
    logo_hashes=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    official_social_accounts=[
        OfficialSocialAccountProfile(
            id=uuid.UUID("aaaaaaaa-1111-2222-3333-444444444444"),
            platform="Twitter",
            handle="acmepay",
            canonical_url="https://twitter.com/acmepay",
            verification_status="VERIFIED",
            is_verified=True,
        )
    ],
    official_mobile_apps=[
        OfficialMobileAppProfile(
            id=uuid.UUID("bbbbbbbb-1111-2222-3333-444444444444"),
            app_name="AcmePay Wallet",
            platform="ANDROID",
            app_identifier="com.acmepay.wallet",
            publisher_name="AcmePay Technologies",
            store_url="https://play.google.com/store/apps/details?id=com.acmepay.wallet",
            verification_status="VERIFIED",
            is_verified=True,
        )
    ],
)


SYNTHETIC_DOMAINS: List[Dict[str, Any]] = [
    # Legitimate Official
    {
        "id": "DOM-01",
        "domain": "acmepay.example",
        "description": "Exact registered official brand domain",
        "is_malicious": False,
        "category": "LEGITIMATE_OFFICIAL",
    },
    # Legitimate Unrelated
    {
        "id": "DOM-02",
        "domain": "nature-photography-blog.com",
        "description": "Unrelated legitimate nature photography blog",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "DOM-03",
        "domain": "classic-auto-repair.org",
        "description": "Unrelated legitimate auto repair business",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "DOM-04",
        "domain": "baking-bread-recipes.net",
        "description": "Unrelated legitimate culinary recipes website",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "DOM-05",
        "domain": "global-shipping-track.com",
        "description": "Unrelated legitimate logistics portal",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    # Look-Alikes: Typo / Mutations
    {
        "id": "DOM-06",
        "domain": "acmepaay.com",
        "description": "Extra character insertion typosquatting domain",
        "is_malicious": True,
        "category": "LOOKALIKE_MUTATION",
    },
    {
        "id": "DOM-07",
        "domain": "acmepya.com",
        "description": "Character transposition typosquatting domain",
        "is_malicious": True,
        "category": "LOOKALIKE_MUTATION",
    },
    # Look-Alikes: Brand Modifiers
    {
        "id": "DOM-08",
        "domain": "acmepay-login-support.com",
        "description": "Brand SLD with added phishing lure keywords",
        "is_malicious": True,
        "category": "LOOKALIKE_MODIFIER",
    },
    {
        "id": "DOM-09",
        "domain": "acmepay-secure-wallet.net",
        "description": "Brand SLD with security and wallet lure words",
        "is_malicious": True,
        "category": "LOOKALIKE_MODIFIER",
    },
    {
        "id": "DOM-10",
        "domain": "verify-acmepay.xyz",
        "description": "Suspicious TLD with verification lure prefix",
        "is_malicious": True,
        "category": "LOOKALIKE_MODIFIER",
    },
    # Look-Alikes: Unicode Homoglyphs
    {
        "id": "DOM-11",
        "domain": "\u0430cm\u0435p\u0430y.com",  # Cyrillic a, c, e
        "description": "IDN homoglyph lookalike imitating acmepay.com",
        "is_malicious": True,
        "category": "LOOKALIKE_HOMOGLYPH",
    },
    # Threat Intelligence IOC
    {
        "id": "DOM-12",
        "domain": "malicious-phish-kit.com",
        "description": "Known malicious phishing kit in threat feed",
        "is_malicious": True,
        "category": "THREAT_INTEL_IOC",
    },
]


SYNTHETIC_SOCIAL_PROFILES: List[Dict[str, Any]] = [
    # Legitimate Official
    {
        "id": "SOC-01",
        "platform": "Twitter",
        "username": "@acmepay",
        "display_name": "AcmePay Official",
        "bio": "Official Twitter for AcmePay services.",
        "external_links": ["https://acmepay.example"],
        "avatar_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "is_malicious": False,
        "category": "LEGITIMATE_OFFICIAL",
    },
    {
        "id": "SOC-02",
        "platform": "Twitter",
        "username": "@acmepay",
        "display_name": "AcmePay",
        "bio": None,
        "external_links": [],  # Missing optional links
        "avatar_hash": None,
        "is_malicious": False,
        "category": "LEGITIMATE_OFFICIAL_MISSING_DATA",
    },
    # Legitimate Unrelated
    {
        "id": "SOC-03",
        "platform": "Twitter",
        "username": "@nature_photography_2026",
        "display_name": "Nature Photos Daily",
        "bio": "Daily photographs of wildlife and landscapes.",
        "external_links": ["https://naturephotos.blog"],
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "SOC-04",
        "platform": "Twitter",
        "username": "@classic_cars_daily",
        "display_name": "Classic Car Garage",
        "bio": "Restoring vintage automobiles from the 1960s.",
        "external_links": ["https://classiccars.example"],
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "SOC-05",
        "platform": "Twitter",
        "username": "@baking_bread_today",
        "display_name": "Artisan Bread Bakery",
        "bio": "Sourdough guides and baking tips.",
        "external_links": [],
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    # Look-Alikes: Typo / Character mutations
    {
        "id": "SOC-06",
        "platform": "Twitter",
        "username": "@acmepayy",
        "display_name": "AcmePay",
        "bio": "Welcome to our page.",
        "external_links": [],
        "is_malicious": True,
        "category": "LOOKALIKE_MUTATION",
    },
    {
        "id": "SOC-07",
        "platform": "Twitter",
        "username": "@acme_pay",
        "display_name": "Acme Pay",
        "bio": "Payments for everyone.",
        "external_links": [],
        "is_malicious": True,
        "category": "LOOKALIKE_MUTATION",
    },
    {
        "id": "SOC-08",
        "platform": "Twitter",
        "username": "@acmepya",
        "display_name": "AcmePya",
        "bio": "Payment solutions.",
        "external_links": [],
        "is_malicious": True,
        "category": "LOOKALIKE_MUTATION",
    },
    # Look-Alikes: Added Modifier + Bio Impersonation Claim
    {
        "id": "SOC-09",
        "platform": "Twitter",
        "username": "@acmepay_support",
        "display_name": "AcmePay Customer Support",
        "bio": "Official customer support for AcmePay. Contact us for help.",
        "external_links": ["http://acmepay-helpdesk.top"],
        "is_malicious": True,
        "category": "LOOKALIKE_MODIFIER_BIO_CLAIM",
    },
    # Look-Alikes: Unicode Homoglyphs
    {
        "id": "SOC-10",
        "platform": "Twitter",
        "username": "@\u0410\u0441m\u0435\u0420\u0430\u0443",  # Cyrillic АсmеPау
        "display_name": "AcmePay",
        "bio": "Official services.",
        "external_links": [],
        "is_malicious": True,
        "category": "LOOKALIKE_HOMOGLYPH",
    },
    # Reused Brand Logo Avatar
    {
        "id": "SOC-11",
        "platform": "Twitter",
        "username": "@acmepay_alerts",
        "display_name": "AcmePay Alerts",
        "bio": "Security alerts.",
        "avatar_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "external_links": ["http://phish-acmepay.xyz"],
        "is_malicious": True,
        "category": "LOOKALIKE_REUSED_IMAGE",
    },
    # Compromised Official Account
    {
        "id": "SOC-12",
        "platform": "Twitter",
        "username": "@acmepay",
        "display_name": "AcmePay Official",
        "bio": "Official account.",
        "external_links": ["http://attacker-c2-redirect.net"],  # Malicious off-domain link
        "is_malicious": True,
        "category": "COMPROMISED_OFFICIAL",
    },
]


SYNTHETIC_APP_METADATA: List[Dict[str, Any]] = [
    # Legitimate Official
    {
        "id": "APP-01",
        "app_name": "AcmePay Wallet",
        "platform": "ANDROID",
        "app_identifier": "com.acmepay.wallet",
        "publisher_name": "AcmePay Technologies",
        "description": "The official AcmePay mobile wallet for digital payments.",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
        "logo_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "is_malicious": False,
        "category": "LEGITIMATE_OFFICIAL",
    },
    # Legitimate Unrelated
    {
        "id": "APP-02",
        "app_name": "Zen Meditation Timer",
        "platform": "ANDROID",
        "app_identifier": "com.zenstudios.meditation",
        "publisher_name": "Zen Studios",
        "description": "A mindful meditation bell and breathing timer.",
        "store_url": "https://play.google.com/store/apps/details?id=com.zenstudios.meditation",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "APP-03",
        "app_name": "Crypto Secure Notes",
        "platform": "ANDROID",
        "app_identifier": "com.secnotes.notes",
        "publisher_name": "NoteLabs",
        "description": "Encrypted offline notes application.",
        "store_url": "https://play.google.com/store/apps/details?id=com.secnotes.notes",
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED",
    },
    {
        "id": "APP-04",
        "app_name": "Classic Radio Streamer",
        "platform": "ANDROID",
        "app_identifier": "com.radio.classic",
        "publisher_name": None,  # Missing publisher
        "description": None,     # Missing description
        "store_url": None,        # Missing store URL
        "is_malicious": False,
        "category": "LEGITIMATE_UNRELATED_MISSING_DATA",
    },
    # Look-Alikes: Similar Name & Package Lookalike
    {
        "id": "APP-05",
        "app_name": "AcmePay Secure Wallet",
        "platform": "ANDROID",
        "app_identifier": "com.acmepay.wallet.scam",
        "publisher_name": "Acme Scam Studio",
        "description": "Official secure wallet app for AcmePay.",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet.scam",
        "is_malicious": True,
        "category": "LOOKALIKE_IMPERSONATION",
    },
    # Look-Alikes: Package Typosquatting
    {
        "id": "APP-06",
        "app_name": "AcmePay Wallet",
        "platform": "ANDROID",
        "app_identifier": "com.acmepayy.wallet",
        "publisher_name": "Rogue Developer",
        "description": "Fast wallet payments.",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmepayy.wallet",
        "is_malicious": True,
        "category": "LOOKALIKE_PACKAGE_TYPO",
    },
    # Look-Alikes: Unicode Homoglyphs
    {
        "id": "APP-07",
        "app_name": "\u0410\u0441m\u0435\u0420\u0430\u0443 Wallet",  # Cyrillic АсmеPау
        "platform": "ANDROID",
        "app_identifier": "com.payment.fakeacmepay",
        "publisher_name": "AcmePay Team",
        "description": "Wallet app.",
        "store_url": "https://play.google.com/store/apps/details?id=com.payment.fakeacmepay",
        "is_malicious": True,
        "category": "LOOKALIKE_HOMOGLYPH",
    },
    # Publisher Mismatch on Official Package
    {
        "id": "APP-08",
        "app_name": "AcmePay Wallet",
        "platform": "ANDROID",
        "app_identifier": "com.acmepay.wallet",
        "publisher_name": "Unauthorized Rogue Publisher",
        "description": "AcmePay Wallet.",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
        "is_malicious": True,
        "category": "PUBLISHER_MISMATCH",
    },
    # Credential Harvesting Lure in Description
    {
        "id": "APP-09",
        "app_name": "AcmePay Quick Pay",
        "platform": "ANDROID",
        "app_identifier": "com.acmepay.quickpay",
        "publisher_name": "QuickPay Inc",
        "description": "Please enter your password, PIN number, and seed phrase to claim rewards.",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.quickpay",
        "is_malicious": True,
        "category": "CREDENTIAL_HARVEST_LURE",
    },
    # Platform Store URL Host Mismatch
    {
        "id": "APP-10",
        "app_name": "AcmePay Client",
        "platform": "ANDROID",
        "app_identifier": "com.acmepay.client",
        "publisher_name": "Third Party Dev",
        "description": "Client app.",
        "store_url": "https://apps.apple.com/app/id123456",  # iOS host on Android app
        "is_malicious": True,
        "category": "STORE_URL_HOST_MISMATCH",
    },
    # Unauthorized Logo Reuse
    {
        "id": "APP-11",
        "app_name": "AcmePay Assistant",
        "platform": "ANDROID",
        "app_identifier": "com.acmeassistant.app",
        "publisher_name": "Assistant Studio",
        "description": "Official assistant.",
        "logo_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "store_url": "https://play.google.com/store/apps/details?id=com.acmeassistant.app",
        "is_malicious": True,
        "category": "UNAUTHORIZED_LOGO_REUSE",
    },
]
