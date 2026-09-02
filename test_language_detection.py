#!/usr/bin/env python3
"""Test language detection feature"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.language_detector import LanguageDetector


def test_language_detection():
    """Test language detection with sample files"""
    print("\n" + "=" * 70)
    print("LANGUAGE DETECTION TESTS")
    print("=" * 70)
    
    detector = LanguageDetector()
    
    # Test 1: Detect English
    print("\nTest 1: Detect English")
    print("-" * 70)
    test_file_en = Path(__file__).parent / "test_sample.en.srt"
    if test_file_en.exists():
        result = detector.detect_language_in_file(test_file_en)
        print(f"File: {result['file']}")
        print(f"Detected language: {result['display_name']}")
        print(f"Language code: {result['language_code']}")
        print(f"Sample length: {result['sample_length']} chars")
        
        assert result['language_code'] == 'en', f"Expected 'en', got {result['language_code']}"
        assert result['display_name'] == 'Inglise', f"Expected 'Inglise', got {result['display_name']}"
        print("✓ English detected correctly")
    else:
        print(f"⚠ Test file not found: {test_file_en}")
    
    # Test 2: Detect Estonian
    print("\nTest 2: Detect Estonian")
    print("-" * 70)
    test_file_et = Path(__file__).parent / "test_sample.et.srt"
    if test_file_et.exists():
        result = detector.detect_language_in_file(test_file_et)
        print(f"File: {result['file']}")
        print(f"Detected language: {result['display_name']}")
        print(f"Language code: {result['language_code']}")
        
        assert result['language_code'] == 'et', f"Expected 'et', got {result['language_code']}"
        assert result['display_name'] == 'Eesti', f"Expected 'Eesti', got {result['display_name']}"
        print("✓ Estonian detected correctly")
    else:
        print(f"⚠ Test file not found: {test_file_et}")
    
    # Test 3: Detect Finnish
    print("\nTest 3: Detect Finnish")
    print("-" * 70)
    test_file_fi = Path(__file__).parent / "test_sample.fi.srt"
    if test_file_fi.exists():
        result = detector.detect_language_in_file(test_file_fi)
        print(f"File: {result['file']}")
        print(f"Detected language: {result['display_name']}")
        print(f"Language code: {result['language_code']}")
        
        assert result['language_code'] == 'fi', f"Expected 'fi', got {result['language_code']}"
        assert result['display_name'] == 'Soome', f"Expected 'Soome', got {result['display_name']}"
        print("✓ Finnish detected correctly")
    else:
        print(f"⚠ Test file not found: {test_file_fi}")
    
    # Test 4: Detect German
    print("\nTest 4: Detect German")
    print("-" * 70)
    test_file_de = Path(__file__).parent / "test_sample.de.srt"
    if test_file_de.exists():
        result = detector.detect_language_in_file(test_file_de)
        print(f"File: {result['file']}")
        print(f"Detected language: {result['display_name']}")
        print(f"Language code: {result['language_code']}")
        
        assert result['language_code'] == 'de', f"Expected 'de', got {result['language_code']}"
        assert result['display_name'] == 'Saksa', f"Expected 'Saksa', got {result['display_name']}"
        print("✓ German detected correctly")
    else:
        print(f"⚠ Test file not found: {test_file_de}")
    
    # Test 5: Multiple files detection
    print("\nTest 5: Multiple files detection")
    print("-" * 70)
    test_files = [test_file_en, test_file_et, test_file_fi]
    if all(f.exists() for f in test_files):
        detections = detector.detect_languages_in_files(test_files)
        print(f"Files analyzed: {len(detections)}")
        
        for det in detections:
            print(f"  {det['file']:25s} -> {det['display_name']}")
        
        assert len(detections) == 3, f"Expected 3 detections, got {len(detections)}"
        print("✓ Multiple files detected correctly")
    
    # Test 6: Summary generation
    print("\nTest 6: Summary generation for multiple languages")
    print("-" * 70)
    if all(f.exists() for f in test_files):
        detections = detector.detect_languages_in_files(test_files)
        summary = detector.summarize_detections(detections)
        
        print(f"Total files: {summary['total_files']}")
        print(f"By language: {summary['by_display_name']}")
        print(f"Has Estonian: {summary['has_estonian']}")
        print(f"Has English: {summary['has_english']}")
        print(f"Has other: {summary['has_other']}")
        print(f"All same: {summary['all_same']}")
        
        assert summary['total_files'] == 3, "Should have 3 files"
        assert summary['has_english'], "Should have English"
        assert summary['has_estonian'], "Should have Estonian"
        assert summary['has_other'], "Should have other languages"
        assert not summary['all_same'], "Should have multiple different languages"
        print("✓ Summary generated correctly")
    
    # Test 7: Format for display
    print("\nTest 7: Format detection for log display")
    print("-" * 70)
    if test_file_en.exists():
        result = detector.detect_language_in_file(test_file_en)
        formatted = detector.format_detection_for_log(result)
        print(f"Formatted: {formatted}")
        assert "test_sample.en.srt" in formatted, "Should contain filename"
        assert "Inglise" in formatted, "Should contain language"
        print("✓ Formatted correctly")
    
    # Test 8: Format multiple detections
    print("\nTest 8: Format multiple detections for log")
    print("-" * 70)
    if all(f.exists() for f in test_files):
        detections = detector.detect_languages_in_files(test_files)
        formatted = detector.format_detections_for_log(detections)
        print(f"Formatted:\n{formatted}")
        
        assert "Keele tuvastamine:" in formatted, "Should have header"
        assert "Inglise" in formatted, "Should contain English"
        assert "Eesti" in formatted, "Should contain Estonian"
        print("✓ Formatted multiple detections correctly")
    
    # Test 9: Sample text extraction
    print("\nTest 9: Sample text extraction")
    print("-" * 70)
    if test_file_en.exists():
        sample = detector.sample_subtitle_text(test_file_en)
        print(f"Sample length: {len(sample)} chars")
        print(f"Sample text: {sample[:100]}...")
        
        assert len(sample) > 0, "Should extract text"
        assert "Hello" in sample or "thanks" in sample, "Should contain subtitle dialogue"
        print("✓ Sample text extracted correctly")
    
    print("\n" + "=" * 70)
    print("ALL LANGUAGE DETECTION TESTS PASSED ✓")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_language_detection()
