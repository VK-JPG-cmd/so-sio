"""
Development benchmark dataset for scam text classification.
Contains representative labeled development examples for baseline training.
NOTE: This is a controlled development dataset, not a massive production corpus.
"""

from typing import List, Tuple

# Labeled pairs: (text, label) where 1 = SCAM / PHISHING, 0 = BENIGN / LEGITIMATE
DEVELOPMENT_SCAM_DATASET: List[Tuple[str, int]] = [
    # --- SCAM / PHISHING SAMPLES (1) ---
    (
        "URGENT: Your bank account has been locked due to suspicious activity. "
        "Click http://bit.ly/secure-login-29 immediately to verify your identity.",
        1,
    ),
    (
        "Final Notice: IRS tax refund of $1,420 is pending approval. "
        "Submit your social security number and debit card details at http://irs-tax-gov.top",
        1,
    ),
    (
        "Congratulations! You won the Walmart $1,000 gift card lottery. "
        "Claim your prize now by sending a $50 processing fee via Bitcoin.",
        1,
    ),
    (
        "Alert: Unusual sign-in attempt detected from Russia. "
        "Please reply with your one-time 6-digit verification code to keep your account safe.",
        1,
    ),
    (
        "Your Netflix subscription has expired. Payment failed. "
        "Update your credit card immediately or service will be terminated: http://netfix-billing.xyz",
        1,
    ),
    (
        "Crypto Investment Opportunity: Guaranteed 300% weekly return with automated trading bots. "
        "Send Ethereum to our smart contract address to start earning today.",
        1,
    ),
    (
        "DHL Express: Your package delivery has been put on hold due to unpaid customs fee of $2.99. "
        "Pay now at http://track-dhl-parcel.link/pay",
        1,
    ),
    (
        "Security Alert: Your Amazon account has been suspended for fraud. "
        "Call our support center immediately at 1-800-FAKE-NUM or click http://amzn-account-verify.info",
        1,
    ),
    (
        "Dear customer, your PayPal account has been limited. "
        "Download the attached invoice.pdf.exe and confirm your billing credentials to restore access.",
        1,
    ),
    (
        "Apple Support: Find My iPhone located your lost device. "
        "Sign in with your Apple ID and password to see real-time location: http://icloud-find-device.cc",
        1,
    ),
    (
        "URGENT: Immediate action required. Transfer funds to safe escrow wallet immediately.",
        1,
    ),
    (
        "Act now! Wire transfer $500 gift card to avoid arrest warrant from local police department.",
        1,
    ),

    # --- BENIGN / LEGITIMATE SAMPLES (0) ---
    (
        "Thank you for reaching out to Acme Support. Your ticket #48192 has been received. "
        "An agent will review your inquiry within one business day.",
        0,
    ),
    (
        "Your monthly statement for account ending in 4102 is now available. "
        "Sign in to your online banking portal to review your transactions.",
        0,
    ),
    (
        "Hi John, here is the meeting recap and action items from our project sync earlier today. "
        "Let me know if you have any questions.",
        0,
    ),
    (
        "Your order #99281 has shipped and is estimated to arrive on Thursday. "
        "Tracking details are available in your customer order history.",
        0,
    ),
    (
        "Welcome to the BrandShield AI community. Please review our documentation "
        "and security guidelines to get started with API integration.",
        0,
    ),
    (
        "Reminder: Scheduled system maintenance will take place this Sunday from 2 AM to 4 AM UTC. "
        "No downtime is expected for primary services.",
        0,
    ),
    (
        "Your password was changed successfully on 2026-10-09. "
        "If you did not perform this change, please contact official customer service.",
        0,
    ),
    (
        "Here are the release notes for version 2.4.0 featuring improved search filters "
        "and updated user preferences in the dashboard.",
        0,
    ),
    (
        "Thank you for attending our product webinar today. "
        "The presentation slides and video recording have been posted to our resources page.",
        0,
    ),
    (
        "Good morning, please find attached the quarterly financial summary report for your team.",
        0,
    ),
    (
        "Your appointment with Dr. Smith is confirmed for tomorrow at 10:30 AM. "
        "Please bring your photo ID and insurance card.",
        0,
    ),
    (
        "Happy holidays from all of us at Acme Corporation! Our office will be closed on Friday.",
        0,
    ),
]
