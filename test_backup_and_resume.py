"""
Test suite for backup and resume functionality

Tests local behavior without making API calls:
1. Automatic backup creation
2. Backup handling for existing files
3. Checkpoint creation and validation
4. Resume detection and validation
5. Model mismatch detection
6. Source file change detection
"""

import json
import tempfile
import time
from pathlib import Path
from app.backup_manager import BackupManager
from app.checkpoint_manager import CheckpointManager
from app.translator import SRTParser, SubtitleEntry


def create_test_srt_file(path: Path, content: str) -> None:
    """Create a test SRT file with given content"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def get_file_contents(path: Path) -> str:
    """Read file contents"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_backup_creation():
    """Test automatic backup creation"""
    print("\n" + "="*70)
    print("TEST 1: Automatic Backup Creation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_file = tmpdir / "test.en.srt"
        
        # Create source file
        test_content = """1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,000 --> 00:00:08,000
This is a test.
"""
        create_test_srt_file(source_file, test_content)
        print(f"✓ Created source file: {source_file.name}")
        
        # Create backup
        success, msg, backup_path = BackupManager.create_backup(source_file)
        assert success, f"Backup creation failed: {msg}"
        assert backup_path.exists(), "Backup file doesn't exist"
        print(f"✓ Backup created: {backup_path.name}")
        print(f"  Message: {msg}")
        
        # Verify backup is byte-for-byte copy
        source_content = get_file_contents(source_file)
        backup_content = get_file_contents(backup_path)
        assert source_content == backup_content, "Backup content mismatch"
        print("✓ Backup is byte-for-byte copy")
        
        # Verify backup name format
        assert backup_path.name == f"BACKUP_{source_file.name}", "Backup name format incorrect"
        print(f"✓ Backup name format correct: BACKUP_<filename>")


def test_backup_existing():
    """Test that existing backups are not overwritten"""
    print("\n" + "="*70)
    print("TEST 2: Don't Overwrite Existing Backups")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_file = tmpdir / "test.en.srt"
        backup_file = tmpdir / "BACKUP_test.en.srt"
        
        # Create source file
        create_test_srt_file(source_file, "Original content")
        print(f"✓ Created source file: {source_file.name}")
        
        # Create initial backup
        success1, msg1, _ = BackupManager.create_backup(source_file)
        assert success1, "First backup creation failed"
        print(f"✓ First backup created: {msg1}")
        
        # Modify source file
        time.sleep(0.1)
        create_test_srt_file(source_file, "Modified content")
        print("✓ Modified source file")
        
        # Try to create backup again
        success2, msg2, _ = BackupManager.create_backup(source_file)
        assert success2, "Second backup check failed"
        assert "juba olemas" in msg2.lower(), "Expected 'already exists' message"
        print(f"✓ Existing backup preserved: {msg2}")
        
        # Verify backup still has original content
        backup_content = get_file_contents(backup_file)
        assert "Original content" in backup_content, "Backup was overwritten!"
        print("✓ Backup content unchanged (not overwritten)")


def test_backup_prefix_files():
    """Test that files starting with BACKUP_ are never backed up"""
    print("\n" + "="*70)
    print("TEST 3: Don't Back Up Already Backed Up Files")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        backup_file = tmpdir / "BACKUP_test.en.srt"
        
        # Create a backup-style file
        create_test_srt_file(backup_file, "Backup content")
        print(f"✓ Created file: {backup_file.name}")
        
        # Try to backup it
        should_backup = BackupManager.should_backup(backup_file)
        assert not should_backup, "BACKUP_ file was marked for backup"
        print("✓ File starting with BACKUP_ is not backed up")
        
        # Try with check_backup_before_translation
        can_proceed, msg = BackupManager.check_backup_before_translation(backup_file)
        assert can_proceed, "Should proceed with BACKUP_ file"
        assert "juba varukoopia" in msg.lower(), "Expected correct message"
        print(f"✓ check_backup_before_translation handled correctly: {msg}")


def test_checkpoint_creation():
    """Test checkpoint creation and restoration"""
    print("\n" + "="*70)
    print("TEST 4: Checkpoint Creation and Restoration")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_file = tmpdir / "test.en.srt"
        
        # Create source file
        create_test_srt_file(source_file, "Test content")
        print(f"✓ Created source file: {source_file.name}")
        
        # Create checkpoint
        translated_dict = {
            "1": "Tere, maailm!",
            "2": "See on test.",
        }
        checkpoint_ok, checkpoint_msg = CheckpointManager.create_checkpoint(
            source_file,
            model_id="gpt-4.1",
            total_batches=2,
            completed_batches=[0],  # First batch done
            translated_entries=translated_dict,
            total_input_tokens=100,
            total_output_tokens=50,
        )
        assert checkpoint_ok, f"Checkpoint creation failed: {checkpoint_msg}"
        print(f"✓ Checkpoint created: {checkpoint_msg}")
        
        # Load checkpoint
        loaded = CheckpointManager.load_checkpoint(source_file)
        assert loaded is not None, "Checkpoint not loaded"
        print("✓ Checkpoint loaded successfully")
        
        # Verify checkpoint contents
        assert loaded["model"]["id"] == "gpt-4.1", "Model ID mismatch"
        assert loaded["progress"]["completed_count"] == 1, "Completed count mismatch"
        assert loaded["translated_entries"]["1"] == "Tere, maailm!", "Translated entry mismatch"
        assert loaded["token_usage"]["input"] == 100, "Token usage mismatch"
        print("✓ Checkpoint contents verified")


def test_checkpoint_validation():
    """Test checkpoint validation"""
    print("\n" + "="*70)
    print("TEST 5: Checkpoint Validation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_file = tmpdir / "test.en.srt"
        
        # Create source file
        original_content = "Test content v1"
        create_test_srt_file(source_file, original_content)
        print(f"✓ Created source file: {source_file.name}")
        
        # Create checkpoint
        CheckpointManager.create_checkpoint(
            source_file,
            model_id="gpt-4.1",
            total_batches=1,
            completed_batches=[],
            translated_entries={},
            total_input_tokens=0,
            total_output_tokens=0,
        )
        print("✓ Checkpoint created")
        
        # Load and validate
        checkpoint = CheckpointManager.load_checkpoint(source_file)
        is_valid, msg = CheckpointManager.validate_checkpoint(source_file, checkpoint)
        assert is_valid, f"Checkpoint validation failed: {msg}"
        print(f"✓ Checkpoint validated: {msg}")
        
        # Modify source file
        time.sleep(0.1)
        create_test_srt_file(source_file, "Modified content v2")
        print("✓ Modified source file")
        
        # Validate again - should fail
        is_valid, msg = CheckpointManager.validate_checkpoint(source_file, checkpoint)
        assert not is_valid, "Checkpoint should be invalid for modified file"
        assert "pärast" in msg.lower(), "Expected 'after' in message"
        print(f"✓ Modified file detected: {msg}")


def test_model_mismatch_detection():
    """Test detection of model mismatch in checkpoint"""
    print("\n" + "="*70)
    print("TEST 6: Model Mismatch Detection")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_file = tmpdir / "test.en.srt"
        
        # Create source file
        create_test_srt_file(source_file, "Test")
        
        # Create checkpoint with one model
        CheckpointManager.create_checkpoint(
            source_file,
            model_id="gpt-4.1",
            total_batches=1,
            completed_batches=[],
            translated_entries={},
            total_input_tokens=0,
            total_output_tokens=0,
        )
        print("✓ Checkpoint created with model: gpt-4.1")
        
        # Load and check for mismatch
        checkpoint = CheckpointManager.load_checkpoint(source_file)
        
        has_mismatch, checkpoint_model = CheckpointManager.check_model_mismatch(
            checkpoint, "gpt-5.6-terra"
        )
        assert has_mismatch, "Model mismatch not detected"
        assert checkpoint_model == "gpt-4.1", "Checkpoint model ID mismatch"
        print(f"✓ Model mismatch detected: checkpoint uses {checkpoint_model}, current is gpt-5.6-terra")
        
        # Check with same model
        has_mismatch2, _ = CheckpointManager.check_model_mismatch(
            checkpoint, "gpt-4.1"
        )
        assert not has_mismatch2, "False positive model mismatch"
        print("✓ No mismatch when model is same")


def test_checkpoint_filename():
    """Test checkpoint filename generation"""
    print("\n" + "="*70)
    print("TEST 7: Checkpoint Filename Format")
    print("="*70)
    
    test_filename = "Stalker.1979.1080p.en.srt"
    source_path = Path("/some/path") / test_filename
    
    checkpoint_name = CheckpointManager.get_checkpoint_filename(source_path)
    expected = f"{test_filename}.translation_progress.json"
    
    assert checkpoint_name == expected, f"Expected {expected}, got {checkpoint_name}"
    print(f"✓ Checkpoint filename: {checkpoint_name}")


def test_progress_summary():
    """Test progress summary generation"""
    print("\n" + "="*70)
    print("TEST 8: Progress Summary")
    print("="*70)
    
    checkpoint = {
        "progress": {
            "completed_count": 12,
            "total_batches": 38,
        }
    }
    
    summary = CheckpointManager.get_progress_summary(checkpoint)
    expected = "Valmis: 12 / 38 plokki"
    
    assert summary == expected, f"Expected '{expected}', got '{summary}'"
    print(f"✓ Progress summary: {summary}")


def run_all_tests():
    """Run all backup and checkpoint tests"""
    print("\n" + "="*80)
    print("BACKUP & RESUME FUNCTIONALITY TESTS")
    print("="*80)
    
    try:
        test_backup_creation()
        test_backup_existing()
        test_backup_prefix_files()
        test_checkpoint_creation()
        test_checkpoint_validation()
        test_model_mismatch_detection()
        test_checkpoint_filename()
        test_progress_summary()
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
        print("\nBackup and Resume Features:")
        print("  ✓ Automatic backup creation (BACKUP_<filename>)")
        print("  ✓ Backup not overwritten if already exists")
        print("  ✓ Files starting with BACKUP_ never backed up again")
        print("  ✓ Checkpoint creation with progress tracking")
        print("  ✓ Source file validation (hash checking)")
        print("  ✓ Model mismatch detection")
        print("  ✓ Resume progress summary")
        print(f"\nCheckpoint storage location: <source_file>.translation_progress.json")
        print(f"Source validation: SHA256 hash check")
        print(f"Supported resume modes: new, resume, restart")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
