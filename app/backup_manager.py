"""
Backup manager for automatic source subtitle file backups

Handles backup creation before translation with safety checks:
- Creates BACKUP_<filename> in the same directory as source
- Never overwrites existing backups
- Never backs up files already named BACKUP_*
- Fails safely if backup creation fails
"""

import shutil
from pathlib import Path
from typing import Tuple


class BackupManager:
    """Manages backup creation and validation"""

    BACKUP_PREFIX = "BACKUP_"

    @staticmethod
    def get_backup_filename(source_path: Path) -> str:
        """
        Get the backup filename for a source file.

        Args:
            source_path: Path to source file

        Returns:
            Backup filename (not full path)
        """
        return f"{BackupManager.BACKUP_PREFIX}{source_path.name}"

    @staticmethod
    def should_backup(source_path: Path) -> bool:
        """
        Check if a file should be backed up.

        Files starting with BACKUP_ are never backed up.

        Args:
            source_path: Path to source file

        Returns:
            True if file should be backed up, False otherwise
        """
        # Don't back up files already starting with BACKUP_
        if source_path.name.startswith(BackupManager.BACKUP_PREFIX):
            return False

        return True

    @staticmethod
    def create_backup(source_path: Path) -> Tuple[bool, str, Path]:
        """
        Create a backup copy of the source file.

        Backup is created in the same directory as the source file.
        If backup already exists, it is not overwritten.

        Args:
            source_path: Path to source file to backup

        Returns:
            Tuple of (success: bool, message: str, backup_path: Path)
            - success: True if backup created or already exists
            - message: Status message for display
            - backup_path: Path to backup file (even if it already existed)
        """
        # Validate source file
        if not source_path.exists():
            return False, f"Viga: Seismine fail ei ole olemas: {source_path.name}", source_path.parent / BackupManager.get_backup_filename(source_path)

        # Check if file should be backed up
        if not BackupManager.should_backup(source_path):
            return False, f"Viga: Faili {source_path.name} ei saa varundada (juba varukoopia)", source_path.parent / BackupManager.get_backup_filename(source_path)

        # Determine backup path
        backup_filename = BackupManager.get_backup_filename(source_path)
        backup_path = source_path.parent / backup_filename

        # Check if backup already exists
        if backup_path.exists():
            return True, f"Varukoopia on juba olemas: {backup_filename}", backup_path

        # Create backup
        try:
            shutil.copy2(source_path, backup_path)
            return True, f"Varukoopia loodud: {backup_filename}", backup_path
        except Exception as e:
            return False, f"Viga: Varukoopia loomine ebaõnnestus: {e}", backup_path

    @staticmethod
    def verify_backup(source_path: Path) -> Tuple[bool, str]:
        """
        Verify that a backup exists for the source file.

        Args:
            source_path: Path to source file

        Returns:
            Tuple of (backup_exists: bool, message: str)
        """
        backup_filename = BackupManager.get_backup_filename(source_path)
        backup_path = source_path.parent / backup_filename

        if backup_path.exists():
            return True, f"Varukoopia olemas: {backup_filename}"
        else:
            return False, f"Varukoopia puudub: {backup_filename}"

    @staticmethod
    def check_backup_before_translation(source_path: Path) -> Tuple[bool, str]:
        """
        Check or create backup before translation starts.

        This is the main entry point for backup verification before translation.

        Args:
            source_path: Path to source file

        Returns:
            Tuple of (can_proceed: bool, message: str)
            - can_proceed: True if backup exists or was created
            - message: Status message for logging
        """
        if not BackupManager.should_backup(source_path):
            return True, f"⚠ {source_path.name} on juba varukoopia, ei vaja täiendavat varundamist"

        success, message, _ = BackupManager.create_backup(source_path)

        if success:
            return True, f"✓ {message}"
        else:
            return False, f"✗ {message}"
