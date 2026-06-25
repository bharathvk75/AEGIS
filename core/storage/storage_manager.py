import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import threading


class StorageManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        from core.config import get_config
        self.config = get_config()
        self.volumes_path = Path(self.config.get('storage.volumes_path', 'data/volumes'))
        self.max_size_bytes = self.config.get('storage.max_size_gb', 50) * 1024 * 1024 * 1024
        self.auto_erase = self.config.get('storage.auto_erase', True)
        self.strategy = self.config.get('storage.strategy', 'fifo')
        self.retention = self.config.get('storage.retention', {})
        self._ensure_directories()
    
    def _ensure_directories(self):
        (self.volumes_path / 'snapshots').mkdir(parents=True, exist_ok=True)
        (self.volumes_path / 'clips').mkdir(parents=True, exist_ok=True)
    
    def get_usage(self) -> Tuple[int, int, float]:
        used = self._calculate_used()
        percentage = (used / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0
        return used, self.max_size_bytes, percentage
    
    def _calculate_used(self) -> int:
        total = 0
        for root, dirs, files in os.walk(self.volumes_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except Exception:

                    pass
        return total
    
    def _get_file_age(self, path: Path) -> timedelta:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            return datetime.now() - mtime
        except Exception:

            return timedelta(days=999)
    
    def _enforce_limit(self) -> int:
        if not self.auto_erase:
            return 0
        deleted = 0
        while self._calculate_used() > self.max_size_bytes:
            oldest = self._get_oldest_file()
            if not oldest:
                break
            try:
                oldest.unlink()
                deleted += 1
            except Exception:

                break
        return deleted
    
    def _get_oldest_file(self) -> Optional[Path]:
        files = []
        for ext in ['*.jpg', '*.png', '*.mp4', '*.avi', '*.mkv']:
            files.extend(self.volumes_path.rglob(ext))
        if not files:
            return None
        if self.strategy == 'oldest_first':
            return min(files, key=lambda f: f.stat().st_mtime)
        return sorted(files, key=lambda f: f.stat().st_mtime)[0]
    
    def _apply_retention(self) -> int:
        deleted = 0
        now = datetime.now()
        snapshots_days = self.retention.get('snapshots_days', 7)
        clips_days = self.retention.get('clips_days', 3)
        logs_days = self.retention.get('logs_days', 30)
        
        snapshots_path = self.volumes_path / 'snapshots'
        clips_path = self.volumes_path / 'clips'
        
        for path, days in [(snapshots_path, snapshots_days), (clips_path, clips_days)]:
            if not path.exists():
                continue
            cutoff = now - timedelta(days=days)
            for f in path.rglob('*'):
                if f.is_file() and self._get_file_age(f) > timedelta(days=days):
                    try:
                        f.unlink()
                        deleted += 1
                    except Exception:

                        pass
        return deleted
    
    def save_snapshot(self, camera_id: int, frame_data: bytes, metadata: dict = None) -> Optional[Path]:
        self._apply_retention()
        snapshot_dir = self.volumes_path / 'snapshots' / f'cam_{camera_id}'
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.jpg"
        path = snapshot_dir / filename
        try:
            with open(path, 'wb') as f:
                f.write(frame_data)
            self._enforce_limit()
            return path
        except Exception:

            return None
    
    def save_clip(self, camera_id: int, clip_data: bytes, metadata: dict = None) -> Optional[Path]:
        self._apply_retention()
        clip_dir = self.volumes_path / 'clips' / f'cam_{camera_id}'
        clip_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.mp4"
        path = clip_dir / filename
        try:
            with open(path, 'wb') as f:
                f.write(clip_data)
            self._enforce_limit()
            return path
        except Exception:

            return None
    
    def get_breakdown(self) -> dict:
        breakdown = {
            'snapshots': {'size': 0, 'count': 0, 'oldest': None},
            'clips': {'size': 0, 'count': 0, 'oldest': None},
            'total': {'size': 0, 'count': 0}
        }
        for category in ['snapshots', 'clips']:
            path = self.volumes_path / category
            if not path.exists():
                continue
            for f in path.rglob('*'):
                if f.is_file():
                    breakdown[category]['size'] += f.stat().st_size
                    breakdown[category]['count'] += 1
                    age = self._get_file_age(f)
                    if breakdown[category]['oldest'] is None or age > timedelta(days=breakdown[category]['oldest'].get('days', 0)):
                        breakdown[category]['oldest'] = {
                            'path': str(f),
                            'days': age.days,
                            'hours': age.seconds // 3600
                        }
        breakdown['total']['size'] = breakdown['snapshots']['size'] + breakdown['clips']['size']
        breakdown['total']['count'] = breakdown['snapshots']['count'] + breakdown['clips']['count']
        return breakdown
    
    def clear_category(self, category: str) -> int:
        count = 0
        path = self.volumes_path / category
        if path.exists():
            for f in path.rglob('*'):
                if f.is_file():
                    try:
                        f.unlink()
                        count += 1
                    except Exception:

                        pass
        return count
    
    def update_settings(self, max_size_gb: int = None, auto_erase: bool = None, strategy: str = None, retention: dict = None):
        if max_size_gb is not None:
            self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
            self.config.set('storage.max_size_gb', max_size_gb)
        if auto_erase is not None:
            self.auto_erase = auto_erase
            self.config.set('storage.auto_erase', auto_erase)
        if strategy is not None:
            self.strategy = strategy
            self.config.set('storage.strategy', strategy)
        if retention is not None:
            self.retention = retention
            self.config.set('storage.retention', retention)
        self._enforce_limit()


def get_storage() -> StorageManager:
    return StorageManager()