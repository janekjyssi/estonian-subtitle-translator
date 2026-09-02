"""
Thread-safe translation worker for non-blocking UI operations
"""

import threading
import queue
from pathlib import Path
from typing import List, Optional, Dict, Callable
from app.translator import TranslationWorker


class TranslationWorkItem:
    """Represents a unit of work in translation"""
    def __init__(self, file_path: Path, file_num: int, total_files: int):
        self.file_path = file_path
        self.file_num = file_num
        self.total_files = total_files


class ThreadedTranslationWorker:
    """
    Manages translation in a background thread with thread-safe communication.
    
    Uses a queue to send status updates back to the GUI thread.
    """

    # Message types for queue communication
    MSG_START = "start"
    MSG_FILE_START = "file_start"
    MSG_BATCH_PROGRESS = "batch_progress"
    MSG_BATCH_COMPLETE = "batch_complete"
    MSG_FILE_COMPLETE = "file_complete"
    MSG_STATUS_UPDATE = "status_update"
    MSG_ERROR = "error"
    MSG_COMPLETE = "complete"
    MSG_CANCELLED = "cancelled"

    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        """
        Initialize threaded translation worker.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for translation
        """
        self.api_key = api_key
        self.model = model
        self.worker = None  # Lazy initialization in background thread
        
        # Thread management
        self.thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        
        # Communication queue
        self.message_queue: queue.Queue = queue.Queue()
        
        # State tracking
        self.is_running = False
        self.file_checkpoint_map: Dict = {}  # Map of file paths to checkpoint info

    def start_translation(self, files: List[Path], file_checkpoint_map: Optional[Dict] = None) -> None:
        """
        Start translation of files in a background thread.
        
        Args:
            files: List of file paths to translate
            file_checkpoint_map: Optional dict mapping file paths to {"checkpoint": ..., "resume_mode": ...}
        """
        if self.is_running:
            raise RuntimeError("Translation already in progress")
        
        self.cancel_event.clear()
        self.is_running = True
        self.file_checkpoint_map = file_checkpoint_map or {}
        
        # Start background thread
        self.thread = threading.Thread(
            target=self._do_translation,
            args=(files,),
            daemon=False
        )
        self.thread.start()

    def cancel(self) -> None:
        """Request translation cancellation"""
        self.cancel_event.set()

    def get_message(self, timeout: float = 0.1) -> Optional[dict]:
        """
        Get a message from the queue (non-blocking).
        
        Returns a dict with 'type' and other fields depending on message type,
        or None if queue is empty.
        """
        try:
            return self.message_queue.get(block=False)
        except queue.Empty:
            return None

    def join(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the worker thread to finish.
        
        Returns:
            True if thread finished, False if timeout occurred
        """
        if not self.thread:
            return True
        
        self.thread.join(timeout=timeout)
        return not self.thread.is_alive()

    def _do_translation(self, files: List[Path]) -> None:
        """
        Main translation loop running in background thread.
        
        Args:
            files: Files to translate
        """
        try:
            # Initialize worker in background thread (lazy initialization)
            if self.worker is None:
                self.worker = TranslationWorker(self.api_key, self.model)
            
            # Send start message
            self._send_message({
                "type": self.MSG_START,
                "total_files": len(files)
            })
            
            for file_num, file_path in enumerate(files, 1):
                if self.cancel_event.is_set():
                    self._send_message({"type": self.MSG_CANCELLED})
                    break
                
                # Send file start message
                self._send_message({
                    "type": self.MSG_FILE_START,
                    "file_path": file_path,
                    "file_num": file_num,
                    "total_files": len(files),
                    "file_name": file_path.name
                })
                
                # Translate the file
                checkpoint_info = self.file_checkpoint_map.get(str(file_path), {})
                checkpoint = checkpoint_info.get("checkpoint")
                resume_mode = checkpoint_info.get("resume_mode", "new")
                
                success, message, output_path = self.worker.translate_file(
                    file_path,
                    callback_log=self._send_batch_update,
                    checkpoint=checkpoint,
                    resume_mode=resume_mode,
                )
                
                # Send file complete message
                self._send_message({
                    "type": self.MSG_FILE_COMPLETE,
                    "file_path": file_path,
                    "file_num": file_num,
                    "total_files": len(files),
                    "success": success,
                    "message": message,
                    "output_path": output_path
                })
            
            # Send completion message
            token_usage = self.worker.get_token_usage()
            self._send_message({
                "type": self.MSG_COMPLETE,
                "token_usage": token_usage
            })
        
        except Exception as e:
            self._send_message({
                "type": self.MSG_ERROR,
                "error": str(e)
            })
        finally:
            self.is_running = False

    def _send_message(self, msg: dict) -> None:
        """Send a message to the queue"""
        self.message_queue.put(msg)

    def _send_batch_update(self, log_message: str) -> None:
        """
        Callback from TranslationWorker for batch updates.
        
        Called from background thread during translation.
        """
        # Parse batch progress messages
        if "Plokk" in log_message and "valmis" in log_message:
            # Example: "  Plokk 4 / 17 valmis"
            self._send_message({
                "type": self.MSG_BATCH_COMPLETE,
                "log_message": log_message
            })
        elif "Plokk" in log_message and "–" in log_message:
            # Example: "  Plokk 1 / 15 – 8 subtiitrit"
            self._send_message({
                "type": self.MSG_BATCH_PROGRESS,
                "log_message": log_message
            })
        elif log_message.strip():
            # Other status messages
            self._send_message({
                "type": self.MSG_STATUS_UPDATE,
                "log_message": log_message
            })

    def get_token_usage(self) -> dict:
        """Get token usage from the underlying worker"""
        return self.worker.get_token_usage()
