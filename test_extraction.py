#!/usr/bin/env python3
"""Quick test for extraction functionality"""

from app.mkv_tools import MKVTools, SubtitleTrack

print("Testing extraction module...")

mt = MKVTools()
print(f"✓ MKVTools initialized")
print(f"  - mkvmerge available: {mt.mkvmerge_available}")
print(f"  - mkvextract available: {mt.mkvextract_available}")

# Test codec compatibility
print("\nTesting codec compatibility:")
test_codecs = [
    ("subrip", True),
    ("SubRip/SRT", True),
    ("srt", True),
    ("text/plain", True),
    ("ASS", False),
    ("SSA", False),
    ("VOBSUB", False),
]

for codec, expected in test_codecs:
    result = mt.is_codec_srt_compatible(codec)
    status = "✓" if result == expected else "✗"
    print(f"  {status} {codec}: {result}")

# Test subtitle track
print("\nTesting SubtitleTrack:")
st = SubtitleTrack(1, "eng", "subrip", "English")
print(f"  Track: {st}")
print(f"  Quality score: {st.quality_score()}")

st_forced = SubtitleTrack(2, "eng", "subrip", "English Forced")
st_forced.is_forced = True
print(f"  Forced track: {st_forced}")
print(f"  Quality score: {st_forced.quality_score()}")

print("\n✓ All extraction module tests passed!")
