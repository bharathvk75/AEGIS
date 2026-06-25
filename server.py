#!/usr/bin/env python3
import asyncio
import os
import sys
import time
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

# Add current directory to path so we can import core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import get_config
from core.camera.capture import get_camera_manager
from core.agent.hermes import get_hermes
from core.storage.database import get_db, Camera, Model, Event, NotificationChannel, Trigger
from core.storage.storage_manager import get_storage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AEGIS-Backend")

app = FastAPI(title="AEGIS Edge API", version="1.0.0")

# Enable CORS for the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []
# Async queue for thread-safe Hermes events
event_queue = asyncio.Queue()

# --- Pydantic Request Models ---
class CameraCreate(BaseModel):
    name: str
    source_type: str
    source_url: str
    fps: int = 10
    model_id: Optional[int] = None

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    enabled: Optional[bool] = None
    fps: Optional[int] = None
    model_id: Optional[int] = None

class ModelConfig(BaseModel):
    provider: str
    host: Optional[str] = None
    enabled: bool = True
    default_model: Optional[str] = None
    api_key: Optional[str] = None

class ChannelCreate(BaseModel):
    name: str
    channel_type: str
    config: Dict[str, Any]

class TriggerCreate(BaseModel):
    name: str
    camera_id: Optional[int] = None
    condition_text: str
    notification_ids: List[int]
    enabled: bool = True
    capture_snapshot: bool = True
    capture_clip: bool = False
    clip_duration: int = 30

