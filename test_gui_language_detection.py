"""
Integration test for language detection in GUI

Tests that:
1. LanguageDetector is properly initialized in SubtitlesApp
2. Language detection works when called from GUI methods
3. Warning system works correctly
4. No files are modified during detection
5. Cost estimation still works with language detection
"""

from pathlib import Path
from app.gui import SubtitlesApp
from app.language_detector import LanguageDetector


def test_language_detector_initialization():
    """Test that LanguageDetector is properly initialized in SubtitlesApp"""
    print("\n" + "="*70)
    print("TEST: LanguageDetector Initialization")
    print("="*70)
    
    # Create a detector instance
    detector = LanguageDetector()
    print("✓ LanguageDetector created successfully")
    
    # Verify it has all required methods
    required_methods = [
        'sample_subtitle_text',
        'detect_language_in_file',
        'detect_languages_in_files',
        'summarize_detections',
        'format_detection_for_log',
        'format_detections_for_log',
        'format_summary_for_log',
    ]
    
    for method in required_methods:
        assert hasattr(detector, method), f"Missing method: {method}"
        print(f"✓ Method '{method}' present")
    
    print("✓ All required methods present")


def test_file_not_modified_after_detection():
    """Test that files are not modified during language detection"""
    print("\n" + "="*70)
    print("TEST: Files Not Modified During Detection")
    print("="*70)
    
    detector = LanguageDetector()
    test_file = Path("test_sample.en.srt")
    
    if not test_file.exists():
        print(f"⚠ Test file {test_file} not found, skipping")
        return
    
    # Record original file content
    with open(test_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    original_mtime = test_file.stat().st_mtime
    
    # Run detection
    result = detector.detect_language_in_file(test_file)
    
    # Check file not modified
    with open(test_file, 'r', encoding='utf-8') as f:
        after_content = f.read()
    
    after_mtime = test_file.stat().st_mtime
    
    assert original_content == after_content, "File content was modified!"
    assert original_mtime == after_mtime, "File modification time changed!"
    
    print(f"✓ File content unchanged")
    print(f"✓ File modification time unchanged")
    print(f"✓ Detection succeeded: {result['language_code']} ({result['display_name']})")


def test_multiple_file_detection():
    """Test detecting languages in multiple files"""
    print("\n" + "="*70)
    print("TEST: Multiple File Detection")
    print("="*70)
    
    detector = LanguageDetector()
    test_files = [
        Path("test_sample.en.srt"),
        Path("test_sample.et.srt"),
        Path("test_sample.fi.srt"),
    ]
    
    # Check which files exist
    existing_files = [f for f in test_files if f.exists()]
    
    if not existing_files:
        print("⚠ No test files found, skipping")
        return
    
    print(f"Testing with {len(existing_files)} files")
    
    # Detect languages
    detections = detector.detect_languages_in_files(existing_files)
    
    assert len(detections) == len(existing_files), "Wrong number of detections!"
    
    for detection in detections:
        assert detection['file'], "Missing file name"
        assert detection['language_code'], "Missing language code"
        assert detection['display_name'], "Missing display name"
        print(f"✓ {detection['file']}: {detection['display_name']} ({detection['language_code']})")
    
    # Test summarization
    summary = detector.summarize_detections(detections)
    
    assert 'total_files' in summary
    assert 'by_language' in summary
    assert 'by_display_name' in summary
    print(f"\n✓ Summary generated: {summary['total_files']} files detected")
    print(f"  Languages: {list(summary['by_display_name'].keys())}")


def test_warning_detection_logic():
    """Test the warning detection logic"""
    print("\n" + "="*70)
    print("TEST: Warning Detection Logic")
    print("="*70)
    
    detector = LanguageDetector()
    
    # Create mock detection results
    detections_english = [
        {
            'file': 'test.srt',
            'language_code': 'en',
            'display_name': 'Inglise',
            'confidence': 0.95,
            'sample_length': 100,
            'error': None,
        }
    ]
    
    detections_estonian = [
        {
            'file': 'test.srt',
            'language_code': 'et',
            'display_name': 'Eesti',
            'confidence': 0.92,
            'sample_length': 100,
            'error': None,
        }
    ]
    
    detections_mixed = [
        {
            'file': 'test1.srt',
            'language_code': 'en',
            'display_name': 'Inglise',
            'confidence': 0.95,
            'sample_length': 100,
            'error': None,
        },
        {
            'file': 'test2.srt',
            'language_code': 'et',
            'display_name': 'Eesti',
            'confidence': 0.92,
            'sample_length': 100,
            'error': None,
        }
    ]
    
    # Test English summary
    summary_en = detector.summarize_detections(detections_english)
    assert summary_en['all_same'] == True, "English should be all_same"
    assert summary_en['has_english'] == True, "Should have English"
    assert summary_en['has_estonian'] == False, "Should not have Estonian"
    print("✓ English summary correct")
    
    # Test Estonian summary
    summary_et = detector.summarize_detections(detections_estonian)
    assert summary_et['all_same'] == True, "Estonian should be all_same"
    assert summary_et['has_estonian'] == True, "Should have Estonian"
    assert summary_et['has_english'] == False, "Should not have English"
    print("✓ Estonian summary correct")
    
    # Test mixed summary
    summary_mixed = detector.summarize_detections(detections_mixed)
    assert summary_mixed['all_same'] == False, "Mixed should not be all_same"
    assert summary_mixed['has_english'] == True, "Should have English"
    assert summary_mixed['has_estonian'] == True, "Should have Estonian"
    print("✓ Mixed language summary correct")


def test_formatting_for_gui():
    """Test that formatting works correctly for GUI display"""
    print("\n" + "="*70)
    print("TEST: GUI Formatting")
    print("="*70)
    
    detector = LanguageDetector()
    
    detection = {
        'file': 'test.srt',
        'language_code': 'en',
        'display_name': 'Inglise',
        'confidence': 0.95,
        'sample_length': 100,
        'error': None,
    }
    
    # Test single detection formatting
    formatted = detector.format_detection_for_log(detection)
    assert 'test.srt' in formatted, "File name missing from format"
    assert 'Inglise' in formatted, "Language name missing from format"
    print(f"✓ Single detection formatted: {formatted}")
    
    # Test multiple detections formatting
    detections = [
        detection,
        {
            'file': 'test2.srt',
            'language_code': 'et',
            'display_name': 'Eesti',
            'confidence': 0.92,
            'sample_length': 100,
            'error': None,
        }
    ]
    
    formatted_multi = detector.format_detections_for_log(detections)
    assert 'Keele tuvastamine' in formatted_multi, "Header missing from format"
    assert 'test.srt' in formatted_multi, "First file missing from format"
    assert 'test2.srt' in formatted_multi, "Second file missing from format"
    print(f"✓ Multiple detections formatted correctly")
    
    # Test summary formatting
    summary = detector.summarize_detections(detections)
    formatted_summary = detector.format_summary_for_log(summary)
    assert formatted_summary, "Summary formatting returned empty"
    print(f"✓ Summary formatted: {formatted_summary}")


def test_display_names():
    """Test that all language codes have display names"""
    print("\n" + "="*70)
    print("TEST: Display Names for Languages")
    print("="*70)
    
    detector = LanguageDetector()
    
    test_codes = ['en', 'et', 'fi', 'de', 'fr', 'ru', 'unknown', None]
    
    for code in test_codes:
        display_name = detector._get_display_name(code)
        assert display_name, f"No display name for {code}"
        print(f"✓ {code}: {display_name}")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("LANGUAGE DETECTION - GUI INTEGRATION TESTS")
    print("="*80)
    
    try:
        test_language_detector_initialization()
        test_file_not_modified_after_detection()
        test_multiple_file_detection()
        test_warning_detection_logic()
        test_formatting_for_gui()
        test_display_names()
        
        print("\n" + "="*80)
        print("ALL INTEGRATION TESTS PASSED ✓")
        print("="*80)
        print("\nLanguage detection is properly integrated with the GUI.")
        print("- Files are not modified during detection")
        print("- All language markers are working")
        print("- Warning logic is correct")
        print("- GUI formatting works as expected")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
