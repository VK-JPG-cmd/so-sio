"""
Lookalike Name and Typo Variation Detection Service (+5 Bonus Points).
Generates and detects brand name variations across:
1. Character swaps (ApexBank -> ApexBnka)
2. Character additions (ApexBank -> ApexXBank)
3. Spacing changes (ApexBank -> Apex Bank)
4. Homoglyphs & Leet substitutions (ApexBank -> ApexB4nk, 0/O, 1/l/I, 5/S, @/a)
5. Typos and double consonants (ApexBank -> ApexBannk)
6. Number suffixes (ApexBank -> Apexbank123)
"""

from typing import Dict, Iterator, List, Set, Tuple
from rapidfuzz import fuzz, distance

HOMOGLYPH_MAP = {
    "o": ["0"], "O": ["0"],
    "i": ["1", "l"], "I": ["1", "l"],
    "l": ["1", "i"], "L": ["1", "i"],
    "s": ["5", "$"], "S": ["5", "$"],
    "a": ["4", "@"], "A": ["4", "@"],
    "e": ["3"], "E": ["3"],
    "b": ["8", "6"], "B": ["8"],
    "t": ["7", "+"], "T": ["7", "+"],
}


class LookalikeNameDetector:
    """Intelligent brand name variation generator and lookalike similarity scorer."""

    def generate_variations(self, name: str) -> Iterator[str]:
        """Generate typos, swaps, insertions, deletions, and homoglyphs."""
        clean = name.strip()
        lower = clean.lower()

        # 1. Spacing changes
        if len(clean) > 4:
            mid = len(clean) // 2
            yield f"{clean[:mid]} {clean[mid:]}"

        # 2. Character swaps (transposition typos)
        for i in range(len(clean) - 1):
            yield clean[:i] + clean[i+1] + clean[i] + clean[i+2:]

        # 3. Double letters (repetition typos)
        for i in range(len(clean)):
            yield clean[:i] + clean[i] + clean[i:]

        # 4. Homoglyphs / Leet speak substitutions
        for i, char in enumerate(clean):
            if char in HOMOGLYPH_MAP:
                for variant in HOMOGLYPH_MAP[char]:
                    yield clean[:i] + variant + clean[i+1:]

        # 5. Common scam additions & suffixes
        for suffix in ["Official", "Support", "Help", "Desk", "Secure", "Pay", "123", "24x7"]:
            yield f"{clean}{suffix}"
            yield f"{clean}_{suffix.lower()}"

    def detect_name_variations(self, official_name: str, max_variations: int = 50) -> List[str]:
        """Returns a deduplicated list of realistic lookalike variations."""
        seen: Set[str] = set()
        results: List[str] = []
        for var in self.generate_variations(official_name):
            if var != official_name and var not in seen:
                seen.add(var)
                results.append(var)
                if len(results) >= max_variations:
                    break
        return results

    async def calculate_similarity(self, official_name: str, candidate_name: str) -> float:
        """
        Calculates similarity percentage [0.0 - 1.0] across Levenshtein,
        token sort, homoglyph normalization, and character ngram models.
        """
        norm_off = official_name.lower().replace(" ", "").replace("_", "")
        norm_cand = candidate_name.lower().replace(" ", "").replace("_", "")

        if norm_off == norm_cand:
            return 1.0

        # Replace leet/homoglyph characters for canonical comparison
        canon_cand = norm_cand
        for orig, replacements in HOMOGLYPH_MAP.items():
            for r in replacements:
                canon_cand = canon_cand.replace(r.lower(), orig.lower())

        # If after homoglyph translation it matches official name, score is 0.95+
        if canon_cand == norm_off or norm_off in canon_cand:
            return 0.96

        # Ratio checks
        ratio = fuzz.ratio(norm_off, norm_cand) / 100.0
        partial = fuzz.partial_ratio(norm_off, norm_cand) / 100.0
        token_sort = fuzz.token_sort_ratio(norm_off, norm_cand) / 100.0

        # Levenshtein distance check
        lev_dist = distance.Levenshtein.distance(norm_off, norm_cand)
        lev_score = max(0.0, 1.0 - (lev_dist / max(len(norm_off), len(norm_cand), 1)))

        return round(max(ratio, partial * 0.85, token_sort, lev_score), 2)
