import React, { useState, useEffect } from 'react';
import { 
  Video, 
  Plus, 
  Trash2, 
  Power, 
  Info, 
  Camera, 
  FileVideo, 
  Link2 
} from 'lucide-react';

export default function Cameras() {
  const [cameras, setCameras] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState('');
  const [sourceType, setSourceType] = useState('usb');
  const [sourceUrl, setSourceUrl] = useState('0');
  const [fps, setFps] = useState(10);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCameras();
  }, []);

  const fetchCameras = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/cameras');
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
      }
    } catch (err) {
      console.error("Error loading cameras:", err);
    }
  };

  const handleToggleEnabled = async (cam) => {
    try {
      const res = await fetch(`http://localhost:8000/api/cameras/${cam.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !cam.enabled })
      });
      if (res.ok) {
        fetchCameras();
      }
    } catch (err) {
      console.error("Error toggling camera:", err);
    }
  };

  const handleDeleteCamera = async (id) => {
    if (!window.confirm("Are you sure you want to remove this camera?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/cameras/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchCameras();
      }
    } catch (err) {
      console.error("Error deleting camera:", err);
    }
  };

  // Quick Add Integrated Webcam
  const handleQuickAddWebcam = async () => {
    try {
      setError('');
      setSuccess('');
      const payload = {
        name: "Integrated Webcam",
        source_type: "usb",
        source_url: "0",
        fps: 10
      };
      const res = await fetch('http://localhost:8000/api/cameras', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setSuccess("Integrated webcam added successfully!");
        fetchCameras();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to add webcam.");
      }
    } catch (err) {
      setError("Network error adding webcam.");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError("Please enter a name.");
      return;
    }
    if (!sourceUrl.trim()) {
      setError("Please enter a source URL or Device ID.");
      return;
    }

    try {
      const payload = {
        name,
        source_type: sourceType,
        source_url: sourceUrl,
        fps: parseInt(fps) || 10
      };

      const res = await fetch('http://localhost:8000/api/cameras', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess("Camera added successfully!");
        setName('');
        setSourceUrl('');
        setFps(10);
        setShowAddForm(false);
        fetchCameras();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to add camera.");
      }
    } catch (err) {
      setError("Network error adding camera.");
    }
  };

  const getSourceIcon = (type) => {
    switch (type) {
      case 'usb': return <Camera size={16} />;
      case 'file': return <FileVideo size={16} />;
      default: return <Link2 size={16} />;
    }
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Cameras</h1>
          <p className="page-subtitle">Configure webcam inputs, RTSP network streams, and local video sources</p>
        </div>
        <div className="header-actions">
          <button className="secondary-btn" onClick={handleQuickAddWebcam}>
            <Camera size={14} />
            <span>+ Add Integrated Webcam</span>
          </button>
          <button className="primary-btn" onClick={() => setShowAddForm(!showAddForm)}>
            <Plus size={14} />
            <span>{showAddForm ? "Hide Form" : "Add Camera"}</span>
          </button>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Add Camera Form */}
      {showAddForm && (
        <form className="admin-form-card" onSubmit={handleSubmit}>
          <h3>Add Camera Source</h3>
          <div className="form-grid">
            <div className="form-group">
              <label>Camera Name</label>
              <input 
                type="text" 
                placeholder="e.g. Front Door, Warehouse" 
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Source Type</label>
              <select value={sourceType} onChange={e => {
                setSourceType(e.target.value);
                if (e.target.value === 'usb') setSourceUrl('0');
                else setSourceUrl('');
              }}>
                <option value="usb">Integrated Webcam / USB (Device ID)</option>
                <option value="rtsp">RTSP Network Stream (URL)</option>
                <option value="file">Video File / Loop (Path)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Source URL / Device Index</label>
              <input 
                type="text" 
                placeholder={sourceType === 'usb' ? "0, 1, 2" : sourceType === 'rtsp' ? "rtsp://username:password@ip:port/h264" : "data/videos/test.mp4"}
                value={sourceUrl}
                onChange={e => setSourceUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Frame Rate (FPS)</label>
              <input 
                type="number" 
                min="1" 
                max="30" 
                value={fps}
                onChange={e => setFps(e.target.value)}
              />
            </div>
          </div>

          <div className="form-actions-row">
            <button type="button" className="text-btn" onClick={() => setShowAddForm(false)}>Cancel</button>
            <button type="submit" className="primary-btn">Save Camera Source</button>
          </div>
        </form>
      )}

      {/* Cameras List */}
      <div className="cameras-listing-grid">
        {cameras.length === 0 ? (
          <div className="empty-state-card span-all">
            <Video size={40} className="empty-state-icon" />
            <h3>No Cameras Configured</h3>
            <p>Use the buttons above to add a camera source to start streaming and analytics.</p>
          </div>
        ) : (
          cameras.map(cam => (
            <div key={cam.id} className="camera-admin-card">
              <div className="card-header-row">
                <div className="source-meta">
                  <div className="icon-badge">{getSourceIcon(cam.source_type)}</div>
                  <span className="source-label-type">{cam.source_type.toUpperCase()}</span>
                </div>
                <div className="card-controls">
                  <button 
                    className={`control-btn toggle-active ${cam.enabled ? 'enabled' : 'disabled'}`}
                    onClick={() => handleToggleEnabled(cam)}
                    title={cam.enabled ? "Disable Camera" : "Enable Camera"}
                  >
                    <Power size={14} />
                  </button>
                  <button 
                    className="control-btn delete-btn"
                    onClick={() => handleDeleteCamera(cam.id)}
                    title="Remove Camera"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <div className="card-body">
                <h3 className="camera-title-name">{cam.name}</h3>
                <p className="camera-url-path" title={cam.source_url}>{cam.source_url}</p>
                
                <div className="camera-detail-pills">
                  <span className="detail-pill">FPS: {cam.fps}</span>
                  <span className={`detail-pill status-pill ${cam.status}`}>
                    {cam.status === 'connected' ? '● Connected' : cam.status === 'connecting' ? '● Reconnecting' : '● Disconnected'}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
