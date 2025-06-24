"""
Configuration management for DiskImage application.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple, Optional, Any
import json
import logging

from .constants import DEFAULT_CONFIG, CONFIG_FILE
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration data class."""
    cleanup_tools: bool = False
    last_output_dir: str = ""
    theme: str = "auto"
    window_size: Tuple[int, int] = (1024, 768)
    buffer_size_mb: int = 64

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        """
        Load configuration from file.
        
        Args:
            config_path: Path to config file, defaults to CONFIG_FILE
            
        Returns:
            AppConfig instance
            
        Raises:
            ConfigError: If config file is corrupted beyond repair
        """
        if config_path is None:
            config_path = CONFIG_FILE
            
        if not config_path.exists():
            logger.info(f"Config file not found, creating default: {config_path}")
            config = cls()
            config.save(config_path)
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Merge with defaults for missing keys
            merged_data = DEFAULT_CONFIG.copy()
            merged_data.update(data)
              # Handle window_size conversion
            window_size: Tuple[int, int] = (1024, 768)
            if 'window_size' in merged_data:
                ws = merged_data['window_size']
                if isinstance(ws, (list, tuple)):
                    try:
                        if len(ws) >= 2:
                            # Safe casting with explicit type checks
                            w, h = ws[0], ws[1]
                            if isinstance(w, (int, float, str)) and isinstance(h, (int, float, str)):
                                window_size = (int(w), int(h))
                    except (ValueError, TypeError, IndexError):
                        window_size = (1024, 768)
            
            # Safely extract and convert values with proper defaults
            buffer_size = 64
            try:
                buffer_size_val = merged_data.get('buffer_size_mb')
                if buffer_size_val is not None:
                    if isinstance(buffer_size_val, (int, float, str)):
                        buffer_size = int(buffer_size_val)
            except (ValueError, TypeError):
                buffer_size = 64
                
            return cls(
                cleanup_tools=bool(merged_data.get('cleanup_tools', True)),
                last_output_dir=str(merged_data.get('last_output_dir', "")),
                theme=str(merged_data.get('theme', "auto")),
                window_size=window_size,
                buffer_size_mb=buffer_size
            )
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Invalid config file, using defaults: {e}")
            return cls()
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}") from e

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Path to save config, defaults to CONFIG_FILE
            
        Raises:
            ConfigError: If unable to save configuration
        """
        if config_path is None:
            config_path = CONFIG_FILE
            
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict and handle tuple serialization
            data = asdict(self)
            if isinstance(data.get('window_size'), tuple):
                data['window_size'] = list(data['window_size'])
                
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Configuration saved to {config_path}")
            
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}") from e

    def update(self, **kwargs: Any) -> None:
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated config: {key} = {value}")
            else:
                logger.warning(f"Unknown config key ignored: {key}")


# Legacy functions for backward compatibility
def load_config() -> dict[str, Any]:
    """Legacy function - returns config as dict."""
    config = AppConfig.load()
    data = asdict(config)
    if isinstance(data.get('window_size'), tuple):
        data['window_size'] = list(data['window_size'])
    return data


def save_config(config_dict: dict[str, Any]) -> None:
    """Legacy function - saves dict as config."""
    try:
        # Convert dict to AppConfig
        if isinstance(config_dict.get('window_size'), list):
            config_dict['window_size'] = tuple(config_dict['window_size'])
        
        config = AppConfig(**config_dict)
        config.save()
    except Exception as e:
        logger.error(f"Failed to save config via legacy function: {e}")


def update_config(updates: dict[str, Any]) -> None:
    """Legacy function - updates config from dict."""
    config = AppConfig.load()
    config.update(**updates)
    config.save()
