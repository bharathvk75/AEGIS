from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import json

Base = declarative_base()


def _utcnow():
    return datetime.utcnow()


class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(20), default='rtsp')
    source_url = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    model_id = Column(Integer, ForeignKey('models.id'), nullable=True)
    fps = Column(Integer, default=10)
    detection_classes = Column(JSON, default=list)
    sensitivity = Column(Float, default=0.7)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    model = relationship("Model", back_populates="cameras")
    events = relationship("Event", back_populates="camera", cascade='all, delete-orphan')
    triggers = relationship("Trigger", back_populates="camera", cascade='all, delete-orphan')


class Model(Base):
    __tablename__ = 'models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(20), nullable=False)
    endpoint = Column(Text, nullable=True)
    api_key = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    is_local = Column(Boolean, default=True)
    model_stats = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)
    
    cameras = relationship("Camera", back_populates="model")


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=False)
    event_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    severity = Column(String(20), default='info')
    snapshot_path = Column(Text, nullable=True)
    video_path = Column(Text, nullable=True)
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)
    
    camera = relationship("Camera", back_populates="events")


class NotificationChannel(Base):
    __tablename__ = 'notification_channels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    channel_type = Column(String(30), nullable=False)
    config_json = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    channel_stats = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    @property
    def config(self):
        return json.loads(self.config_json)
    
    @config.setter
    def config(self, value):
        self.config_json = json.dumps(value)


class Trigger(Base):
    __tablename__ = 'triggers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    camera_id = Column(Integer, ForeignKey('cameras.id'), nullable=True)
    condition_text = Column(Text, nullable=False)
    condition_config = Column(JSON, default=dict)
    notification_channel_ids = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    capture_snapshot = Column(Boolean, default=True)
    capture_clip = Column(Boolean, default=False)
    clip_duration = Column(Integer, default=30)
    trigger_stats = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)
    
    camera = relationship("Camera", back_populates="triggers")
    
    @property
    def notification_ids_list(self):
        if not self.notification_channel_ids:
            return []
        return [int(x.strip()) for x in self.notification_channel_ids.split(',') if x.strip()]
    
    @notification_ids_list.setter
    def notification_ids_list(self, value):
        self.notification_channel_ids = ','.join(str(x) for x in value)


class StorageMeta(Base):
    __tablename__ = 'storage_meta'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)


class Database:
    _instance = None
    
    def __new__(cls, db_path='data/aegis.db'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path='data/aegis.db'):
        if self._initialized:
            return
        self._initialized = True
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def close(self):
        self.engine.dispose()


def get_db(db_path='data/aegis.db'):
    return Database(db_path)


@contextmanager
def Session():
    db = get_db()
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()