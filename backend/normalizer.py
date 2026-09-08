import re
from typing import Tuple, Optional, Dict, Any

class Normalizer:
    """
    Entity resolution, temporal parsing, and currency/unit normalization engine.
    Ensures that differences in formatting do not masquerade as contradictions.
    """

    # Entity canonical mapping dictionary
    KNOWN_ENTITY_ALIASES = {
        "delhivery": "Delhivery Limited",
        "delhivery limited": "Delhivery Limited",
        "the company": "Delhivery Limited",
        "our company": "Delhivery Limited",
        "the group": "Delhivery Limited",
        "reserve bank of india": "Reserve Bank of India",
        "rbi": "Reserve Bank of India",
        "the bank": "Reserve Bank of India",
        "international monetary fund": "International Monetary Fund",
        "imf": "International Monetary Fund",
        "government of india": "Government of India",
        "goi": "Government of India",
    }

    LEGAL_SUFFIXES = [
        r"\blimited\b", r"\bltd\b", r"\binc\b", r"\bincorporated\b",
        r"\bcorp\b", r"\bcorporation\b", r"\bllc\b", r"\bpvt\b", r"\bprivate\b"
    ]

    @classmethod
    def canonicalize_entity(cls, entity_str: str) -> str:
        """Strips legal suffixes and resolves pronouns/aliases to the canonical entity."""
        if not entity_str:
            return "Unknown Entity"
        
        cleaned = entity_str.strip()
        lower_cleaned = cleaned.lower()

        if lower_cleaned in cls.KNOWN_ENTITY_ALIASES:
            return cls.KNOWN_ENTITY_ALIASES[lower_cleaned]

        # Strip legal suffix and check again
        simplified = lower_cleaned
        for suffix in cls.LEGAL_SUFFIXES:
            simplified = re.sub(suffix, "", simplified, flags=re.IGNORECASE).strip()
        simplified = re.sub(r"\s+", " ", simplified).strip()

        if simplified in cls.KNOWN_ENTITY_ALIASES:
            return cls.KNOWN_ENTITY_ALIASES[simplified]

        # Default: title case the cleaned entity name
        return cleaned.title()

    @classmethod
    def normalize_temporal(cls, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extracts fiscal period, period_start (ISO), and period_end (ISO).
        Returns: (fiscal_period, period_start, period_end)
        """
        text_lower = text.lower()

        # FY24 / FY 2023-24 / 2023-2024 / year ended March 31, 2024
        if any(k in text_lower for k in ["fy24", "fy 24", "fy 2024", "2023-24", "2023-2024", "march 31, 2024"]):
            if "q4" in text_lower:
                return "Q4_FY24", "2024-01-01", "2024-03-31"
            return "FY24", "2023-04-01", "2024-03-31"

        # FY22 / FY 2021-22 / 2021-2022 / year ended March 31, 2022
        if any(k in text_lower for k in ["fy22", "fy 22", "fy 2022", "2021-22", "2021-2022", "march 31, 2022"]):
            return "FY22", "2021-04-01", "2022-03-31"

        # FY23 / FY 2022-23 / 2022-2023 / year ended March 31, 2023
        if any(k in text_lower for k in ["fy23", "fy 23", "fy 2023", "2022-23", "2022-2023", "march 31, 2023"]):
            return "FY23", "2022-04-01", "2023-03-31"

        # FY25 / 2024-25
        if any(k in text_lower for k in ["fy25", "fy 25", "2024-25", "march 31, 2025"]):
            return "FY25", "2024-04-01", "2025-03-31"

        return None, None, None

    @classmethod
    def normalize_quantity(cls, raw_val: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Converts financial quantity into base absolute float, canonical currency, and unit.
        Example:
          '₹7,935 crore' -> (79350000000.0, 'INR', 'crore')
          '79.35B INR'    -> (79350000000.0, 'INR', 'billion')
        """
        if not raw_val:
            return None, None, None

        cleaned = raw_val.replace(",", "").strip()

        # Currency detection
        currency = None
        if "₹" in cleaned or "rs" in cleaned.lower() or "inr" in cleaned.lower():
            currency = "INR"
        elif "$" in cleaned or "usd" in cleaned.lower():
            currency = "USD"
        elif "€" in cleaned or "eur" in cleaned.lower():
            currency = "EUR"

        # Multiplier detection
        multiplier = 1.0
        unit = "absolute"
        lower = cleaned.lower()

        if "crore" in lower or "cr" in lower:
            multiplier = 10_000_000.0  # 1e7
            unit = "crore"
        elif "lakh" in lower or "lac" in lower:
            multiplier = 100_000.0     # 1e5
            unit = "lakh"
        elif "billion" in lower or re.search(r"\b\d+(\.\d+)?\s*b\b", lower):
            multiplier = 1_000_000_000.0 # 1e9
            unit = "billion"
        elif "million" in lower or re.search(r"\b\d+(\.\d+)?\s*m\b", lower):
            multiplier = 1_000_000.0   # 1e6
            unit = "million"
        elif "%" in lower or "percent" in lower:
            unit = "percent"
            multiplier = 1.0

        # Extract number
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if not match:
            return None, currency, unit

        try:
            num = float(match.group())
            normalized_value = round(num * multiplier, 2)
            return normalized_value, currency, unit
        except ValueError:
            return None, currency, unit
