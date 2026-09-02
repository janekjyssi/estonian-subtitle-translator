"""
Checkpoint manager for interrupted translation resume

Handles checkpoint creation, validation, and restore for translation resumption:
- Saves progress after each batch
- Stores source file identity (path, hash)
- Stores model and translation progress
- Validates source file hasn't changed before resuming
- Detects model mismatches
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime


class CheckpointManager:
    """Manages checkpoint creation and resume for translations"""

    CHECKPOINT_SUFFIX = ".translation_progress.json"

    @staticmethod
    def get_checkpoint_filename(source_path: Path) -> str:
        """
        Get the checkpoint filename for a source file.

        Args:
            source_path: Path to source file

        Returns:
            Checkpoint filename (not full path)
        """
        return f"{source_path.name}{CheckpointManager.CHECKPOINT_SUFFIX}"

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def create_checkpoint(
        source_path: Path,
        model_id: str,
        total_batches: int,
        completed_batches: List[int],
        translated_entries: Dict[int, str],  # {seq_number: translated_text}
        total_input_tokens: int,
        total_output_tokens: int,
    ) -> Tuple[bool, str]:
        """
        Create or update a checkpoint for a translation.

        Args:
            source_path: Path to source file being translated
            model_id: Model ID used for translation
            total_batches: Total number of batches
            completed_batches: List of batch indexes that completed (0-indexed)
            translated_entries: Dict mapping entry sequence numbers to translated text
            total_input_tokens: Total input tokens used so far
            total_output_tokens: Total output tokens used so far

        Returns:
            Tuple of (success: bool, message: str)
        """
        checkpoint_filename = CheckpointManager.get_checkpoint_filename(source_path)
        checkpoint_path = source_path.parent / checkpoint_filename

        checkpoint_data = {
            "version": 1,
            "timestamp": datetime.now().isoformat(),
            "source_file": {
                "path": str(source_path),
                "name": source_path.name,
                "size": source_path.stat().st_size,
                "hash": CheckpointManager.compute_file_hash(source_path),
            },
            "model": {
                "id": model_id,
            },
            "progress": {
                "total_batches": total_batches,
                "completed_batches": sorted(set(completed_batches)),
                "completed_count": len(set(completed_batches)),
            },
            "translated_entries": translated_entries,
            "token_usage": {
                "input": total_input_tokens,
                "output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens,
            },
        }

        # Write to temporary file first (atomic write safety)
        temp_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
            # Atomic rename
            temp_path.replace(checkpoint_path)
            return True, f"Kontrolmpunkt salvestatud"

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False, f"Viga: Kontrolmpunkti salvestamine ebaõnnestus: {e}"

    @staticmethod
    def load_checkpoint(source_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint for a source file.

        Args:
            source_path: Path to source file

        Returns:
            Checkpoint data dict if valid checkpoint exists, None otherwise
        """
        checkpoint_filename = CheckpointManager.get_checkpoint_filename(source_path)
        checkpoint_path = source_path.parent / checkpoint_filename

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
            return checkpoint_data
        except Exception:
            return None

    @staticmethod
    def validate_checkpoint(source_path: Path, checkpoint: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that a checkpoint is still valid for the source file.

        Checks:
        - Source file hasn't been modified (hash matches)
        - Source file size matches

        Args:
            source_path: Path to source file
            checkpoint: Checkpoint data

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if not checkpoint:
            return False, "Kontrolmpunkt ei eksisteeri"

        try:
            # Check source file exists
            if not source_path.exists():
                return False, f"Algne subtiitrifail ei ole enam olemas: {source_path.name}"

            # Get source file info
            current_size = source_path.stat().st_size
            current_hash = CheckpointManager.compute_file_hash(source_path)

            # Check size and hash haven't changed
            stored_size = checkpoint.get("source_file", {}).get("size")
            stored_hash = checkpoint.get("source_file", {}).get("hash")

            if stored_size != current_size or stored_hash != current_hash:
                return (
                    False,
                    "Algset subtiitrifaili on pärast tõlkimise alustamist muudetud. "
                    "Pooleli jäänud tõlget ei saa turvaliselt jätkata.",
                )

            return True, "Kontrolmpunkt on kehtiv"

        except Exception as e:
            return False, f"Viga kontrolmpunkti valideerimisel: {e}"

    @staticmethod
    def check_model_mismatch(
        checkpoint: Dict[str, Any], current_model_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if the checkpoint was created with a different model.

        Args:
            checkpoint: Checkpoint data
            current_model_id: Currently selected model ID

        Returns:
            Tuple of (has_mismatch: bool, checkpoint_model_id: Optional[str])
        """
        if not checkpoint:
            return False, None

        checkpoint_model = checkpoint.get("model", {}).get("id")

        if checkpoint_model and checkpoint_model != current_model_id:
            return True, checkpoint_model

        return False, None

    @staticmethod
    def delete_checkpoint(source_path: Path) -> Tuple[bool, str]:
        """
        Delete the checkpoint file.

        Args:
            source_path: Path to source file

        Returns:
            Tuple of (success: bool, message: str)
        """
        checkpoint_filename = CheckpointManager.get_checkpoint_filename(source_path)
        checkpoint_path = source_path.parent / checkpoint_filename

        if not checkpoint_path.exists():
            return True, f"Kontrolmpunkt juba kaustutatud"

        try:
            checkpoint_path.unlink()
            return True, f"Kontrolmpunkt kaustutatud: {checkpoint_filename}"
        except Exception as e:
            return False, f"Viga kontrolmpunkti kustutamisel: {e}"

    @staticmethod
    def get_progress_summary(checkpoint: Dict[str, Any]) -> str:
        """
        Get a human-readable progress summary from a checkpoint.

        Args:
            checkpoint: Checkpoint data

        Returns:
            Progress summary string
        """
        if not checkpoint:
            return "Kontrolmpunkti andmeid pole"

        progress = checkpoint.get("progress", {})
        completed = progress.get("completed_count", 0)
        total = progress.get("total_batches", 0)

        return f"Valmis: {completed} / {total} plokki"

    @staticmethod
    def get_checkpoint_info_for_dialog(
        source_path: Path, checkpoint: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Get information for displaying in resume dialog.

        Args:
            source_path: Path to source file
            checkpoint: Checkpoint data

        Returns:
            Dict with dialog information
        """
        progress = checkpoint.get("progress", {})
        completed = progress.get("completed_count", 0)
        total = progress.get("total_batches", 0)
        model = checkpoint.get("model", {}).get("id", "teadmata")
        timestamp = checkpoint.get("timestamp", "")

        return {
            "file": source_path.name,
            "progress": f"Valmis: {completed} / {total} plokki",
            "model": model,
            "timestamp": timestamp,
        }
