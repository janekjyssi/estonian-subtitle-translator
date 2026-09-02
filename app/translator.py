"""
Subtitle translation module using OpenAI API
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import re
from app.checkpoint_manager import CheckpointManager


class SubtitleEntry:
    """Represents a single subtitle entry"""

    def __init__(self, seq_number: int, start_time: str, end_time: str, text: str):
        self.seq_number = seq_number
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

    def __repr__(self):
        return f"SubtitleEntry({self.seq_number}, {self.start_time} --> {self.end_time}, {len(self.text)} chars)"


class SRTParser:
    """Parse and write SRT subtitle files"""

    @staticmethod
    def parse_srt(filepath: Path) -> List[SubtitleEntry]:
        """
        Parse an SRT file into subtitle entries

        Args:
            filepath: Path to the .srt file

        Returns:
            List of SubtitleEntry objects
        """
        entries = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()

        # Split by double newline to get subtitle blocks
        blocks = content.strip().split("\n\n")

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                seq_number = int(lines[0].strip())
                timecode = lines[1].strip()

                # Parse timecode: HH:MM:SS,mmm --> HH:MM:SS,mmm
                parts = timecode.split("-->")
                if len(parts) != 2:
                    continue

                start_time = parts[0].strip()
                end_time = parts[1].strip()

                # Subtitle text is everything after the timecode
                text = "\n".join(lines[2:])

                entry = SubtitleEntry(seq_number, start_time, end_time, text)
                entries.append(entry)

            except (ValueError, IndexError):
                continue

        return entries

    @staticmethod
    def write_srt(filepath: Path, entries: List[SubtitleEntry]) -> None:
        """
        Write subtitle entries to an SRT file

        Args:
            filepath: Path to write the .srt file
            entries: List of SubtitleEntry objects
        """
        lines = []

        for entry in entries:
            lines.append(str(entry.seq_number))
            lines.append(f"{entry.start_time} --> {entry.end_time}")
            lines.append(entry.text)
            lines.append("")  # Blank line between entries

        content = "\n".join(lines)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


class OpenAITranslator:
    """Handle translation using OpenAI API"""

    # Model-specific batch sizes for reliability
    MODEL_BATCH_SIZES = {
        "gpt-4.1": 20,
        "gpt-4.1-mini": 8,
        "gpt-5.6-terra": 20,
        "gpt-5.6-luna": 20,
    }
    MAX_RETRIES = 3  # Retry failed batches

    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        """
        Initialize translator with OpenAI API key

        Args:
            api_key: OpenAI API key
            model: The model to use for translation (default: gpt-4.1)
        """
        self.api_key = api_key
        self.model_name = model
        self.client = None
        self.total_input_tokens = 0
        self.total_cached_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

    def get_batch_size(self) -> int:
        """
        Get the batch size for the current model

        Returns:
            Batch size for the model (default: 20 for unknown models)
        """
        return self.MODEL_BATCH_SIZES.get(self.model_name, 20)

    def translate_batch(
        self, entries: List[SubtitleEntry]
    ) -> Tuple[List[SubtitleEntry], Optional[str]]:
        """
        Translate a batch of subtitle entries using structured JSON output

        Args:
            entries: List of SubtitleEntry objects to translate

        Returns:
            Tuple of (translated_entries, error_message)
            On success: (translated_entries, None)
            On error: (empty_list, error_message)
        """
        if not entries:
            return [], None

        # Create structured input with sequence numbers and text
        batch_data = [
            {"id": e.seq_number, "text": e.text} for e in entries
        ]

        # Build prompt that enforces structured JSON output
        prompt = self._build_translation_prompt(batch_data)

        try:
            # Build API call parameters
            api_params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional subtitle translator. "
                            "Translate English subtitles to natural, conversational Estonian. "
                            "Preserve every subtitle entry exactly. "
                            "Preserve speaker names, formatting, and structure. "
                            "Return ONLY valid JSON matching the required format. "
                            "NEVER omit any subtitle text or entries."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "timeout": 60,
            }
            
            response = self.client.chat.completions.create(**api_params)

            response_text = response.choices[0].message.content

            # Track token usage
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                cached_input_tokens = getattr(
                    getattr(response.usage, "prompt_tokens_details", None),
                    "cached_tokens",
                    0,
                ) or 0
                
                self.total_input_tokens += input_tokens
                self.total_cached_input_tokens += cached_input_tokens
                self.total_output_tokens += output_tokens
                self.total_tokens += total_tokens

            # Parse and validate the JSON response
            translated_entries, error = self._parse_and_validate_response(
                response_text, entries, batch_data
            )

            if error:
                return [], error

            return translated_entries, None

        except Exception as e:
            return [], f"Translation API error: {str(e)}"

    def _build_translation_prompt(self, batch_data: List[Dict[str, Any]]) -> str:
        """
        Build the translation prompt with structured JSON input/output

        Args:
            batch_data: List of dicts with 'id' and 'text'

        Returns:
            Formatted prompt for the API
        """
        import json

        batch_json = json.dumps(batch_data, ensure_ascii=False, indent=2)

        prompt = f"""Translate the following English subtitles to Estonian.

