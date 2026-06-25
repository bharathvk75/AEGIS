import yaml
import os
from pathlib import Path
from typing import Any, Optional

CONFIG_FILE = 'config/config.yaml'


class Config:
    _instance = None
    _data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            with open(config_path, 'r') as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = self._default_config()
            self._save()
    
    def _default_config(self):
        return {
            'app': {
                'name': 'AEGIS',
                'version': '1.0.0',
                'theme': 'dark',
                'min_to_tray': True
            },
            'storage': {
                'max_size_gb': 50,
                'auto_erase': True,
                'strategy': 'fifo',
                'retention': {
                    'snapshots_days': 7,
                    'clips_days': 3,
                    'logs_days': 30
                },
                'volumes_path': 'data/volumes'
            },
            'database': {
                'path': 'data/aegis.db'
            },
            'ollama': {
                'host': 'http://localhost:11434',
                'default_model': 'llava'
            },
            'lmstudio': {
                'host': 'http://localhost:1234',
                'enabled': False
            },
            'external_ai': {
                'enabled': False,
                'providers': []
            },
            'hermes': {
                'check_interval': 2,
                'max_events_in_memory': 100
            },
            'camera': {
                'default_fps': 10,
                'buffer_size': 5,
                'reconnect_attempts': 3,
                'reconnect_delay': 5
            },
            'logging': {
                'level': 'INFO',
                'path': 'data/logs',
                'max_size_mb': 100,
                'backup_count': 5
            }
        }
    
    def _save(self):
        config_path = Path(CONFIG_FILE)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        d = self._data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self._save()
    
    def get_section(self, section: str) -> dict:
        return self._data.get(section, {})
    
    def reload(self):
        self._load()
    
    @property
    def data(self) -> dict:
        return self._data


def get_config() -> Config:
    return Config()