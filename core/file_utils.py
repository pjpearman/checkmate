"""
File operation utilities with pathlib-based implementation and validation.
Enhanced version with additional functionality for CheckMate.
"""

from pathlib import Path
import json
import logging
from typing import List, Dict, Optional, Union, Tuple
import shutil
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class FileUtils:
    """File operation utilities for CheckMate applications."""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """
        Ensure a directory exists and return its Path object.
        Creates the directory if it doesn't exist.
        
        Args:
            path: Directory path as string or Path
            
        Returns:
            Path object for the directory
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True, mode=0o755)
        return path

    @staticmethod
    def validate_file_ext(path: Union[str, Path], allowed_exts: List[str]) -> bool:
        """
        Validate that a file has an allowed extension.
        
        Args:
            path: File path to validate
            allowed_exts: List of allowed extensions (with dot)
            
        Returns:
            bool: Whether the file extension is allowed
        """
        path = Path(path)
        return path.suffix.lower() in [ext.lower() for ext in allowed_exts]

    @staticmethod
    def safe_json_load(path: Union[str, Path]) -> Dict:
        """
        Safely load a JSON file with error handling.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Dict containing the JSON data
            
        Raises:
            ValueError: If file is invalid JSON
            FileNotFoundError: If file doesn't exist
        """
        path = Path(path)
        try:
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            raise ValueError(f"Invalid JSON in {path}: {e}")
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            raise

    @staticmethod
    def safe_json_save(data: Dict, path: Union[str, Path], indent: int = 2) -> Path:
        """
        Safely save data to a JSON file with error handling.
        
        Args:
            data: Data to save
            path: Path to save JSON file
            indent: JSON indentation level
            
        Returns:
            Path object for the saved file
        """
        path = Path(path)
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first
            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            # Atomic move
            temp_path.replace(path)
            return path
        except Exception as e:
            logger.error(f"Error saving JSON to {path}: {e}")
            raise

    @staticmethod
    def safe_file_move(src: Union[str, Path], dest: Union[str, Path]) -> Path:
        """
        Safely move a file with error handling and backup.
        
        Args:
            src: Source file path
            dest: Destination file path
            
        Returns:
            Path object for the destination file
            
        Raises:
            FileNotFoundError: If source doesn't exist
            OSError: If move operation fails
        """
        src, dest = Path(src), Path(dest)
        
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
            
        if dest.exists():
            backup = dest.with_suffix(f"{dest.suffix}.{datetime.now():%Y%m%d_%H%M%S}.bak")
            logger.info(f"Creating backup: {backup}")
            shutil.copy2(dest, backup)
        
        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dest)
            return dest
        except Exception as e:
            logger.error(f"Error moving {src} to {dest}: {e}")
            raise

    @staticmethod
    def safe_file_copy(src: Union[str, Path], dest: Union[str, Path]) -> Path:
        """
        Safely copy a file with error handling.
        
        Args:
            src: Source file path
            dest: Destination file path
            
        Returns:
            Path object for the destination file
        """
        src, dest = Path(src), Path(dest)
        
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        
        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return dest
        except Exception as e:
            logger.error(f"Error copying {src} to {dest}: {e}")
            raise

    @staticmethod
    def list_files_with_ext(
        directory: Union[str, Path],
        extension: str,
        recursive: bool = False
    ) -> List[Path]:
        """
        List all files with a given extension in a directory.
        
        Args:
            directory: Directory to search
            extension: File extension to match (with or without dot)
            recursive: Whether to search recursively
            
        Returns:
            List of Path objects for matching files
        """
        directory = Path(directory)
        if not extension.startswith('.'):
            extension = f".{extension}"
            
        pattern = f"**/*{extension}" if recursive else f"*{extension}"
        return sorted(directory.glob(pattern))

    @staticmethod
    def get_file_info(path: Union[str, Path]) -> Dict:
        """
        Get comprehensive file information.
        
        Args:
            path: File path
            
        Returns:
            Dict with file information
        """
        path = Path(path)
        if not path.exists():
            return {"exists": False, "path": str(path)}
        
        stat = path.stat()
        return {
            "exists": True,
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix
        }

    @staticmethod
    def find_cklb_files(directory: Union[str, Path], pattern: str = None) -> List[Path]:
        """
        Find CKLB files in a directory with optional pattern matching.
        
        Args:
            directory: Directory to search
            pattern: Optional filename pattern to match
            
        Returns:
            List of CKLB file paths
        """
        directory = Path(directory)
        if not directory.exists():
            return []
        
        if pattern:
            files = directory.glob(f"*{pattern}*.cklb")
        else:
            files = directory.glob("*.cklb")
        
        return sorted(files)

    @staticmethod
    def import_files(
        source_files: List[Union[str, Path]], 
        dest_dir: Union[str, Path],
        allowed_extensions: List[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Import multiple files to a destination directory.
        
        Args:
            source_files: List of source file paths
            dest_dir: Destination directory
            allowed_extensions: List of allowed file extensions
            
        Returns:
            List of (filename, status) tuples
        """
        if allowed_extensions is None:
            allowed_extensions = ['.cklb', '.json']
        
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for file_path in source_files:
            file_path = Path(file_path)
            
            if not file_path.exists():
                results.append((str(file_path), "File not found"))
                continue
            
            if not FileUtils.validate_file_ext(file_path, allowed_extensions):
                results.append((str(file_path), "Invalid file type"))
                continue
            
            try:
                dest_path = dest_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                results.append((str(file_path), "Imported"))
            except Exception as e:
                logger.error(f"Error importing {file_path}: {e}")
                results.append((str(file_path), f"Error: {e}"))
        
        return results


# Convenience functions for backward compatibility
ensure_dir = FileUtils.ensure_dir
validate_file_ext = FileUtils.validate_file_ext
safe_json_load = FileUtils.safe_json_load
safe_file_move = FileUtils.safe_file_move
list_files_with_ext = FileUtils.list_files_with_ext
