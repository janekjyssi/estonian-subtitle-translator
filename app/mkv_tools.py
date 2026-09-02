"""
MKV file handling tools module
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any


class SubtitleTrack:
    """Represents a subtitle track in an MKV file"""

    def __init__(self, track_id: int, language: str, codec: str, name: str = ""):
        self.track_id = track_id
        self.language = language
        self.codec = codec
        self.name = name
        self.is_forced = False
        self.is_commentary = False
        self.is_sdh = False

    def __str__(self):
        flags = []
        if self.is_forced:
            flags.append("forced")
        if self.is_commentary:
            flags.append("commentary")
        if self.is_sdh:
            flags.append("SDH")

        flag_str = f" ({', '.join(flags)})" if flags else ""
        name_str = f" - {self.name}" if self.name else ""
        return f"Track {self.track_id}: {self.language} ({self.codec}){name_str}{flag_str}"

    def quality_score(self) -> int:
        """
        Return a score for this subtitle track.
        Higher score = better for processing.
        Used to find the best English subtitle.
        """
        score = 0

        # Prefer normal tracks over special tracks
        if self.is_commentary:
            score -= 1000
        if self.is_forced:
            score -= 500
        if self.is_sdh:
            score -= 100

        return score


class MKVInfo:
    """Information about an MKV file's subtitle tracks"""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.filename = self.filepath.name
        self.subtitles: List[SubtitleTrack] = []
        self.error: Optional[str] = None

    def get_best_english_track(self) -> Optional[SubtitleTrack]:
        """
        Find the best English subtitle track.
        Prefers normal full subtitles over forced/commentary/SDH.
        Falls back to SDH if no normal tracks available.
        """
        english_tracks = [s for s in self.subtitles if s.language.lower().startswith("eng")]

        if not english_tracks:
            return None

        # Sort by quality score (higher is better)
        english_tracks.sort(key=lambda t: t.quality_score(), reverse=True)
        return english_tracks[0]

    def has_english_subtitles(self) -> bool:
        """Check if this MKV has any English subtitles"""
        return self.get_best_english_track() is not None


