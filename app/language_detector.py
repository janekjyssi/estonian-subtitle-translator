"""
Language detection module for subtitle files.

Detects the language of subtitle text locally without external API calls.
Uses heuristic-based detection for reliability without external dependencies.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple


# ============================================================================
# LANGUAGE CONFIGURATION  
# ============================================================================

# Mapping from language code to display name (in Estonian)
CODE_TO_DISPLAY = {
    "en": "Inglise",
    "et": "Eesti",
    "fi": "Soome",
    "sv": "Rootsi",
    "de": "Saksa",
    "ru": "Vene",
    "fr": "Prantsuse",
    "es": "Hispaania",
    "it": "Itaalia",
    "pl": "Poola",
    "pt": "Portugali",
    "nl": "Hollandi",
    "no": "Norra",
    "da": "Taani",
    "cs": "Tšiki",
    "hu": "Ungari",
    "ro": "Rumeenia",
    "el": "Kreeka",
    "tr": "Türgi",
    "uk": "Ukraina",
    "ja": "Jaapani",
    "zh-cn": "Hiina",
    "zh-tw": "Hiina",
    "ko": "Korea",
    "th": "Tai",
    "vi": "Vietnami",
    "ar": "Araabia",
    "he": "Heebrea",
}

# Language-specific markers (common words/patterns)
LANGUAGE_MARKERS = {
    "en": {
        "words": [
            "the", "and", "a", "to", "of", "is", "in", "you", "it", "that",
            "hello", "hi", "thanks", "thank", "great", "good", "yes", "no",
            "what", "where", "who", "when", "how", "please", "sorry",
            "for", "with", "on", "have", "has", "be", "are", "was",
        ],
        "patterns": ["ing", "tion", "ly"],
    },
    "et": {
        "words": [
            "ja", "et", "on", "see", "ei", "ma", "sa", "ta", "mis", "kus",
            "tere", "aitäh", "jah", "ei", "kuidas", "palun", "hästi", "vabandust",
            "tänud", "õnnitud", "olen", "oled", "oleme", "olete",
        ],
        "patterns": ["ne", "le", "se", "ks", "tu", "da"],
    },
    "fi": {
        "words": [
            "ja", "on", "että", "ei", "se", "minä", "sinä", "hän", "mitä",
            "tere", "kiitos", "kyllä", "terve", "paremmin", "hyvä", "ikävä",
            "menee", "kuuluu", "kuulla", "kysymyksestä", "oletko", "kunnossa",
            "sinulle", "minulla", "hyvin", "kaiken", "kaikki",
        ],
        "patterns": ["lla", "lle", "ssa", "yksestä", "llo"],
    },
    "de": {
        "words": [
            "der", "die", "und", "in", "den", "von", "zu", "das", "mit",
            "sich", "des", "auf", "für", "ist", "im", "dem", "hallo",
            "danke", "gut", "ja", "nein", "gestern", "heute", "morgen",
            "wie", "was", "wer", "wo", "wann",
        ],
        "patterns": ["ung", "heit", "keit", "er", "en"],
    },
    "fr": {
        "words": [
            "le", "de", "un", "et", "a", "que", "est", "dans", "ce", "qui",
            "par", "pour", "bonjour", "merci", "oui", "non", "je", "tu",
            "vous", "se", "la", "les", "des", "aux", "au",
        ],
        "patterns": ["tion", "ement", "able", "ure"],
    },
    "ru": {
        "words": [
            "и", "в", "во", "не", "что", "он", "на", "я", "с", "со",
            "он", "а", "то", "все", "она", "так", "его", "но", "да",
        ],
        "patterns": ["ство", "ость", "ение", "ля"],
    },
}

# Configuration
MIN_TEXT_FOR_DETECTION = 50  # Minimum characters for detection
MAX_TEXT_SAMPLE = 10000  # Maximum characters to sample for performance


# ============================================================================
# Language Detector Class
# ============================================================================


class LanguageDetector:
    """Detects the language of subtitle files locally without API calls"""

    def __init__(self):
        """Initialize the language detector"""
        pass

    def _get_display_name(self, language_code: Optional[str]) -> str:
        """
        Get Estonian display name for a language code.

        Args:
            language_code: ISO 639-1 language code (e.g., 'en', 'et')

        Returns:
            Display name or "Teadmata" if unknown
        """
        if language_code is None:
            return "Teadmata"

        # Normalize language code
        code = language_code.lower().strip()
        
        return CODE_TO_DISPLAY.get(code, "Teadmata")

    def sample_subtitle_text(self, file_path: Path) -> str:
        """
        Sample subtitle text from an SRT file for language detection.

        Extracts dialogue text only (no timestamps or sequence numbers).
        Samples up to MAX_TEXT_SAMPLE characters for performance.

        Args:
            file_path: Path to .srt file

        Returns:
            Sampled subtitle text (may be empty if file is invalid)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception:
                return ""

        # Parse SRT file
        blocks = content.strip().split("\n\n")
        subtitle_texts = []

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                # Skip sequence number (lines[0])
                # Skip timecode (lines[1])
                # Subtitle text is everything from lines[2] onwards
                text = "\n".join(lines[2:])

                if text.strip():
                    subtitle_texts.append(text)

                # Stop if we have enough text sampled
                combined = " ".join(subtitle_texts)
                if len(combined) >= MAX_TEXT_SAMPLE:
                    break

            except (ValueError, IndexError):
                continue

        # Combine and return sampled text
        sampled = " ".join(subtitle_texts)
        return sampled[:MAX_TEXT_SAMPLE] if sampled else ""

    def _score_language(self, text: str, language_code: str) -> float:
        """
        Score how likely the text is in a given language.
        
        Uses heuristic-based detection with language-specific word markers
        and character patterns.

        Args:
            text: Text sample to analyze
            language_code: Language code to test

        Returns:
            Confidence score 0.0-1.0
        """
        if language_code not in LANGUAGE_MARKERS:
            return 0.0

        markers = LANGUAGE_MARKERS[language_code]
        text_lower = text.lower()
        text_len = len(text)

        # Score based on language-specific words
        word_score = 0.0
        for word in markers["words"]:
            # Count occurrences of the word as whole word
            count = text_lower.count(word)
            if count > 0:
                word_score += min(0.05, count * 0.01)  # Each match adds up to 0.05

        # Score based on language-specific patterns
        pattern_score = 0.0
        for pattern in markers["patterns"]:
            count = text_lower.count(pattern)
            if count > 0:
                pattern_score += min(0.15, count * 0.01)

        # Combine scores
        total_score = min(1.0, word_score + pattern_score)

        return total_score

    def _detect_language_heuristic(self, text: str) -> Tuple[str, float]:
        """
        Detect language using heuristic analysis.

        Scores the text against multiple known languages and returns
        the language with the highest score.

        Args:
            text: Text sample to analyze

        Returns:
            Tuple of (language_code, confidence) where confidence is 0.0-1.0
        """
        if not text:
            return ("unknown", 0.0)

        scores = {}
        for language_code in LANGUAGE_MARKERS.keys():
            scores[language_code] = self._score_language(text, language_code)

        # Find the best match
        best_lang = max(scores.items(), key=lambda x: x[1])
        language_code, confidence = best_lang

        # If the best score is very low, return unknown
        if confidence < 0.1:
            return ("unknown", 0.0)

        return (language_code, confidence)

    def detect_language_in_file(self, file_path: Path) -> Dict:
        """
        Detect the language of a subtitle file.

        Args:
            file_path: Path to .srt file

        Returns:
            Dict with:
            {
                'file': str (filename),
                'language_code': str (ISO 639-1 code or 'unknown'),
                'display_name': str (Estonian name),
                'confidence': float (0.0-1.0, or 0.0 if unknown),
                'sample_length': int (characters sampled),
                'error': str or None,
            }
        """
        try:
            # Sample text from file
            sample_text = self.sample_subtitle_text(file_path)

            if not sample_text or len(sample_text) < MIN_TEXT_FOR_DETECTION:
                return {
                    "file": file_path.name,
                    "language_code": "unknown",
                    "display_name": "Teadmata",
                    "confidence": 0.0,
                    "sample_length": len(sample_text),
                    "error": f"Insufficient text for detection (need >= {MIN_TEXT_FOR_DETECTION} chars)",
                }

            # Detect language using heuristic analysis
            detected_code, confidence = self._detect_language_heuristic(sample_text)

            # Get display name
            display_name = self._get_display_name(detected_code)

            return {
                "file": file_path.name,
                "language_code": detected_code,
                "display_name": display_name,
                "confidence": confidence,
                "sample_length": len(sample_text),
                "error": None,
            }

        except Exception as e:
            return {
                "file": file_path.name,
                "language_code": "unknown",
                "display_name": "Teadmata",
                "confidence": 0.0,
                "sample_length": 0,
                "error": f"Error reading file: {str(e)}",
            }

    def detect_languages_in_files(self, file_paths: List[Path]) -> List[Dict]:
        """
        Detect languages in multiple files.

        Args:
            file_paths: List of Path objects to .srt files

        Returns:
            List of detection result dicts
        """
        results = []
        for file_path in file_paths:
            result = self.detect_language_in_file(file_path)
            results.append(result)
        return results

    def summarize_detections(self, detections: List[Dict]) -> Dict:
        """
        Summarize language detections for multiple files.

        Args:
            detections: List of detection results

        Returns:
            Dict with:
            {
                'total_files': int,
                'by_language': {language_code: count, ...},
                'by_display_name': {display_name: count, ...},
                'has_estonian': bool,
                'has_english': bool,
                'has_other': bool,
                'all_same': bool,
                'errors': list of error messages,
            }
        """
        by_code = {}
        by_display = {}
        errors = []

        for detection in detections:
            if detection["error"]:
                errors.append(f"{detection['file']}: {detection['error']}")
                continue

            code = detection["language_code"]
            display = detection["display_name"]

            by_code[code] = by_code.get(code, 0) + 1
            by_display[display] = by_display.get(display, 0) + 1

        has_estonian = "et" in by_code or "Eesti" in by_display
        has_english = "en" in by_code or "Inglise" in by_display
        has_other = any(
            code not in ("et", "en", "unknown") for code in by_code.keys()
        )
        all_same = len(by_code) <= 1

        return {
            "total_files": len(detections),
            "by_language": by_code,
            "by_display_name": by_display,
            "has_estonian": has_estonian,
            "has_english": has_english,
            "has_other": has_other,
            "all_same": all_same,
            "errors": errors,
        }

    def format_detection_for_log(self, detection: Dict) -> str:
        """
        Format a single detection result for display in log.

        Args:
            detection: Detection result dict

        Returns:
            Formatted string for display
        """
        if detection["error"]:
            return f"  {detection['file']} — Viga: {detection['error']}"

        return f"  {detection['file']} — {detection['display_name']}"

    def format_detections_for_log(self, detections: List[Dict]) -> str:
        """
        Format multiple detections for display in log.

        Args:
            detections: List of detection results

        Returns:
            Formatted string for display
        """
        lines = ["Keele tuvastamine:"]
        for detection in detections:
            lines.append(self.format_detection_for_log(detection))
        return "\n".join(lines)

    def format_summary_for_log(self, summary: Dict) -> str:
        """
        Format detection summary for display in log.

        For single language, shows simple format.
        For multiple languages, shows breakdown.

        Args:
            summary: Summary dict from summarize_detections()

        Returns:
            Formatted string for display
        """
        if summary["total_files"] == 0:
            return ""

        if summary["all_same"] and not summary["errors"]:
            # Single language
            language = list(summary["by_display_name"].keys())[0]
            if summary["total_files"] == 1:
                return f"Tuvastatud keel: {language}"
            else:
                return f"Tuvastatud keel: {language} ({summary['total_files']} faili)"

        # Multiple languages
        lines = ["Keeled:"]
        for display_name, count in sorted(
            summary["by_display_name"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {display_name}: {count} " + ("fail" if count == 1 else "faili"))

        return "\n".join(lines)
