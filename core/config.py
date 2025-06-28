"""
Shared configuration for CheckMate GUI and TUI applications.
Unified settings and directory management.
"""

import os
from pathlib import Path
from typing import Dict, List, Union, Optional


class Config:
    """Centralized configuration management for CheckMate applications."""
    
    # Branding
    PEAR_ART = "\U0001F350 "  # Unicode pear emoji
    ASCII_PEAR = "( )\n/ \\"  # ASCII fallback
    
    # Version info
    VERSION = "2.1.0"
    
    def __init__(self, base_dir: str = None):
        """Initialize configuration with optional base directory."""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self._setup_directories()
    
    @property
    def user_docs_dir(self) -> Path:
        """Main user data directory."""
        return self.base_dir / "user_docs"
    
    @property
    def cklb_proc_dir(self) -> Path:
        """Legacy cklb_proc directory for backward compatibility."""
        return self.base_dir / "cklb_proc"
    
    @property
    def directories(self) -> Dict[str, Path]:
        """Dictionary of all managed directories."""
        return {
            # New unified structure
            "user_docs": self.user_docs_dir,
            "zip_files": self.user_docs_dir / "zip_files",
            "cklb_new": self.user_docs_dir / "cklb_new", 
            "cklb_artifacts": self.user_docs_dir / "cklb_artifacts",
            "cklb_updated": self.user_docs_dir / "cklb_updated",
            "inventory": self.user_docs_dir / "inventory",
            
            # Legacy directories (for backward compatibility)
            "cklb_proc": self.cklb_proc_dir,
            "usr_cklb_lib": self.cklb_proc_dir / "usr_cklb_lib",
            "cklb_lib": self.cklb_proc_dir / "cklb_lib",
            "xccdf_lib": self.cklb_proc_dir / "xccdf_lib",
            
            # Common directories
            "logs": self.base_dir / "logs",
            "tmp": self.base_dir / "tmp",
            "baselines": self.base_dir / "baselines"
        }
    
    def get_path(self, directory_name: str) -> Path:
        """Get path for a named directory."""
        if directory_name in self.directories:
            return self.directories[directory_name]
        else:
            raise KeyError(f"Unknown directory: {directory_name}")
    
    def get_version(self) -> str:
        """Get the application version."""
        return self.VERSION
    
    def get_all_directories(self) -> Dict[str, Path]:
        """Get all managed directories."""
        return self.directories.copy()
    
    def get_log_level(self) -> str:
        """Get the default log level."""
        return "INFO"
    
    @property
    def file_extensions(self) -> Dict[str, str]:
        """Supported file extensions."""
        return {
            "cklb": ".cklb",
            "json": ".json", 
            "yaml": ".yaml",
            "yml": ".yml",
            "xml": ".xml",
            "zip": ".zip"
        }
    
    @property
    def log_files(self) -> Dict[str, Path]:
        """Log file locations."""
        log_dir = self.directories["logs"]
        return {
            "main": log_dir / "checkmate.log",
            "gui": log_dir / "gui.log",
            "tui": log_dir / "tui.log",
            "downloader": log_dir / "downloader.log",
            "scraper": log_dir / "scraper.log",
            "fullauto": log_dir / "fullauto.log"
        }
    
    def _setup_directories(self):
        """Create only new user_docs-based directories, not legacy cklb_proc ones."""
        new_dirs = [
            self.user_docs_dir,
            self.user_docs_dir / "zip_files",
            self.user_docs_dir / "cklb_new",
            self.user_docs_dir / "cklb_artifacts",
            self.user_docs_dir / "cklb_updated",
            self.user_docs_dir / "inventory",
            self.base_dir / "logs",
            self.base_dir / "tmp",
            self.base_dir / "baselines"
        ]
        for path in new_dirs:
            path.mkdir(parents=True, exist_ok=True, mode=0o755)
    
    def get_user_cklb_dir(self) -> Path:
        """Get the user CKLB directory (artifacts for new, usr_cklb_lib for legacy)."""
        # Prefer new structure, fall back to legacy
        new_dir = self.directories["cklb_artifacts"]
        legacy_dir = self.directories["usr_cklb_lib"]
        
        if new_dir.exists() and any(new_dir.iterdir()):
            return new_dir
        elif legacy_dir.exists():
            return legacy_dir
        else:
            return new_dir
    
    def get_cklb_lib_dir(self) -> Path:
        """Get the CKLB library directory (new for new, cklb_lib for legacy)."""
        # Prefer new structure, fall back to legacy
        new_dir = self.directories["cklb_new"]
        legacy_dir = self.directories["cklb_lib"]
        
        if new_dir.exists() and any(new_dir.iterdir()):
            return new_dir
        elif legacy_dir.exists():
            return legacy_dir
        else:
            return new_dir
    
    def migrate_legacy_data(self):
        """Migrate data from legacy cklb_proc structure to new user_docs structure."""
        migrations = [
            (self.directories["usr_cklb_lib"], self.directories["cklb_artifacts"]),
            (self.directories["cklb_lib"], self.directories["cklb_new"]),
        ]
        
        for source, target in migrations:
            if source.exists() and any(source.iterdir()):
                target.mkdir(parents=True, exist_ok=True)
                for file_path in source.glob("*.cklb"):
                    target_path = target / file_path.name
                    if not target_path.exists():
                        import shutil
                        shutil.copy2(file_path, target_path)


# Global default config instance
default_config = Config()