# --- Live Streaming Utility ---
def generate_mjpeg_stream(camera_id: int):
    cam_mgr = get_camera_manager()
    logger.info(f"Starting MJPEG stream for camera {camera_id}")
    
    # Ensure source is started
    cam_mgr.start_source(camera_id)
    
    try:
        while True:
            frame_bytes = cam_mgr.get_frame_jpeg(camera_id)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # If frame is not available, yield a small delay to prevent CPU spinning
                time.sleep(0.1)
            time.sleep(1.0 / cam_mgr.get_camera(camera_id).get('fps', 10))
    except GeneratorExit:
        logger.info(f"Stream client disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"Error in MJPEG stream for camera {camera_id}: {e}")

# --- Background Worker for WebSockets ---
async def broadcast_worker():
    while True:
        try:
            event = await event_queue.get()
            result = event.get('event_result', {})
            
            # Format event data for the client
            data = {
                'id': int(time.time() * 1000), # temporary id
                'camera_name': result.get('camera_name', 'Unknown'),
                'event_type': result.get('event_type', 'Alert'),
                'description': result.get('description', ''),
                'confidence': result.get('confidence', 0.0),
                'severity': result.get('severity', 'info'),
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'snapshot_path': result.get('snapshot_path')
            }
            
            # Broadcast to all connected WebSockets
            disconnected = []
            for connection in active_connections:
                try:
                    await connection.send_json(data)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up disconnected sockets
            for conn in disconnected:
                if conn in active_connections:
                    active_connections.remove(conn)
                    
            event_queue.task_done()
        except Exception as e:
            logger.error(f"Error in broadcast worker: {e}")
            await asyncio.sleep(1)

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    # Start the broadcast worker
    asyncio.create_task(broadcast_worker())
    
    # Register Hermes callback to push events into the async queue
    loop = asyncio.get_running_loop()
    
    def on_hermes_event(event):
        loop.call_soon_threadsafe(event_queue.put_nowait, event)
        
    hermes = get_hermes()
    hermes.register_event_callback(on_hermes_event)
    logger.info("Registered Hermes real-time event listener")
    
    # Start all cameras automatically
    cam_mgr = get_camera_manager()
    cam_mgr.start_all()
    logger.info("Initialized camera feeds")

# --- Shutdown Event ---
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down AEGIS backend...")
    try:
        get_camera_manager().stop_all()
    except Exception:
        pass
    try:
        get_hermes().stop()
    except Exception:
        pass

# ==========================================
#                  REST APIs
# ==========================================

# --- System & Status ---
@app.get("/api/status")
def get_system_status():
    try:
        # CPU & Memory
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Storage usage
        storage = get_storage()
        used, total, percentage = storage.get_usage()
        
        # Hermes stats
        hermes = get_hermes()
        h_stats = hermes.get_stats()
        
        # Active cameras
        cam_mgr = get_camera_manager()
        cameras = cam_mgr.get_all_cameras()
        active_cams = sum(1 for cid in cameras if cam_mgr.get_source_status(cid) == 'connected')
        
        return {
            "status": "online",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "storage": {
                "used_gb": used / (1024**3),
                "total_gb": total / (1024**3),
                "percentage": percentage
            },
            "hermes": {
                "uptime": h_stats.get("uptime", 0),
                "triggers_active": h_stats.get("triggers_active", 0),
                "notifications_sent": h_stats.get("notifications_sent", 0),
                "last_event_time": h_stats.get("last_event")
            },
            "cameras": {
                "active": active_cams,
                "total": len(cameras)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Camera Endpoints ---
@app.get("/api/cameras")
def list_cameras():
    db = get_db()
    session = db.get_session()
    try:
        cameras = session.query(Camera).all()
        cam_mgr = get_camera_manager()
        
        result = []
        for cam in cameras:
            result.append({
                "id": cam.id,
                "name": cam.name,
                "source_type": cam.source_type,
                "source_url": cam.source_url,
                "enabled": cam.enabled,
                "fps": cam.fps,
                "model_id": cam.model_id,
                "status": cam_mgr.get_source_status(cam.id)
            })
        return result
    finally:
        session.close()

@app.post("/api/cameras")
def add_camera(cam_data: CameraCreate):
    db = get_db()
    session = db.get_session()
    try:
        camera = Camera(
            name=cam_data.name,
            source_type=cam_data.source_type,
            source_url=cam_data.source_url,
            fps=cam_data.fps,
            model_id=cam_data.model_id,
            enabled=True
        )
        session.add(camera)
        session.commit()
        
        # Start in CameraManager
        cam_mgr = get_camera_manager()
        cam_mgr.add_camera(
            camera_id=camera.id,
            name=camera.name,
            source_type=camera.source_type,
            source_url=camera.source_url,
            fps=camera.fps,
            model_id=camera.model_id
        )
        
        # Force reload Hermes triggers
        get_hermes().reload()
        
        return {"success": True, "id": camera.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.put("/api/cameras/{id}")
def update_camera(id: int, cam_data: CameraUpdate):
    db = get_db()
    session = db.get_session()
    try:
        camera = session.query(Camera).filter_by(id=id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
            
        cam_mgr = get_camera_manager()
        
        if cam_data.name is not None:
            camera.name = cam_data.name
        if cam_data.source_type is not None:
            camera.source_type = cam_data.source_type
        if cam_data.source_url is not None:
            camera.source_url = cam_data.source_url
        if cam_data.fps is not None:
            camera.fps = cam_data.fps
        if cam_data.model_id is not None:
            camera.model_id = cam_data.model_id
            
        if cam_data.enabled is not None:
            camera.enabled = cam_data.enabled
            if cam_data.enabled:
                cam_mgr.start_source(id)
            else:
                cam_mgr.stop_source(id)
                
        session.commit()
        
        # Reload camera inside manager
        cam_mgr.reload_cameras()
        get_hermes().reload()
        
        return {"success": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.delete("/api/cameras/{id}")
def delete_camera(id: int):
    db = get_db()
    session = db.get_session()
    try:
        camera = session.query(Camera).filter_by(id=id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
            
        session.delete(camera)
        session.commit()
        
        # Stop in CameraManager
        cam_mgr = get_camera_manager()
        cam_mgr.remove_camera(id)
        
        # Force reload Hermes
        get_hermes().reload()
        
        return {"success": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/cameras/{id}/stream")
def get_camera_stream(id: int):
    cam_mgr = get_camera_manager()
    camera = cam_mgr.get_camera(id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    return StreamingResponse(
        generate_mjpeg_stream(id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# --- AI Model Endpoints ---
@app.get("/api/models")
def list_models():
    # Expose current AI config
    config = get_config()
    return {
        "ollama": {
            "host": config.get("ollama.host"),
            "default_model": config.get("ollama.default_model"),
            "enabled": True
        },
        "lmstudio": {
            "host": config.get("lmstudio.host"),
            "enabled": config.get("lmstudio.enabled", False)
        },
        "gemini": {
            "enabled": config.get("external_ai.enabled", False),
            "has_key": bool(config.get("external_ai.providers")) or bool(os.getenv("GEMINI_API_KEY"))
        }
    }

@app.post("/api/models/connect")
def connect_model(config_data: ModelConfig):
    config = get_config()
    provider = config_data.provider.lower()
    
    try:
        if provider == "ollama":
            if config_data.host:
                config.set("ollama.host", config_data.host)
            if config_data.default_model:
                config.set("ollama.default_model", config_data.default_model)
        elif provider == "lmstudio":
            if config_data.host:
                config.set("lmstudio.host", config_data.host)
            config.set("lmstudio.enabled", config_data.enabled)
        elif provider == "gemini":
            if config_data.api_key:
                # Save the new Gemini API key
                os.environ["GEMINI_API_KEY"] = config_data.api_key
                config.set("external_ai.enabled", True)
                
        # Trigger manager client check
        from core.ai.llm_clients import get_llm_manager
        manager = get_llm_manager()
        manager.reload_clients()
        clients = manager.check_all_connected()
        
        connected = clients.get(provider, False)
        
        return {"success": True, "connected": connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Hermes Channels Endpoints ---
@app.get("/api/hermes/channels")
def list_channels():
    db = get_db()
    session = db.get_session()
    try:
        channels = session.query(NotificationChannel).all()
        hermes = get_hermes()
        
        result = []
        for ch in channels:
            # get stats from running agent if available
            agent_ch = hermes.get_channel(ch.id)
            stats = agent_ch.stats if agent_ch else (ch.channel_stats or {"sent": 0, "failed": 0})
            
            result.append({
                "id": ch.id,
                "name": ch.name,
                "channel_type": ch.channel_type,
                "config": ch.config,
                "enabled": ch.enabled,
                "stats": stats
            })
        return result
    finally:
        session.close()

@app.post("/api/hermes/channels")
def add_channel(ch_data: ChannelCreate):
    try:
        hermes = get_hermes()
        config = {
            **ch_data.config,
            "name": ch_data.name,
            "type": ch_data.channel_type
        }
        channel_id = hermes.add_channel(ch_data.channel_type, config)
        return {"success": True, "id": channel_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/hermes/channels/{id}")
def delete_channel(id: int):
    try:
        hermes = get_hermes()
        hermes.delete_channel(id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hermes/channels/{id}/test")
async def test_channel(id: int):
    try:
        hermes = get_hermes()
        success = await hermes.test_channel(id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Hermes Triggers Endpoints ---
@app.get("/api/hermes/triggers")
def list_triggers():
    db = get_db()
    session = db.get_session()
    try:
        triggers = session.query(Trigger).all()
        
        result = []
        for tg in triggers:
            result.append({
                "id": tg.id,
                "name": tg.name,
                "camera_id": tg.camera_id,
                "condition_text": tg.condition_text,
                "notification_ids": tg.notification_ids_list,
                "enabled": tg.enabled,
                "capture_snapshot": tg.capture_snapshot,
                "capture_clip": tg.capture_clip,
                "clip_duration": tg.clip_duration
            })
        return result
    finally:
        session.close()

@app.post("/api/hermes/triggers")
def add_trigger(tg_data: TriggerCreate):
    try:
        hermes = get_hermes()
        trigger_dict = {
            "name": tg_data.name,
            "camera_id": tg_data.camera_id,
            "condition_text": tg_data.condition_text,
            "notification_ids": tg_data.notification_ids,
            "enabled": tg_data.enabled,
            "capture_snapshot": tg_data.capture_snapshot,
            "capture_clip": tg_data.capture_clip,
            "clip_duration": tg_data.clip_duration
        }
        trigger_id = hermes.add_trigger(trigger_dict)
        return {"success": True, "id": trigger_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/hermes/triggers/{id}")
def delete_trigger(id: int):
    try:
        hermes = get_hermes()
        hermes.delete_trigger(id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hermes/triggers/{id}/toggle")
def toggle_trigger(id: int, body: Dict[str, bool]):
    enabled = body.get("enabled", True)
    try:
        hermes = get_hermes()
        hermes.toggle_trigger(id, enabled)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Events Endpoints ---
@app.get("/api/events")
def list_events(limit: int = 50, camera_id: Optional[int] = None):
    db = get_db()
    session = db.get_session()
    try:
        query = session.query(Event)
        if camera_id is not None:
            query = query.filter_by(camera_id=camera_id)
            
        events = query.order_by(Event.created_at.desc()).limit(limit).all()
        
        result = []
        for ev in events:
            result.append({
                "id": ev.id,
                "camera_id": ev.camera_id,
                "camera_name": ev.camera.name if ev.camera else "Unknown",
                "event_type": ev.event_type,
                "description": ev.description,
                "confidence": ev.confidence,
                "severity": ev.severity,
                "snapshot_path": ev.snapshot_path,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            })
        return result
    finally:
        session.close()

# --- Storage & Asset Serving Endpoints ---
@app.post("/api/storage/clean")
def clean_storage():
    try:
        storage = get_storage()
        cleaned_bytes = storage.clean_old_data()
        return {"success": True, "cleaned_mb": cleaned_bytes / (1024**2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/storage/files/{path:path}")
def serve_file(path: str):
    # Serve snapshot image files safely
    # Check if file exists in the storage path
    config = get_config()
    volumes_base = Path(config.get("storage.volumes_path", "data/volumes")).resolve()
    
    target_path = Path(path).resolve()
    
    # Security check: Ensure the path is within the volumes_base directory
    if not str(target_path).startswith(str(volumes_base)):
        # Try finding relative to current workspace
        target_path = Path(os.path.join(volumes_base, path)).resolve()
        if not str(target_path).startswith(str(volumes_base)):
            raise HTTPException(status_code=403, detail="Access denied")
            
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(str(target_path))

# ==========================================
#                WebSockets
# ==========================================

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"New web client connected. Active connections: {len(active_connections)}")
    try:
        while True:
            # Keep the connection alive by waiting for client messages (if any)
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"Web client disconnected. Active connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# --- Server Runner Entrypoint ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
