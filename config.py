"""
Configuration management for GeminiTask.
Handles API keys, default settings, and other configuration options.
"""

import os
import json
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "priority_default": "medium",
    "api_key": "",
    "date_format": "%Y-%m-%d %H:%M:%S"
}

CONFIG_DIR = Path.home() / ".geminitask"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config():
    """Load configuration from file or create default if it doesn't exist."""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        # Create default config file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If config file is corrupt, recreate it
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file."""
    ensure_config_dir()
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_api_key():
    """Get Gemini API key from environment variable or config file."""
    # Environment variable takes precedence
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        # Fall back to config file
        config = load_config()
        api_key = config.get("api_key", "")
        
    return api_key


def set_api_key(api_key):
    """Save API key to configuration file."""
    config = load_config()
    config["api_key"] = api_key
    save_config(config)
    return True


def get_config_value(key, default=None):
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key, value):
    """Set a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
    return True
