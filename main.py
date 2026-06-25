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
    
    missing_deps = check_dependencies()
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        print(f"\n[!] Please install missing dependencies:")
        print(f"    pip install {' '.join(missing_deps)}\n")
        sys.exit(1)
    
    try:
        logger.info("Initializing AEGIS application...")
        
        from gui.app import AEGISApp
        
        logger.info("Starting GUI...")
        app = AEGISApp()
        app.mainloop()
        
    except Exception as e:
        logger.exception(f"AEGIS crashed: {e}")
        sys.exit(1)
    
    logger.info("AEGIS shutdown complete")


if __name__ == '__main__':
    main()