class MKVTools:
    """Handle MKV file operations"""

    # SRT-compatible subtitle codecs
    SRT_COMPATIBLE_CODECS = {"subrip", "srt", "text/plain"}

    def __init__(self, tools_dir: Optional[Path] = None):
        """
        Initialize MKV tools

        Args:
            tools_dir: Path to tools directory containing mkvtoolnix folder.
                      Defaults to 'tools' folder relative to project root.
        """
        if tools_dir is None:
            # Default to tools folder relative to project root
            project_root = Path(__file__).parent.parent
            tools_dir = project_root / "tools"

        self.tools_dir = Path(tools_dir)
        self.mkvmerge_path = self.tools_dir / "mkvtoolnix" / "mkvmerge.exe"
        self.mkvextract_path = self.tools_dir / "mkvtoolnix" / "mkvextract.exe"
        self.mkvmerge_available = self.mkvmerge_path.exists()
        self.mkvextract_available = self.mkvextract_path.exists()

    def get_error_message(self) -> Optional[str]:
        """Get error message if mkvmerge.exe is not available"""
        if not self.mkvmerge_available:
            return (
                f"Viga: mkvmerge.exe ei leitud asukohast: {self.mkvmerge_path}\n"
                f"Palun installige MKVToolNix ja kopeerige mkvmerge.exe "
                f"kausta: tools/mkvtoolnix/"
            )
        return None

    def identify_subtitles(self, mkv_file: Path) -> MKVInfo:
        """
        Identify subtitle tracks in an MKV file using mkvmerge -J

        Args:
            mkv_file: Path to the MKV file

        Returns:
            MKVInfo object with detected subtitles or error information
        """
        info = MKVInfo(str(mkv_file))

        if not self.mkvmerge_available:
            info.error = f"mkvmerge.exe not found at {self.mkvmerge_path}"
            return info

        try:
            # Run mkvmerge with JSON output
            result = subprocess.run(
                [str(self.mkvmerge_path), "-J", str(mkv_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                info.error = f"mkvmerge failed: {result.stderr}"
                return info

            # Parse JSON output
            data = json.loads(result.stdout)

            # Extract subtitle tracks
            if "tracks" in data:
                for track in data["tracks"]:
                    if track.get("type") == "subtitles":
                        subtitle = self._parse_subtitle_track(track)
                        info.subtitles.append(subtitle)

            return info

        except subprocess.TimeoutExpired:
            info.error = "mkvmerge timeout while processing file"
            return info
        except json.JSONDecodeError as e:
            info.error = f"Failed to parse mkvmerge output: {e}"
            return info
        except Exception as e:
            info.error = f"Error identifying subtitles: {e}"
            return info

    def _parse_subtitle_track(self, track_data: Dict[str, Any]) -> SubtitleTrack:
        """
        Parse a subtitle track from mkvmerge JSON output

        Args:
            track_data: Dictionary containing track information

        Returns:
            SubtitleTrack object
        """
        track_id = track_data.get("id", -1)
        properties = track_data.get("properties", {})

        language = properties.get("language", "unknown")
        codec = track_data.get("codec", "unknown")
        name = properties.get("track_name", "")

        subtitle = SubtitleTrack(track_id, language, codec, name)

        # Check for special track types
        if properties.get("forced_track"):
            subtitle.is_forced = True

        if properties.get("hearing_impaired"):
            subtitle.is_sdh = True

        # Check if it's a commentary track (by name or properties)
        track_name_lower = (name or "").lower()
        if "commentary" in track_name_lower or properties.get("comment"):
            subtitle.is_commentary = True

        return subtitle

    def is_codec_srt_compatible(self, codec: str) -> bool:
        """
        Check if a subtitle codec is compatible with SRT format

        Args:
            codec: The codec name from mkvmerge

        Returns:
            True if the codec can be extracted as SRT, False otherwise
        """
        codec_lower = codec.lower()
        return any(
            compatible in codec_lower for compatible in self.SRT_COMPATIBLE_CODECS
        )

    def extract_subtitle(self, mkv_file: Path, subtitle_track: SubtitleTrack) -> tuple[bool, str]:
        """
        Extract subtitle track from MKV file to .en.srt format

        Args:
            mkv_file: Path to the MKV file
            subtitle_track: The SubtitleTrack object to extract

        Returns:
            Tuple of (success: bool, filepath_or_error_msg: str)
            On success: (True, output_file_path)
            On error: (False, error_message)
        """
        if not self.mkvextract_available:
            return False, f"mkvextract.exe not found at {self.mkvextract_path}"

        # Check codec compatibility
        if not self.is_codec_srt_compatible(subtitle_track.codec):
            return (
                False,
                f"Subtiitri kodek ei ole SRT-iga ühilduv: {subtitle_track.codec}",
            )

        # Generate output filename
        mkv_path = Path(mkv_file)
        output_file = mkv_path.with_name(mkv_path.stem + ".en.srt")

        # Check if file already exists
        if output_file.exists():
            return False, f"Juba olemas"

        try:
            # Run mkvextract with format specification
            # Format: mkvextract <file> tracks <track_id>:<output_file>
            result = subprocess.run(
                [
                    str(self.mkvextract_path),
                    str(mkv_file),
                    "tracks",
                    f"{subtitle_track.track_id}:{str(output_file)}",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Tundmatu viga"
                return False, f"Ekstraheerimine ebaõnnestus: {error_msg}"

            # Verify the file was created
            if not output_file.exists():
                return False, "Väljundfaili ei loodud"

            return True, str(output_file)

        except subprocess.TimeoutExpired:
            return False, "Ekstraheerimine aegusin väljas"
        except Exception as e:
            return False, f"Viga ekstraheerimisel: {e}"


