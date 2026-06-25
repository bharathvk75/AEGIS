"""
AEGIS - Real-Time Edge Video Analytics System
A local-first, privacy-focused video analytics platform with AI-powered notifications.
"""

__version__ = "1.0.0"
__author__ = "AEGIS Team"
__description__ = "Real-Time Edge Video Analytics System"

from core.config import get_config
from core.storage.database import get_db
from core.storage.storage_manager import get_storage
from core.ai.llm_clients import get_llm_manager
from core.agent.hermes import get_hermes
from core.camera.capture import get_camera_manager

__all__ = [
    'get_config',
    'get_db',
    'get_storage',
    'get_llm_manager',
    'get_hermes',
    'get_camera_manager',
]