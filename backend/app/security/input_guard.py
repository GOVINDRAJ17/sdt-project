"""Multi-layer Input Security Guard for defending LLM from prompt injection."""

import base64
import re
import unicodedata

from app.security.guard_models import GuardDecision, GuardResult

# Zero-width, directional, and invisible formatting characters
ZERO_WIDTH_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # byte order mark / zero-width no-break space
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u202a",  # left-to-right embedding
    "\u202b",  # right-to-left embedding
    "\u202c",  # pop directional formatting
    "\u202d",  # left-to-right override
    "\u202e",  # right-to-left override
    "\u2060",  # word joiner
    "\u2061",  # function application
    "\u2062",  # invisible times
    "\u2063",  # invisible separator
    "\u2064",  # invisible plus
]

# Common Cyrillic and Greek homoglyphs used to evade ASCII regex
HOMOGLYPH_MAP = {
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "у": "y",
    "х": "x",
    "і": "i",
    "ј": "j",
    "ѕ": "s",
    "ԁ": "d",
    "ԛ": "q",
    "ԝ": "w",
    "А": "A",
    "В": "B",
    "Е": "E",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "Х": "X",
}

# Delimiter attacks attempting to break out of structural isolation
DELIMITER_PATTERNS = [
    r"===\s*(?:BEGIN|END)\s+[A-Z\s]+===",
    r"---+\s*(?:BEGIN|END)\s+[A-Z\s]+---+",
    r"\[\/?INST\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\/?system>",
    r"```\s*(?:json|markdown|system)?",
]

# Explicit injection & instruction override patterns (English, Hindi, Marathi)
INJECTION_PATTERNS = [
    # Direct instruction override (English)
    r"\b(?:ignore|disregard|forget|override|bypass|cancel)\s+(?:all\s+)?(?:prior|previous|above|system|initial)\s+(?:instructions|prompts|directives|rules|guidelines|commands)\b",
    r"\bdisregard\s+(?:everything|all)\s+(?:said|written)\s+above\b",
    r"\bnew\s+instructions\s*:\s*(?:ignore|forget|override)\b",
    r"\bclear\s+(?:all\s+)?previous\s+context\b",
    r"\bstop\s+following\s+system\s+prompt\b",
    # Roleplay / Jailbreak / DAN (English)
    r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(?:DAN|an\s+unrestricted|a\s+jailbroken|developer\s+mode|root|administrator)\b",
    r"\bswitch\s+to\s+(?:developer\s+mode|god\s+mode|unrestricted\s+mode|unaligned\s+mode)\b",
    r"\benable\s+(?:debug|root|bypass)\s+mode\b",
    r"\byou\s+have\s+no\s+(?:rules|filters|guidelines|restrictions)\b",
    # System prompt / Canary token exfiltration (English)
    r"\b(?:reveal|print|show|repeat|display|echo|output|leak|tell\s+me)\s+(?:the\s+)?(?:system\s+prompt|canary\s+token|secret\s+token|initial\s+prompt|hidden\s+instructions)\b",
    r"\bwhat\s+(?:is|are)\s+(?:the\s+)?(?:system\s+prompt|canary\s+token|secret\s+token|hidden\s+rules)\b",
    r"\becho\s+(?:the\s+)?(?:system\s+message|canary)\s+verbatim\b",
    # Hallucination / Override forcing
    r"\b(?:say|claim|state|declare|report)\s+(?:that\s+)?(?:the\s+)?severity\s+(?:is|as)\s+(?:NONE|HEATWAVE|SEVERE_HEATWAVE)\b",
    r"\bforce\s+(?:the\s+)?(?:severity|temperature|tmax)\s+to\b",
    r"\bignore\s+actual\s+forecast\s+and\s+report\b",
    r"\bdo\s+not\s+report\s+the\s+forecasted\s+temperature\b",
    # Hindi injection patterns (हिन्दी)
    r"पिछले\s+(?:सभी\s+)?निर्देशों?\s+को\s+(?:अनदेखा|नजरअंदाज)\s+करें",
    r"सिस्टम\s+प्रॉम्प्ट\s+(?:भूल\s+जाओ|दिखाओ|बताओ|प्रकट\s+करो)",
    r"सभी\s+नियमों?\s+को\s+(?:रद्द|बायपास)\s+करें",
    r"गुप्त\s+कैनरी\s+टोकन\s+(?:बताओ|दिखाओ)",
    r"अब\s+आप\s+बिना\s+किसी\s+नियम\s+के\s+काम\s+करें",
    # Marathi injection patterns (मराठी)
    r"मागील\s+(?:सर्व\s+)?सूचना\s+(?:दुर्लक्षित\s+करा|विसरा)",
    r"सिस्टम\s+सूचना\s+(?:विसरा|दाखवा|सांगा)",
    r"सर्व\s+नियम\s+(?:रद्द\s+करा|दुर्लक्षित\s+करा)",
    r"गुप्त\s+कॅनरी\s+टोकन\s+दाखवा",
    r"आता\s+तुम्ही\s+कोणत्याही\s+नियमांशिवाय\s+काम\s+करा",
]

