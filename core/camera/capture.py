import cv2
import threading
import time
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import queue


class VideoSource(ABC):
    def __init__(self, source_id: str, source_type: str):
        self.source_id = source_id
        self.source_type = source_type
        self._running = False
        self._cap = None
        self._thread = None
        self._frame_queue = queue.Queue(maxsize=5)
        self._latest_frame = None
        self._latest_frame_time = 0
        self._fps = 10
        self._callback = None
        self._status = 'disconnected'
        self._reconnect_attempts = 3
        self._reconnect_delay = 5
    
    @abstractmethod
    def _connect(self) -> bool:
        pass
    
    @abstractmethod
    def _disconnect(self):
        pass
    
    def start(self) -> bool:
        if self._running:
            return True
        if self._connect():
            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            self._status = 'connected'
            return True
        self._status = 'failed'
        return False
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self._disconnect()
        self._status = 'disconnected'
    
    def _capture_loop(self):
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                if not self._reconnect():
                    break
            ret, frame = self._cap.read()
            if ret:
                self._latest_frame = frame
                self._latest_frame_time = time.time()
                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame)
                    except Exception:

                        pass
                if self._callback:
                    self._callback(frame, self)
            else:
                time.sleep(0.1)
                self._reconnect()
    
    def _reconnect(self) -> bool:
        for attempt in range(self._reconnect_attempts):
            self._disconnect()
            time.sleep(self._reconnect_delay)
            if self._connect():
                self._status = 'connected'
                return True
        self._status = 'failed'
        return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        if self._latest_frame is not None and (time.time() - self._latest_frame_time) < 2:
            return self._latest_frame.copy()
        return None
    
    def get_frame_jpeg(self, quality: int = 80) -> Optional[bytes]:
        frame = self.read_frame()
        if frame is not None:
            ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if ret:
                return buf.tobytes()
        return None
    
    def get_latest_frame_bytes(self) -> Optional[bytes]:
        try:
            frame = self._frame_queue.get_nowait()
            ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                return buf.tobytes()
        except Exception:

            pass
        return None
    
    def set_callback(self, callback: Callable):
        self._callback = callback
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def fps(self) -> int:
        return self._fps
    
    @fps.setter
    def fps(self, value: int):
        self._fps = max(1, min(30, value))


class RTSPSource(VideoSource):
    def __init__(self, source_id: str, url: str, fps: int = 10):
        super().__init__(source_id, 'rtsp')
        self.url = url
        self._fps = fps
    
    def _connect(self) -> bool:
        self._cap = cv2.VideoCapture(self.url)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)
        self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        self._cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
        return self._cap.isOpened()
    
    def _disconnect(self):
        if self._cap:
            self._cap.release()
            self._cap = None


class USBSource(VideoSource):
    def __init__(self, source_id: str, device: int = 0, fps: int = 10):
        super().__init__(source_id, 'usb')
        self.device = device
        self._fps = fps
    
    def _connect(self) -> bool:
        import os
        if os.name == 'nt':
            self._cap = cv2.VideoCapture(self.device, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(self.device)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return self._cap.isOpened()
    
    def _disconnect(self):
        if self._cap:
            self._cap.release()
            self._cap = None


class FileSource(VideoSource):
    def __init__(self, source_id: str, file_path: str, loop: bool = True):
        super().__init__(source_id, 'file')
        self.file_path = file_path
        self.loop = loop
        self._total_frames = 0
        self._position = 0
    
    def _connect(self) -> bool:
        self._cap = cv2.VideoCapture(self.file_path)
        if self._cap.isOpened():
            self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            return True
        return False
    
    def _disconnect(self):
        if self._cap:
            self._cap.release()
            self._cap = None
    
    def _capture_loop(self):
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                if not self._reconnect():
                    break
            
            ret, frame = self._cap.read()
            if ret:
                self._latest_frame = frame
                self._latest_frame_time = time.time()
                self._position = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame)
                    except Exception:

                        pass
                
                if self._callback:
                    self._callback(frame, self)
                
                time.sleep(1.0 / self._fps)
            else:
                if self.loop:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self._position = 0
                else:
                    break


class SourceFactory:
    @staticmethod
    def create_source(source_type: str, source_id: str, **kwargs) -> VideoSource:
        source_type = source_type.lower()
        if source_type == 'rtsp':
            return RTSPSource(source_id, kwargs.get('url', ''), kwargs.get('fps', 10))
        elif source_type == 'usb':
            return USBSource(source_id, kwargs.get('device', 0), kwargs.get('fps', 10))
        elif source_type == 'file':
            return FileSource(source_id, kwargs.get('file_path', ''), kwargs.get('loop', True))
        else:
            raise ValueError(f"Unknown source type: {source_type}")


class CameraManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sources: Dict[str, VideoSource] = {}
        self._cameras: Dict[int, Dict[str, Any]] = {}
        self._status_callbacks: List[Callable] = []
        self._load_cameras()
    
    def _load_cameras(self):
        from core.storage.database import get_db, Camera
        db = get_db()
        session = db.get_session()
        try:
            for cam in session.query(Camera).all():
                self._cameras[cam.id] = {
                    'id': cam.id,
                    'name': cam.name,
                    'source_type': cam.source_type,
                    'source_url': cam.source_url,
                    'model_id': cam.model_id,
                    'fps': cam.fps,
                    'enabled': cam.enabled
                }
        finally:
            session.close()
    
    def add_camera(self, camera_id: int, name: str, source_type: str, source_url: str, fps: int = 10, model_id: int = None):
        self._cameras[camera_id] = {
            'id': camera_id,
            'name': name,
            'source_type': source_type,
            'source_url': source_url,
            'fps': fps,
            'model_id': model_id,
            'enabled': True
        }
        self._start_source(camera_id)
        self._notify_status_change()
    
    def remove_camera(self, camera_id: int):
        self.stop_source(camera_id)
        if camera_id in self._cameras:
            del self._cameras[camera_id]
        self._notify_status_change()
    
    def _start_source(self, camera_id: int):
        cam = self._cameras.get(camera_id)
        if not cam:
            return
        
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            return
        
        try:
            if cam['source_type'] == 'rtsp':
                source = SourceFactory.create_source('rtsp', source_key, url=cam['source_url'], fps=cam.get('fps', 10))
            elif cam['source_type'] == 'usb':
                device_id = int(cam['source_url'].replace('/dev/video', '')) if '/' in cam['source_url'] else int(cam['source_url'])
                source = SourceFactory.create_source('usb', source_key, device=device_id, fps=cam.get('fps', 10))
            else:
                source = SourceFactory.create_source('file', source_key, file_path=cam['source_url'], loop=True)
            
            source.start()
            self._sources[source_key] = source
        except Exception as e:
            print(f"Failed to start source for camera {camera_id}: {e}")
    
    def start_source(self, camera_id: int):
        if f"cam_{camera_id}" not in self._sources:
            self._start_source(camera_id)
        self._cameras[camera_id]['enabled'] = True
        self._notify_status_change()
    
    def stop_source(self, camera_id: int):
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            self._sources[source_key].stop()
            del self._sources[source_key]
        self._cameras[camera_id]['enabled'] = False
        self._notify_status_change()
    
    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            return self._sources[source_key].read_frame()
        return None
    
    def get_frame_jpeg(self, camera_id: int) -> Optional[bytes]:
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            return self._sources[source_key].get_frame_jpeg()
        return None
    
    def get_source_status(self, camera_id: int) -> str:
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            return self._sources[source_key].status
        return 'disconnected'
    
    def register_status_callback(self, callback: Callable):
        self._status_callbacks.append(callback)
    
    def _notify_status_change(self):
        for callback in self._status_callbacks:
            try:
                callback(self.get_all_status())
            except Exception:

                pass
    
    def get_all_status(self) -> Dict[str, str]:
        return {
            source_key: source.status 
            for source_key, source in self._sources.items()
        }
    
    def get_all_cameras(self) -> Dict[int, Dict[str, Any]]:
        return self._cameras.copy()
    
    def list_cameras(self) -> list:
        return list(self._cameras.values())
    
    def get_camera(self, camera_id: int) -> Optional[Dict[str, Any]]:
        return self._cameras.get(camera_id)
    
    def start_all(self):
        for camera_id in self._cameras:
            if self._cameras[camera_id].get('enabled', True):
                self._start_source(camera_id)
    
    def stop_all(self):
        for source_key in list(self._sources.keys()):
            self._sources[source_key].stop()
        self._sources.clear()
    
    def set_camera_frame_callback(self, camera_id: int, callback: Callable):
        source_key = f"cam_{camera_id}"
        if source_key in self._sources:
            self._sources[source_key].set_callback(callback)
    
    def reload_cameras(self):
        self.stop_all()
        self._cameras.clear()
        self._load_cameras()
        self.start_all()


def get_camera_manager() -> CameraManager:
    return CameraManager()