import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

DEFAULT_CONFIG = {
    "cleanup_tools": True,
    "last_output_dir": "",
    "theme": "auto",
    "window_size": [1024, 768]
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in config:
                config[k] = v
        return config
    except Exception:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def update_config(updates):
    config = load_config()
    config.update(updates)
    save_config(config)
