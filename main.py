#!/usr/bin/env python3
"""
AEGIS - Real-Time Edge Video Analytics System
Local, private, AI-powered video analytics with Hermes Agent notifications
"""

import sys
import os
import logging
from pathlib import Path


def setup_logging():
    log_dir = Path('data/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'aegis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logger = logging.getLogger('AEGIS')
    logger.info('AEGIS starting...')
    return logger


def check_dependencies():
    missing = []
    required = {
        'customtkinter': 'customtkinter',
        'cv2': 'opencv-python',
        'sqlalchemy': 'sqlalchemy',
        'PIL': 'pillow',
        'yaml': 'pyyaml',
        'httpx': 'httpx',
        'requests': 'requests',
        'twilio': 'twilio'
    }
    
    for lib, pkg in required.items():
        try:
            __import__(lib)
        except ImportError:
            missing.append(pkg)
    
    return missing


def main():
    logger = setup_logging()
    
    try:
        logger.info("Initializing AEGIS Web Application...")
        
        import run_aegis
        run_aegis.main()
        
    except Exception as e:
        logger.exception(f"AEGIS crashed: {e}")
        sys.exit(1)
    
    logger.info("AEGIS shutdown complete")


if __name__ == '__main__':
    main()