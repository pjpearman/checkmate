"""
Logging configuration for CheckMate applications.
Provides centralized logging setup for both GUI and TUI.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import os
from datetime import datetime
from .config import Config


class LogConfig:
    """Centralized logging configuration for CheckMate."""
    
    def __init__(self, config: Config = None):
        """Initialize logging configuration."""
        self.config = config or Config()
        self._loggers: Dict[str, logging.Logger] = {}
    
    def setup_logging(
        self,
        app_name: str = "checkmate",
        level: int = logging.INFO,
        enable_console: bool = True,
        enable_file: bool = True
    ) -> logging.Logger:
        """
        Set up logging with rotation and formatting.
        
        Args:
            app_name: Name of the application (used for log file name)
            level: Logging level
            enable_console: Whether to enable console output
            enable_file: Whether to enable file output
            
        Returns:
            Logger instance configured for the application
        """
        # Create logs directory
        log_dir = self.config.directories["logs"]
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(app_name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # File handler with rotation
        if enable_file:
            log_file = log_dir / f"{app_name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                mode='a'
            )
            
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '[%(levelname)s] %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # Store logger reference
        self._loggers[app_name] = logger
        
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name, creating it if it doesn't exist.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = self.setup_logging(name)
        return self._loggers[name]
    
    def get_operation_logger(self, operation: str) -> logging.Logger:
        """
        Get a logger for a specific operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Logger configured for the specific operation
        """
        logger_name = f"checkmate.{operation}"
        return self.get_logger(logger_name)
    
    def setup_gui_logger(self, text_widget: Any = None) -> logging.Logger:
        """
        Set up logging for GUI applications with optional text widget output.
        
        Args:
            text_widget: Optional text widget for GUI output
            
        Returns:
            Logger configured for GUI
        """
        logger = self.setup_logging("gui", enable_console=False)
        
        if text_widget:
            gui_handler = GUILogHandler(text_widget)
            gui_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
            gui_handler.setFormatter(gui_formatter)
            logger.addHandler(gui_handler)
        
        return logger
    
    def setup_tui_logger(self) -> logging.Logger:
        """
        Set up logging for TUI applications.
        
        Returns:
            Logger configured for TUI
        """
        return self.setup_logging("tui", enable_console=False)


class GUILogHandler(logging.Handler):
    """Custom log handler for GUI text widgets."""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        """Emit a log record to the text widget."""
        try:
            msg = self.format(record)
            # Use after_idle to ensure thread safety
            if hasattr(self.text_widget, 'after_idle'):
                self.text_widget.after_idle(self._append_text, msg + '\n')
            else:
                self._append_text(msg + '\n')
        except Exception:
            self.handleError(record)
    
    def _append_text(self, text):
        """Append text to the widget."""
        try:
            self.text_widget.insert('end', text)
            self.text_widget.see('end')
        except Exception:
            pass


# Global instance for convenience
default_log_config = LogConfig()

# Convenience functions
def setup_logging(app_name: str = "checkmate", **kwargs) -> logging.Logger:
    """Convenience function for setting up logging."""
    return default_log_config.setup_logging(app_name, **kwargs)

def get_operation_logger(operation: str) -> logging.Logger:
    """Convenience function for getting operation logger."""
    return default_log_config.get_operation_logger(operation)