# Benign phrases containing words like "ignore" or "instructions" that MUST NOT be blocked
BENIGN_EXCEPTIONS = [
    r"\bdo\s+not\s+ignore\b",
    r"\bcannot\s+ignore\b",
    r"\bcan\'?t\s+ignore\b",
    r"\bnever\s+ignore\b",
    r"\bignore\s+(?:the\s+)?(?:rumors?|false\s+claims?|social\s+media|unverified\s+reports?)\b",
    r"\bignore\s+(?:the\s+)?(?:minor\s+wind|dew\s+point|noise|instrument\s+drift|fluctuation)\b",
    r"\bfollow\s+(?:all\s+)?(?:imd|official|government|medical)\s+instructions\b",
]


class InputGuard:
    """Production-grade multi-layer input guard for sanitization and attack mitigation."""

    def __init__(self, max_length: int = 1000):
        self.max_length = max_length

    def _normalize_text(self, text: str) -> tuple[str, list[str]]:
        """Normalize Unicode, strip zero-width characters, and map homoglyphs."""
        flags: list[str] = []

        # 1. Strip zero-width / directional markers
        clean_text = text
        stripped_zw = False
        for zw in ZERO_WIDTH_CHARS:
            if zw in clean_text:
                clean_text = clean_text.replace(zw, "")
                stripped_zw = True
        if stripped_zw:
            flags.append("STRIPPED_ZERO_WIDTH_CHARS")

        # 2. Unicode NFKC normalization
        norm_text = unicodedata.normalize("NFKC", clean_text)
        if norm_text != clean_text:
            flags.append("UNICODE_NORMALIZED_NFKC")

        # 3. Replace Latin-Cyrillic homoglyphs
        homoglyph_found = False
        chars = []
        for ch in norm_text:
            if ch in HOMOGLYPH_MAP:
                chars.append(HOMOGLYPH_MAP[ch])
                homoglyph_found = True
            else:
                chars.append(ch)
        if homoglyph_found:
            norm_text = "".join(chars)
            flags.append("NORMALIZED_HOMOGLYPHS")

        # 4. Collapse excessive whitespace
        collapsed = re.sub(r"[ \t]+", " ", norm_text).strip()
        if collapsed != norm_text:
            flags.append("COLLAPSED_WHITESPACE")

        return collapsed, flags

    def _detect_base64_payloads(self, text: str) -> tuple[bool, str, list[str]]:
        """Scan for base64 encoded strings and inspect decoded content."""
        # Match base64 chunks of length 16+
        b64_pattern = r"(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"
        matches = re.findall(b64_pattern, text)
        detected: list[str] = []

        for m in matches:
            if len(m) < 16:
                continue
            try:
                decoded = base64.b64decode(m).decode("utf-8", errors="ignore").lower()
                # Check decoded payload against attack keywords
                if any(
                    k in decoded
                    for k in ["ignore", "system prompt", "canary", "override", "bypass"]
                ):
                    detected.append(f"BASE64_INJECTION_PAYLOAD: {decoded[:40]}...")
            except Exception:
                continue

        return len(detected) > 0, text, detected

    def _detect_delimiters(self, text: str) -> list[str]:
        """Detect attempts to inject prompt boundary delimiters."""
        triggers: list[str] = []
        for pat in DELIMITER_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                triggers.append(f"DELIMITER_INJECTION: {pat}")
        return triggers

    def _detect_injection_patterns(self, text: str) -> list[str]:
        """Match against direct injection patterns while respecting legitimate weather context."""
        matched: list[str] = []

        # Check if the text matches a benign exemption first
        is_exempt = any(re.search(benign, text, re.IGNORECASE) for benign in BENIGN_EXCEPTIONS)

        for pat in INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                # If it's exempt and the match is generic, verify
                if is_exempt and "ignore previous" not in text.lower():
                    continue
                matched.append(f"INJECTION_PATTERN: {pat}")

        return matched

    def check(self, text: str | None) -> GuardResult:
        """
        Evaluate untrusted text through all security guard layers.

        Returns:
            GuardResult with ALLOW, SANITIZE, or BLOCK decision and detailed risk breakdown.
        """
        if not text or not text.strip():
            return GuardResult(
                decision=GuardDecision.ALLOW,
                risk_score=0.0,
                original_text=text or "",
                sanitized_text="",
                flags=["EMPTY_INPUT"],
                detected_patterns=[],
                is_blocked=False,
            )

        original_text = text
        flags: list[str] = []
        detected_patterns: list[str] = []

        # Length enforcement
        if len(text) > self.max_length:
            text = text[: self.max_length]
            flags.append(f"TRUNCATED_TO_MAX_LENGTH_{self.max_length}")

        # Layer 1: Normalization
        sanitized_text, norm_flags = self._normalize_text(text)
        flags.extend(norm_flags)

        # Layer 2: Base64 payload detection
        has_b64, _, b64_triggers = self._detect_base64_payloads(sanitized_text)
        detected_patterns.extend(b64_triggers)

        # Layer 3: Delimiter breakout detection
        delimiter_triggers = self._detect_delimiters(sanitized_text)
        detected_patterns.extend(delimiter_triggers)

        # Layer 4: Pattern & Semantic Rule Engine
        injection_triggers = self._detect_injection_patterns(sanitized_text)
        detected_patterns.extend(injection_triggers)

        # Calculate risk score
        risk_score = 0.0

        if detected_patterns:
            # Critical attacks (delimiters, direct overrides, base64 payload)
            risk_score = min(1.0, 0.70 + (0.10 * len(detected_patterns)))
        elif norm_flags:
            # Suspicious zero-width or homoglyphs without explicit attack keywords
            risk_score = (
                0.40
                if "STRIPPED_ZERO_WIDTH_CHARS" in norm_flags
                or "NORMALIZED_HOMOGLYPHS" in norm_flags
                else 0.15
            )
        else:
            risk_score = 0.0

        # Decision Mapping
        if risk_score >= 0.70 or len(detected_patterns) > 0:
            decision = GuardDecision.BLOCK
            is_blocked = True
        elif risk_score >= 0.30:
            decision = GuardDecision.SANITIZE
            is_blocked = False
        else:
            decision = GuardDecision.ALLOW
            is_blocked = False

        return GuardResult(
            decision=decision,
            risk_score=round(risk_score, 2),
            original_text=original_text,
            sanitized_text=sanitized_text,
            flags=flags,
            detected_patterns=detected_patterns,
            is_blocked=is_blocked,
        )


input_guard = InputGuard()
