import os
import shutil
from src.utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger()

class FileManager:
    def __init__(self):
        # Optional whitelist of allowed directories from .env
        allowed_dirs = os.getenv("ALLOWED_DIRS", "").split(",")
        self.allowed_dirs = [os.path.abspath(d.strip()) for d in allowed_dirs if d.strip()] if allowed_dirs else None

    def _is_path_allowed(self, path: str) -> bool:
        """Check if the path is allowed based on the whitelist (if set)."""
        if not self.allowed_dirs:
            return True  # No restrictions if whitelist is not set
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(allowed_dir) for allowed_dir in self.allowed_dirs)

    def create_file(self, file_path: str, content: str = "") -> bool:
        """Create a file at the specified path with optional content."""
        if not self._is_path_allowed(file_path):
            logger.error(f"Path not allowed: {file_path}")
            return False
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {str(e)}")
            return False

    def read_file(self, file_path: str) -> str:
        """Read content from a file at the specified path."""
        if not self._is_path_allowed(file_path):
            logger.error(f"Path not allowed: {file_path}")
            return ""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Read file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return ""

    def update_file(self, file_path: str, content: str) -> bool:
        """Update (overwrite) a file's content at the specified path."""
        if not self._is_path_allowed(file_path):
            logger.error(f"Path not allowed: {file_path}")
            return False
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Updated file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update file {file_path}: {str(e)}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file at the specified path."""
        if not self._is_path_allowed(file_path):
            logger.error(f"Path not allowed: {file_path}")
            return False
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        try:
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    def create_directory(self, dir_path: str) -> bool:
        """Create a directory at the specified path."""
        if not self._is_path_allowed(dir_path):
            logger.error(f"Path not allowed: {dir_path}")
            return False
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {str(e)}")
            return False

    def move_file(self, src_path: str, dest_dir: str) -> bool:
        """Move a file from src_path to dest_dir."""
        if not (self._is_path_allowed(src_path) and self._is_path_allowed(dest_dir)):
            logger.error(f"Path not allowed: {src_path} or {dest_dir}")
            return False
        if not os.path.exists(src_path):
            logger.error(f"File not found: {src_path}")
            return False
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src_path, dest_path)
            logger.info(f"Moved file {src_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file {src_path}: {str(e)}")
            return False

    def search_files(self, dir_path: str, pattern: str) -> list[str]:
        """Search for files matching a pattern in the specified directory."""
        if not self._is_path_allowed(dir_path):
            logger.error(f"Path not allowed: {dir_path}")
            return []
        if not os.path.exists(dir_path):
            logger.error(f"Directory not found: {dir_path}")
            return []
        try:
            files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if pattern in f or f.endswith(pattern)]
            logger.info(f"Found files matching {pattern} in {dir_path}: {files}")
            return files
        except Exception as e:
            logger.error(f"Failed to search files in {dir_path} with pattern {pattern}: {str(e)}")
            return []

    def execute_task(self, task: str, args: dict) -> str:
        """Execute a task based on LLM instructions."""
        task = task.lower()
        if task == "create_file":
            return "Success" if self.create_file(args.get("file_path", ""), args.get("content", "")) else "Failed"
        elif task == "read_file":
            return self.read_file(args.get("file_path", ""))
        elif task == "update_file":
            return "Success" if self.update_file(args.get("file_path", ""), args.get("content", "")) else "Failed"
        elif task == "delete_file":
            return "Success" if self.delete_file(args.get("file_path", "")) else "Failed"
        elif task == "create_directory":
            return "Success" if self.create_directory(args.get("dir_path", "")) else "Failed"
        elif task == "move_file":
            return "Success" if self.move_file(args.get("src_path", ""), args.get("dest_dir", "")) else "Failed"
        elif task == "search_files":
            files = self.search_files(args.get("dir_path", ""), args.get("pattern", ""))
            return f"Found: {', '.join(files)}" if files else "No files found"
        else:
            logger.warning(f"Unknown task: {task}")
            return "Task not recognized"