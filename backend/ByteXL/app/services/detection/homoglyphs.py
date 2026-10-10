"""
Homoglyph and Unicode-confusable detection module.
Identifies visual spoofing attempts where Cyrillic, Greek, or internationalized
characters mimic Latin characters to impersonate legitimate brand assets.
"""

from typing import Dict, List, Set, Tuple
import unicodedata

# Mapping from common visual lookalike characters to their Latin ASCII equivalents
CONFUSABLE_MAP: Dict[str, str] = {
    # Cyrillic small letters
    "а": "a",  # U+0430
    "с": "c",  # U+0441
    "е": "e",  # U+0435
    "і": "i",  # U+0456
    "ј": "j",  # U+0458
    "к": "k",  # U+043A
    "о": "o",  # U+043E
    "р": "p",  # U+0440
    "ѕ": "s",  # U+0455
    "х": "x",  # U+0445
    "у": "y",  # U+0443
    "ԁ": "d",  # U+0501
    "ԛ": "q",  # U+051B
    "ԝ": "w",  # U+051D
    # Cyrillic capital letters
    "А": "A",  # U+0410
    "В": "B",  # U+0412
    "С": "C",  # U+0421
    "Е": "E",  # U+0415
    "Н": "H",  # U+041D
    "І": "I",  # U+0406
    "Ј": "J",  # U+0408
    "К": "K",  # U+041A
    "М": "M",  # U+041C
    "О": "O",  # U+041E
    "Р": "P",  # U+0420
    "Ѕ": "S",  # U+0405
    "Т": "T",  # U+0422
    "Х": "X",  # U+0425
    "Ү": "Y",  # U+04AE
    # Greek letters
    "α": "a",  # U+03B1
    "β": "b",  # U+03B2
    "ε": "e",  # U+03B5
    "ι": "i",  # U+03B9
    "κ": "k",  # U+03BA
    "ν": "v",  # U+03BD
    "ο": "o",  # U+03BF
    "ρ": "p",  # U+03C1
    "τ": "t",  # U+03C4
    "υ": "u",  # U+03C5
    "χ": "x",  # U+03C7
    "Α": "A",  # U+0391
    "Β": "B",  # U+0392
    "Ε": "E",  # U+0395
    "Η": "H",  # U+0397
    "Ι": "I",  # U+0399
    "Κ": "K",  # U+039A
    "Μ": "M",  # U+039C
    "Ν": "N",  # U+039D
    "Ο": "O",  # U+039F
    "Ρ": "P",  # U+03A1
    "Τ": "T",  # U+03A4
    "Χ": "X",  # U+03A7
    "Υ": "Y",  # U+03A5
    # Fullwidth / special forms
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
}


class HomoglyphDetector:
    """Detects and decodes visual lookalike homoglyphs in domains, handles, and URLs."""

    @classmethod
    def analyze_string(cls, text: str) -> Tuple[bool, str, List[Dict[str, str]]]:
        """
        Analyze a string for homoglyphs and confusables.
        Returns:
            (has_homoglyphs, canonical_ascii_equivalent, detected_confusables)
        """
        # If string is punycode (starts with xn--), decode it first
        analyzed_text = text
        if text.startswith("xn--") or ".xn--" in text:
            try:
                analyzed_text = text.encode("ascii").decode("idna")
            except Exception:
                pass

        detected: List[Dict[str, str]] = []
        canonical_chars: List[str] = []
        has_homoglyph = False

        for char in analyzed_text:
            if char in CONFUSABLE_MAP:
                has_homoglyph = True
                latin_equiv = CONFUSABLE_MAP[char]
                char_name = unicodedata.name(char, "UNKNOWN UNICODE")
                detected.append({
                    "confusable_char": char,
                    "latin_equivalent": latin_equiv,
                    "codepoint": f"U+{ord(char):04X}",
                    "unicode_name": char_name,
                })
                canonical_chars.append(latin_equiv)
            else:
                canonical_chars.append(char)

        canonical_text = "".join(canonical_chars)
        return has_homoglyph, canonical_text, detected

    @classmethod
    def detect_mixed_script(cls, text: str) -> bool:
        """
        Detect whether a string mixes Latin characters with non-Latin scripts (e.g. Cyrillic/Greek).
        This is a hallmark of IDN homograph attack domains.
        """
        scripts: Set[str] = set()
        for char in text:
            if not char.isalpha():
                continue
            name = unicodedata.name(char, "")
            if "LATIN" in name:
                scripts.add("LATIN")
            elif "CYRILLIC" in name:
                scripts.add("CYRILLIC")
            elif "GREEK" in name:
                scripts.add("GREEK")
            elif "ARABIC" in name:
                scripts.add("ARABIC")
            elif "HEBREW" in name:
                scripts.add("HEBREW")

        return len(scripts) > 1