IMPORTANT RULES:
1. Preserve EVERY subtitle entry - no omissions or merging
2. Preserve speaker names exactly (MARGE:, HOMER:, etc.)
3. Preserve leading hyphens for multi-speaker lines
4. Preserve HTML tags like <i>...</i> and <b>...</b>
5. Preserve line breaks in multi-line subtitles
6. Preserve musical notes and sound symbols
7. Translate sound descriptions naturally: (laughs) -> (naerab), (clears throat) -> (köhatab)
8. Never lose dialogue text
9. Use natural conversational Estonian, not literal translation
10. Keep character tone and jokes where possible

Input subtitles (JSON):
{batch_json}

Return ONLY this JSON structure with translations:
{{
  "translations": [
    {{"id": <number>, "text": "<translated_text>"}},
    ...same count as input...
  ]
}}

Ensure:
- Every input ID has exactly one translation
- Same number of translations as input
- No empty text if source was not empty"""

        return prompt

    def _parse_and_validate_response(
        self,
        response_text: str,
        original_entries: List[SubtitleEntry],
        batch_data: List[Dict[str, Any]],
    ) -> Tuple[List[SubtitleEntry], Optional[str]]:
        """
        Parse JSON response and validate it matches input

        Args:
            response_text: Raw response from OpenAI API
            original_entries: Original subtitle entries for reference
            batch_data: Original batch data sent to API

        Returns:
            Tuple of (translated_entries, error_message)
        """
        import json

        try:
            # Extract JSON from response
            response_json = self._extract_json_from_response(response_text)
            if not response_json:
                return [], "Failed to extract JSON from response"

            # Parse translations array
            if "translations" not in response_json:
                return [], "Response missing 'translations' array"

            translations_data = response_json["translations"]
            if not isinstance(translations_data, list):
                return [], "translations must be an array"

            # Validate response
            error = self._validate_translations(
                translations_data, batch_data, original_entries
            )
            if error:
                return [], error

            # Build translated entries maintaining order
            translations_dict = {t["id"]: t["text"] for t in translations_data}
            translated_entries = []

            for entry in original_entries:
                translated_text = translations_dict.get(entry.seq_number)
                if translated_text is None:
                    return [], f"Missing translation for entry {entry.seq_number}"

                translated_entry = SubtitleEntry(
                    entry.seq_number,
                    entry.start_time,
                    entry.end_time,
                    translated_text,
                )
                translated_entries.append(translated_entry)

            return translated_entries, None

        except json.JSONDecodeError as e:
            return [], f"Invalid JSON in response: {e}"
        except Exception as e:
            return [], f"Error parsing response: {e}"

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """
        Extract JSON object from response text

        Args:
            response_text: Raw API response text

        Returns:
            Parsed JSON dict or None if not found
        """
        import json

        response_text = response_text.strip()

        # Try direct parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                try:
                    return json.loads(response_text[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try extracting JSON object between { and }
        start = response_text.find("{")
        if start >= 0:
            end = response_text.rfind("}")
            if end > start:
                try:
                    return json.loads(response_text[start : end + 1])
                except json.JSONDecodeError:
                    pass

        return None

    def _validate_translations(
        self,
        translations_data: List[Dict[str, Any]],
        batch_data: List[Dict[str, Any]],
        original_entries: List[SubtitleEntry],
    ) -> Optional[str]:
        """
        Validate that response contains all required translations

        Args:
            translations_data: Parsed translations from response
            batch_data: Original input batch
            original_entries: Original subtitle entries

        Returns:
            Error message if validation fails, None if valid
        """
        # Check count matches
        if len(translations_data) != len(batch_data):
            return f"Entry count mismatch: expected {len(batch_data)}, got {len(translations_data)}"

        # Check all required IDs are present
        input_ids = {b["id"] for b in batch_data}
        response_ids = {t["id"] for t in translations_data}

        missing_ids = input_ids - response_ids
        if missing_ids:
            return f"Missing translations for IDs: {missing_ids}"

        extra_ids = response_ids - input_ids
        if extra_ids:
            return f"Unexpected IDs in response: {extra_ids}"

        # Check for duplicate IDs
        response_id_list = [t["id"] for t in translations_data]
        if len(response_id_list) != len(set(response_id_list)):
            return "Duplicate IDs in response"

        # Check translated texts are not empty for non-empty originals
        original_text_by_id = {e.seq_number: e.text for e in original_entries}
        for t in translations_data:
            entry_id = t["id"]
            original_text = original_text_by_id.get(entry_id, "")
            translated_text = t.get("text", "")

            if original_text.strip() and not translated_text.strip():
                return f"Lost dialogue in entry {entry_id}: original had text but translation is empty"

            if not isinstance(translated_text, str):
                return f"Invalid text type in entry {entry_id}"

        return None

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get accumulated token usage statistics

        Returns:
            Dict with 'input_tokens', 'output_tokens', 'total_tokens'
        """
        return {
            "input_tokens": self.total_input_tokens,
            "cached_input_tokens": self.total_cached_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset_token_usage(self):
        """Reset token usage counters"""
        self.total_input_tokens = 0
        self.total_cached_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0


class TranslationWorker:
    """Orchestrates subtitle file translation"""

    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        """
        Initialize translation worker

        Args:
            api_key: OpenAI API key
            model: The model to use for translation (default: gpt-4.1)
        """
        self.api_key = api_key
        self.model = model
        self.translator = None
        self._initialize_translator()

    def _initialize_translator(self):
        """Initialize the OpenAI translator"""
        self.translator = OpenAITranslator(self.api_key, self.model)

    def translate_file(
        self, en_srt_path: Path, callback_log=None, auto_delete_source=True,
        checkpoint: Optional[Dict[str, Any]] = None, resume_mode: str = "new"
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Translate an English SRT file to Estonian

        Args:
            en_srt_path: Path to the .srt file
            callback_log: Optional callback function for logging
            auto_delete_source: If True, delete source file after successful translation
            checkpoint: Optional checkpoint data for resuming (from CheckpointManager.load_checkpoint)
            resume_mode: "new", "resume", or "restart"
                - "new": Start fresh, no checkpoint
                - "resume": Continue from checkpoint
                - "restart": Ignore checkpoint and start over

        Returns:
            Tuple of (success: bool, message: str, output_path: Optional[Path])
        """
        # Determine output filename
        output_path = self._get_output_path(en_srt_path)

        if output_path is None:
            return False, "Otsusta väljundfaili nime määramise viga", None

        # Skip if output file is the input file (already Estonian)
        if output_path == en_srt_path:
            return False, "Fail on juba eestikeelne (.et.srt)", None

        # Check if output already exists
        if output_path.exists():
            return False, "Juba olemas", None

        # Parse the source file
        try:
            entries = SRTParser.parse_srt(en_srt_path)
            if not entries:
                return False, "Ei saanud SRT faili parsida", None
        except Exception as e:
            return False, f"SRT parsimise viga: {e}", None

        # Determine resume mode based on parameters
        resuming = resume_mode == "resume" and checkpoint is not None
        
        # Initialize translation tracking
        translated_entries = []
        completed_batches_set = set()
        start_from_batch_idx = 0
        skip_entry_ids = set()  # Track which entries were already translated
        
        # Restore from checkpoint if resuming
        if resuming:
            if callback_log:
                callback_log(f"  Jätkan pooleli jäänud tõlkest...")
            
            # Restore already translated entries
            stored_entries = checkpoint.get("translated_entries", {})
            for seq_num_str, translated_text in stored_entries.items():
                seq_num = int(seq_num_str)
                skip_entry_ids.add(seq_num)
                
                # Find the original entry to get timing info
                for entry in entries:
                    if entry.seq_number == seq_num:
                        # Create a new entry with translated text
                        translated_entry = SubtitleEntry(
                            seq_num,
                            entry.start_time,
                            entry.end_time,
                            translated_text
                        )
                        translated_entries.append(translated_entry)
                        break
            
            # Restore token usage
            token_usage = checkpoint.get("token_usage", {})
            self.translator.total_input_tokens = token_usage.get("input", 0)
            self.translator.total_cached_input_tokens = token_usage.get("cached_input", 0)
            self.translator.total_output_tokens = token_usage.get("output", 0)
            
            # Determine which batches need to be completed
            completed_batches_set = set(checkpoint.get("progress", {}).get("completed_batches", []))
            batch_size = self.translator.get_batch_size()
            total_batches = (len(entries) + batch_size - 1) // batch_size
            
            # Find first incomplete batch (0-indexed)
            for i in range(total_batches):
                if i not in completed_batches_set:
                    start_from_batch_idx = i
                    break
            
            if callback_log:
                completed_count = len(completed_batches_set)
                callback_log(f"  Jätkan plokist {start_from_batch_idx + 1} / {total_batches} (valmis: {completed_count} / {total_batches})")
        
        # Translate in batches with intelligent splitting
        if not resuming:
            translated_entries = []
        
        batch_size = self.translator.get_batch_size()
        batch_num = 0
        total_batches = (len(entries) + batch_size - 1) // batch_size

        # Call _process_batches to translate remaining batches
        success = self._process_batches(
            entries,
            0 if not resuming else start_from_batch_idx * batch_size,
            batch_size,
            0 if not resuming else start_from_batch_idx,
            total_batches,
            translated_entries,
            callback_log,
            source_path=en_srt_path,
            model_id=self.model,
            total_batches_for_checkpoint=total_batches,
        )

        if not success:
            return (
                False,
                f"Tõlkimise katsed ebaõnnestusid pärast korduvaid katsetest",
                None,
            )

        # Sort translated entries by sequence number (important when resuming)
        translated_entries.sort(key=lambda e: e.seq_number)

        # Save translated file
        try:
            SRTParser.write_srt(output_path, translated_entries)
        except Exception as e:
            return False, f"Faili salvestamise viga: {e}", None

        # Delete checkpoint after successful completion
        checkpoint_success, checkpoint_msg = CheckpointManager.delete_checkpoint(en_srt_path)
        if callback_log and checkpoint_success:
            callback_log(f"✓ {checkpoint_msg}")

        # Delete source file if requested and translation was successful
        if auto_delete_source and en_srt_path != output_path:
            try:
                en_srt_path.unlink()
                if callback_log:
                    callback_log(f"  Ingliskeelne subtiiter kustutatud: {en_srt_path.name}")
            except Exception as e:
                # Log warning but don't fail the translation
                if callback_log:
                    callback_log(f"  ⚠ Hoiatus: Ei saanud kustutada {en_srt_path.name}: {e}")
        
        # Log backup preservation
        from app.backup_manager import BackupManager
        backup_filename = BackupManager.get_backup_filename(en_srt_path)
        backup_path = en_srt_path.parent / backup_filename
        if backup_path.exists() and callback_log:
            callback_log(f"✓ Originaali varukoopia säilitatud: {backup_filename}")

        return True, str(output_path), output_path

    def _process_batches(
        self,
        entries: List[SubtitleEntry],
        start_idx: int,
        batch_size: int,
        batch_num: int,
        total_batches: int,
        translated_entries: List[SubtitleEntry],
        callback_log=None,
        source_path: Optional[Path] = None,
        model_id: Optional[str] = None,
        total_batches_for_checkpoint: Optional[int] = None,
    ) -> bool:
        """
        Recursively process batches with intelligent splitting on failures

        Args:
            entries: All source entries
            start_idx: Starting index in entries list
            batch_size: Current batch size
            batch_num: Current batch number (1-indexed for display)
            total_batches: Total number of batches
            translated_entries: List to accumulate translated entries
            callback_log: Optional logging callback
            source_path: Path to source file (for checkpoint saving)
            model_id: Model ID (for checkpoint saving)
            total_batches_for_checkpoint: Total number of batches (for checkpoint)

        Returns:
            True if all batches translated successfully, False otherwise
        """
        if start_idx >= len(entries):
            return True

        # Calculate batch range
        end_idx = min(start_idx + batch_size, len(entries))
        batch = entries[start_idx:end_idx]
        batch_num += 1

        if callback_log:
            callback_log(f"  Partii {batch_num}/{total_batches} – {len(batch)} subtiitrit")

        # Try to translate batch with retries
        for attempt in range(self.translator.MAX_RETRIES):
            result_entries, error = self.translator.translate_batch(batch)

            if error is None:
                translated_entries.extend(result_entries)
                if callback_log:
                    callback_log(f"  ✓ Partii {batch_num} valmis")
                
                # Save checkpoint after each successful batch
                if source_path and model_id and total_batches_for_checkpoint:
                    # Build translated entries dictionary
                    translated_dict = {}
                    for entry in translated_entries:
                        translated_dict[str(entry.seq_number)] = entry.text
                    
                    # Determine which batches are complete
                    completed_batches = list(range(batch_num))  # 0-indexed: 0 to batch_num-1
                    
                    checkpoint_ok, checkpoint_msg = CheckpointManager.create_checkpoint(
                        source_path,
                        model_id,
                        total_batches_for_checkpoint,
                        completed_batches,
                        translated_dict,
                        self.translator.total_input_tokens,
                        self.translator.total_output_tokens,
                    )
                
                # Continue to next batch
                return self._process_batches(
                    entries,
                    end_idx,
                    batch_size,
                    batch_num,
                    total_batches,
                    translated_entries,
                    callback_log,
                    source_path=source_path,
                    model_id=model_id,
                    total_batches_for_checkpoint=total_batches_for_checkpoint,
                )
            elif attempt < self.translator.MAX_RETRIES - 1:
                # Log retry attempt
                if callback_log:
                    # Extract entry count from error if possible
                    if "Entry count mismatch" in error:
                        parts = error.split("expected")
                        if len(parts) > 1:
                            expected = parts[1].strip().split(",")[0]
                            got = error.split("got")[-1].strip()
                            callback_log(f"  ⚠ Partii {batch_num}: saadi {got}/{expected} kirjet – uus katse")
                        else:
                            callback_log(f"  ⚠ Partii {batch_num}: {error} – uus katse")
                    else:
                        callback_log(f"  ⚠ Partii {batch_num}: {error} – uus katse")

        # If we get here, batch failed after all retries
        # Try splitting the batch into smaller pieces
        if len(batch) > 1:
            if callback_log:
                callback_log(f"  ⚠ Partii {batch_num} jagatakse väiksemateks osadeks")

            # Split batch in half
            smaller_batch_size = max(1, len(batch) // 2)

            # Process the split batches
            return self._process_batches(
                batch,
                0,
                smaller_batch_size,
                0,  # Reset batch numbering for sub-batches
                (len(batch) + smaller_batch_size - 1) // smaller_batch_size,
                translated_entries,
                callback_log,
                source_path=source_path,
                model_id=model_id,
                total_batches_for_checkpoint=total_batches_for_checkpoint,
            ) and self._process_batches(
                entries,
                end_idx,
                batch_size,
                batch_num,
                total_batches,
                translated_entries,
                callback_log,
                source_path=source_path,
                model_id=model_id,
                total_batches_for_checkpoint=total_batches_for_checkpoint,
            )
        else:
            # Single entry batch still failing - this is a hard failure
            if callback_log:
                callback_log(f"  ✗ Üksik kirje {batch[0].seq_number} tõlkimise katsed ebaõnnestusid")
            return False

    def _get_output_path(self, input_path: Path) -> Optional[Path]:
        """
        Determine the output path for a subtitle file

        Args:
            input_path: Path to input subtitle file

        Returns:
            Path to output .et.srt file or None if path is invalid
        """
        try:
            # If filename contains .en.srt, replace with .et.srt
            if ".en.srt" in input_path.name:
                output_name = input_path.name.replace(".en.srt", ".et.srt")
            # If filename is .et.srt, return None (already Estonian)
            elif input_path.name.endswith(".et.srt"):
                return None
            # If filename is .srt, add .et. before .srt
            elif input_path.name.endswith(".srt"):
                output_name = input_path.name.replace(".srt", ".et.srt")
            else:
                return None

            return input_path.parent / output_name
        except Exception:
            return None

    def get_model_name(self) -> str:
        """Get the current model name"""
        return OpenAITranslator.MODEL_NAME

    def get_batch_size(self) -> int:
        """Get the current batch size"""
        return OpenAITranslator.BATCH_SIZE

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get accumulated token usage from translator

        Returns:
            Dict with 'input_tokens', 'output_tokens', 'total_tokens'
        """
        if self.translator:
            return self.translator.get_token_usage()
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def reset_token_usage(self):
        """Reset token usage counters"""
        if self.translator:
            self.translator.reset_token_usage()
