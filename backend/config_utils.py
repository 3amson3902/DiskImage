"""
Configuration management for DiskImage application.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple, Optional
import json
import logging

from .constants import DEFAULT_CONFIG, CONFIG_FILE
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration data class."""
    cleanup_tools: bool = True
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
            
            # Convert window_size list to tuple
            if isinstance(merged_data.get('window_size'), list):
                merged_data['window_size'] = tuple(merged_data['window_size'])
            
            return cls(**merged_data)
            
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

    def update(self, **kwargs) -> None:
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
def load_config() -> dict:
    """Legacy function - returns config as dict."""
    config = AppConfig.load()
    data = asdict(config)
    if isinstance(data.get('window_size'), tuple):
        data['window_size'] = list(data['window_size'])
    return data


def save_config(config_dict: dict) -> None:
    """Legacy function - saves dict as config."""
    try:
        # Convert dict to AppConfig
        if isinstance(config_dict.get('window_size'), list):
            config_dict['window_size'] = tuple(config_dict['window_size'])
        
        config = AppConfig(**config_dict)
        config.save()
    except Exception as e:
        logger.error(f"Failed to save config via legacy function: {e}")


def update_config(updates: dict) -> None:
    """Legacy function - updates config from dict."""
    config = AppConfig.load()
    config.update(**updates)
    config.save()
