"""
Cost estimation module for API requests before translation starts.

Provides local token counting and cost estimation without making API calls.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json


# ============================================================================
# CONFIGURATION - Cost Estimation Parameters
# ============================================================================

# Token ratio estimates for output based on input
# These represent the approximate relationship between input and output tokens
# for English -> Estonian subtitle translation
TOKEN_RATIO_CONFIG = {
    "low": 0.65,          # Conservative estimate (output tokens)
    "expected": 0.75,     # Expected estimate (output tokens)
    "high": 0.90,         # Liberal estimate (output tokens)
}

# Prompt overhead tokens per batch
# This accounts for system messages, instructions, JSON structure, etc.
# that are sent with each batch request
PROMPT_OVERHEAD_TOKENS_PER_BATCH = 500

# ============================================================================
# Main Estimator Class
# ============================================================================


class CostEstimator:
    """Estimates API costs for subtitle translation without making API calls"""

    def __init__(self):
        """Initialize the cost estimator (lazy load tiktoken)"""
        self.tokenizer = None
        self._tokenizer_initialized = False

    def _ensure_tokenizer(self) -> bool:
        """
        Lazy-load tiktoken tokenizer on first use.
        
        Returns:
            True if tokenizer loaded successfully, False if tiktoken not available
        """
        if self._tokenizer_initialized:
            return self.tokenizer is not None

        try:
            import tiktoken
            # Use the same encoding as GPT models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self._tokenizer_initialized = True
            return True
        except ImportError:
            self._tokenizer_initialized = True
            self.tokenizer = None
            return False

    def count_tokens_in_text(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Falls back to character-based estimate if tiktoken not available.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        if not self._ensure_tokenizer():
            # Fallback: rough estimate of ~4 characters per token
            return max(1, len(text) // 4)

        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception:
            # Fallback on error
            return max(1, len(text) // 4)

    def estimate_file_tokens(self, file_path: Path) -> Dict[str, int]:
        """
        Estimate token count for an SRT file.
        
        Parses subtitle text only (no timestamps or sequence numbers).
        
        Args:
            file_path: Path to .srt file
            
        Returns:
            Dict with 'text_tokens' and 'entry_count'
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        # Parse SRT file
        blocks = content.strip().split("\n\n")
        subtitle_texts = []
        entry_count = 0

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
                    entry_count += 1
            except (ValueError, IndexError):
                continue

        # Count tokens in all subtitle text combined
        combined_text = "\n".join(subtitle_texts)
        text_tokens = self.count_tokens_in_text(combined_text)

        return {
            "text_tokens": text_tokens,
            "entry_count": entry_count,
        }

    def estimate_cost(
        self,
        files: List[Path],
        model_config: Dict,
    ) -> Dict:
        """
        Estimate API cost for translating multiple files.
        
        Args:
            files: List of .srt file paths to estimate
            model_config: Model configuration dict with:
                - 'input_price': price per 1M input tokens
                - 'output_price': price per 1M output tokens
                - 'batch_size': how many entries per batch
                
        Returns:
            Dict with comprehensive cost estimate:
            {
                'files': int,
                'total_entries': int,
                'total_text_tokens': int,
                'estimated_batches': int,
                'estimated_input_tokens': int,
                'estimated_output_tokens_low': int,
                'estimated_output_tokens_expected': int,
                'estimated_output_tokens_high': int,
                'estimated_cost_low': float,
                'estimated_cost_expected': float,
                'estimated_cost_high': float,
                'error': Optional[str],
            }
        """
        if not files:
            return {
                "files": 0,
                "total_entries": 0,
                "total_text_tokens": 0,
                "estimated_batches": 0,
                "estimated_input_tokens": 0,
                "estimated_output_tokens_low": 0,
                "estimated_output_tokens_expected": 0,
                "estimated_output_tokens_high": 0,
                "estimated_cost_low": 0.0,
                "estimated_cost_expected": 0.0,
                "estimated_cost_high": 0.0,
                "error": None,
            }

        total_entries = 0
        total_text_tokens = 0

        # Process each file
        for file_path in files:
            try:
                file_estimate = self.estimate_file_tokens(Path(file_path))
                total_entries += file_estimate["entry_count"]
                total_text_tokens += file_estimate["text_tokens"]
            except Exception as e:
                return {
                    "files": len(files),
                    "total_entries": 0,
                    "total_text_tokens": 0,
                    "estimated_batches": 0,
                    "estimated_input_tokens": 0,
                    "estimated_output_tokens_low": 0,
                    "estimated_output_tokens_expected": 0,
                    "estimated_output_tokens_high": 0,
                    "estimated_cost_low": 0.0,
                    "estimated_cost_expected": 0.0,
                    "estimated_cost_high": 0.0,
                    "error": f"Error parsing file {file_path.name}: {str(e)}",
                }

        # Calculate number of batches
        batch_size = model_config.get("batch_size", 20)
        estimated_batches = max(1, (total_entries + batch_size - 1) // batch_size)

        # Calculate total input tokens including prompt overhead
        prompt_overhead = estimated_batches * PROMPT_OVERHEAD_TOKENS_PER_BATCH
        estimated_input_tokens = total_text_tokens + prompt_overhead

        # Estimate output tokens based on configurable ratios
        estimated_output_tokens_low = int(
            total_text_tokens * TOKEN_RATIO_CONFIG["low"]
        )
        estimated_output_tokens_expected = int(
            total_text_tokens * TOKEN_RATIO_CONFIG["expected"]
        )
        estimated_output_tokens_high = int(
            total_text_tokens * TOKEN_RATIO_CONFIG["high"]
        )

        # Calculate costs
        input_price = model_config.get("input_price", 0)
        output_price = model_config.get("output_price", 0)

        input_cost = (estimated_input_tokens / 1_000_000) * input_price

        output_cost_low = (
            (estimated_output_tokens_low / 1_000_000) * output_price
        )
        output_cost_expected = (
            (estimated_output_tokens_expected / 1_000_000) * output_price
        )
        output_cost_high = (
            (estimated_output_tokens_high / 1_000_000) * output_price
        )

        estimated_cost_low = round(input_cost + output_cost_low, 4)
        estimated_cost_expected = round(input_cost + output_cost_expected, 4)
        estimated_cost_high = round(input_cost + output_cost_high, 4)

        return {
            "files": len(files),
            "total_entries": total_entries,
            "total_text_tokens": total_text_tokens,
            "estimated_batches": estimated_batches,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens_low": estimated_output_tokens_low,
            "estimated_output_tokens_expected": estimated_output_tokens_expected,
            "estimated_output_tokens_high": estimated_output_tokens_high,
            "estimated_cost_low": estimated_cost_low,
            "estimated_cost_expected": estimated_cost_expected,
            "estimated_cost_high": estimated_cost_high,
            "error": None,
        }

    def format_cost_estimate(
        self,
        estimate: Dict,
        model_display_name: str,
    ) -> str:
        """
        Format cost estimate for display in GUI/log.
        
        Args:
            estimate: Result dict from estimate_cost()
            model_display_name: Human-readable model name
            
        Returns:
            Formatted string for display
        """
        if estimate["error"]:
            return f"HINNAPROGNOOS - VIGA\n{estimate['error']}"

        lines = []
        lines.append("\nHINNAPROGNOOS")
        lines.append("=" * 60)
        lines.append(f"Mudel: {model_display_name}")
        lines.append(f"Faile: {estimate['files']}")
        lines.append(f"Subtiitriplokke: {estimate['total_entries']}")
        lines.append("")

        lines.append("Hinnanguline sisend:")
        lines.append(f"  {estimate['estimated_input_tokens']:,} tokenit")
        lines.append(f"  (teksti: {estimate['total_text_tokens']:,} + pea: {estimate['estimated_input_tokens'] - estimate['total_text_tokens']:,})")
        lines.append("")

        lines.append("Hinnanguline väljund:")
        lines.append(
            f"  madal: {estimate['estimated_output_tokens_low']:,} tokenit"
        )
        lines.append(
            f"  umbes: {estimate['estimated_output_tokens_expected']:,} tokenit"
        )
        lines.append(
            f"  kõrge: {estimate['estimated_output_tokens_high']:,} tokenit"
        )
        lines.append("")

        lines.append("Prognoositav API kulu:")
        lines.append(f"  umbes ${estimate['estimated_cost_expected']:.4f}")
        lines.append(
            f"  tõenäoline vahemik: ${estimate['estimated_cost_low']:.4f}–${estimate['estimated_cost_high']:.4f}"
        )
        lines.append("")
        
        if estimate["files"] > 1:
            avg_cost = estimate["estimated_cost_expected"] / estimate["files"]
            lines.append(f"Keskmiselt faili kohta: umbes ${avg_cost:.4f}")
            lines.append("")

        lines.append("NB! Tegemist on hinnanguga.")
        lines.append("Tegelik kulu kuvatakse pärast tõlkimist tegelike tokenite põhjal.")
        lines.append("=" * 60)

        return "\n".join(lines)
