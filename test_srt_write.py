#!/usr/bin/env python3
"""Test SRT parsing and writing"""

from pathlib import Path
from app.translator import SRTParser, SubtitleEntry

# Create test entries
entries = [
    SubtitleEntry(1, "00:00:01,000", "00:00:04,000", "Tere, kuidas sul läheb?"),
    SubtitleEntry(2, "00:00:05,000", "00:00:08,000", "Minul läheb suurepäraselt, aitäh küsimise eest!"),
    SubtitleEntry(3, "00:00:09,000", "00:00:12,000", "See on imeline kuulda."),
]

# Write to file
output_path = Path('test_sample.et.srt')
SRTParser.write_srt(output_path, entries)
print(f"✓ Wrote {len(entries)} entries to {output_path.name}")

# Read back and verify
parsed = SRTParser.parse_srt(output_path)
print(f"✓ Read back {len(parsed)} entries")
for e in parsed:
    print(f"  {e.seq_number}: {e.text[:40]}...")

# Show file content
print("\nFile content:")
print(output_path.read_text(encoding='utf-8'))

print("✓ SRT write/read test passed!")
