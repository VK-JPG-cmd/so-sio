"""
Defensible Threat Relationship Engine.
Evaluates evidence-backed connections between threat entities.
Strict Invariant: Entities are NEVER correlated solely because they mention or target the same brand.
"""

from typing import Any, Dict, Optional, Tuple
from rapidfuzz import fuzz
import tldextract

from app.models.enums import EntityType, RelationshipStatus, RelationshipType
from app.models.threat_entity import ThreatEntity
from app.services.detection.homoglyphs import HomoglyphDetector


class RelationshipEvaluation:
    """Outcome of relationship evaluation between two entities."""

    def __init__(
        self,
        relationship_type: RelationshipType,
        relationship_status: RelationshipStatus,
        confidence: float,
        reason: str,
        evidence_details: Dict[str, Any],
    ) -> None:
        self.relationship_type = relationship_type
        self.relationship_status = relationship_status
        self.confidence = confidence
        self.reason = reason
        self.evidence_details = evidence_details


class DefensibleRelationshipEngine:
    """
    Evaluates evidence-backed technical connections between threat entities.
    Requires concrete infrastructure, lexical, perceptual, or threat intelligence evidence.
    """

    def __init__(self) -> None:
        self.tld_extractor = tldextract.TLDExtract(cache_dir=None)

    def evaluate_pair(
        self,
        entity_a: ThreatEntity,
        entity_b: ThreatEntity,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[RelationshipEvaluation]:
        """
        Evaluate if entity_a and entity_b share a defensible technical link.
        Returns RelationshipEvaluation if evidence exists, else None.
        """
        if entity_a.id == entity_b.id:
            return None

        ctx = shared_context or {}

        # 1. SIMILAR_DOMAIN (Both are DOMAIN entities)
        if entity_a.entity_type == EntityType.DOMAIN and entity_b.entity_type == EntityType.DOMAIN:
            dom_a = entity_a.canonical_value
            dom_b = entity_b.canonical_value

            # Extract registrable domains
            ext_a = self.tld_extractor(dom_a)
            ext_b = self.tld_extractor(dom_b)
            reg_a = (
                ext_a.top_domain_under_public_suffix
                if hasattr(ext_a, "top_domain_under_public_suffix")
                else ext_a.registered_domain
            ) or dom_a
            reg_b = (
                ext_b.top_domain_under_public_suffix
                if hasattr(ext_b, "top_domain_under_public_suffix")
                else ext_b.registered_domain
            ) or dom_b

            # Check Homoglyphs
            _, canon_a, _ = HomoglyphDetector.analyze_string(dom_a)
            _, canon_b, _ = HomoglyphDetector.analyze_string(dom_b)

            if canon_a == canon_b or canon_a == dom_b or canon_b == dom_a:
                return RelationshipEvaluation(
                    relationship_type=RelationshipType.SIMILAR_DOMAIN,
                    relationship_status=RelationshipStatus.CONFIRMED,
                    confidence=0.95,
                    reason=f"Domains '{dom_a}' and '{dom_b}' share visual Unicode homoglyphs.",
                    evidence_details={"type": "homoglyph_collision", "canonical": canon_a},
                )

            # High lexical similarity (ratio or multi-token overlap)
            sim = max(fuzz.ratio(reg_a, reg_b), fuzz.token_set_ratio(reg_a, reg_b))
            if sim >= 75.0:
                conf = round(sim / 100.0, 2)
                status = RelationshipStatus.CONFIRMED if sim >= 85.0 else RelationshipStatus.INVESTIGATED
                return RelationshipEvaluation(
                    relationship_type=RelationshipType.SIMILAR_DOMAIN,
                    relationship_status=status,
                    confidence=conf,
                    reason=f"Registrable domains '{reg_a}' and '{reg_b}' exhibit {sim:.1f}% lexical similarity.",
                    evidence_details={"type": "lexical_similarity", "ratio": sim},
                )

        # 2. SHARED_DESTINATION (URL pointing to specific DOMAIN or IP)
        if (
            (entity_a.entity_type == EntityType.URL and entity_b.entity_type in [EntityType.DOMAIN, EntityType.IP_ADDRESS])
            or (entity_b.entity_type == EntityType.URL and entity_a.entity_type in [EntityType.DOMAIN, EntityType.IP_ADDRESS])
        ):
            url_ent = entity_a if entity_a.entity_type == EntityType.URL else entity_b
            target_ent = entity_b if entity_a.entity_type == EntityType.URL else entity_a

            from urllib.parse import urlparse
            url_host = urlparse(url_ent.canonical_value).netloc.split(":")[0]

            if url_host == target_ent.canonical_value:
                return RelationshipEvaluation(
                    relationship_type=RelationshipType.SHARED_DESTINATION,
                    relationship_status=RelationshipStatus.CONFIRMED,
                    confidence=1.0,
                    reason=f"URL '{url_ent.canonical_value}' targets destination host '{target_ent.canonical_value}'.",
                    evidence_details={"type": "direct_url_host_resolution", "host": url_host},
                )

        # 3. REUSED_IMAGE_HASH (Both are IMAGE_HASH entities)
        if entity_a.entity_type == EntityType.IMAGE_HASH and entity_b.entity_type == EntityType.IMAGE_HASH:
            hash_a = entity_a.canonical_value
            hash_b = entity_b.canonical_value

            # Compute hex Hamming distance
            try:
                val_a = int(hash_a, 16)
                val_b = int(hash_b, 16)
                distance = bin(val_a ^ val_b).count("1")
                if distance <= 6:
                    conf = round(max(0.7, 1.0 - (distance / 64.0)), 2)
                    status = RelationshipStatus.CONFIRMED if distance <= 2 else RelationshipStatus.INVESTIGATED
                    return RelationshipEvaluation(
                        relationship_type=RelationshipType.REUSED_IMAGE_HASH,
                        relationship_status=status,
                        confidence=conf,
                        reason=f"Perceptual image hashes have close Hamming distance ({distance} bits).",
                        evidence_details={"hamming_distance": distance, "hash_a": hash_a, "hash_b": hash_b},
                    )
            except Exception:
                pass

        # 4. REPEATED_SCAM_PATTERN (Both are SCAM_TEXT_HASH with verified pattern or shared context)
        if (
            entity_a.entity_type == EntityType.SCAM_TEXT_HASH
            and entity_b.entity_type == EntityType.SCAM_TEXT_HASH
        ):
            if entity_a.canonical_value == entity_b.canonical_value:
                return RelationshipEvaluation(
                    relationship_type=RelationshipType.REPEATED_SCAM_PATTERN,
                    relationship_status=RelationshipStatus.CONFIRMED,
                    confidence=1.0,
                    reason="Identical cryptographic text hash for scam message payload.",
                    evidence_details={"type": "exact_scam_hash_match"},
                )

        # 5. SHARED_INFRASTRUCTURE from explicit context (e.g. shared IP or MX record)
        if ctx.get("shared_ip"):
            return RelationshipEvaluation(
                relationship_type=RelationshipType.SHARED_INFRASTRUCTURE,
                relationship_status=RelationshipStatus.INVESTIGATED,
                confidence=0.85,
                reason=f"Entities co-hosted on shared IP infrastructure: {ctx.get('shared_ip')}.",
                evidence_details={"type": "shared_ip", "ip": ctx.get("shared_ip")},
            )

        # 6. THREAT_INTEL_CLUSTER from explicit feed correlation
        if ctx.get("shared_threat_cluster"):
            return RelationshipEvaluation(
                relationship_type=RelationshipType.THREAT_INTEL_CLUSTER,
                relationship_status=RelationshipStatus.CONFIRMED,
                confidence=0.90,
                reason=f"Entities co-indexed in threat intelligence cluster: {ctx.get('shared_threat_cluster')}.",
                evidence_details={"type": "threat_intel_cluster", "cluster": ctx.get("shared_threat_cluster")},
            )

        # Invariant: No defensible technical relationship found.
        # NEVER connect entities solely because they target the same brand.
        return None
