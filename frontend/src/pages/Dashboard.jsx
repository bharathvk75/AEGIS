import React, { useState, useEffect } from 'react';
import { 
  Video, 
  AlertTriangle, 
  Activity, 
  Clock, 
  Maximize2, 
  Eye,
  Trash2,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';

export default function Dashboard({ stats, socketEvents, setSocketEvents }) {
  const [cameras, setCameras] = useState([]);
  const [events, setEvents] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);

  // Fetch cameras and recent events
  useEffect(() => {
    fetchCameras();
    fetchEvents();
    
    const interval = setInterval(() => {
      fetchCameras();
    }, 5000); // Poll cameras status every 5s

    return () => clearInterval(interval);
  }, []);

  // Sync real-time events from App WebSocket
  useEffect(() => {
    if (socketEvents.length > 0) {
      const newEvent = socketEvents[0];
      setEvents(prev => [newEvent, ...prev].slice(0, 50));
    }
  }, [socketEvents]);

  const fetchCameras = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/cameras');
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
      }
    } catch (err) {
      console.error("Error fetching cameras:", err);
    }
  };

  const fetchEvents = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/events?limit=30');
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (err) {
      console.error("Error fetching events:", err);
    }
  };

  const clearEvents = () => {
    setEvents([]);
    setSocketEvents([]);
  };

  // Helper to format seconds to human-readable uptime
  const formatUptime = (seconds) => {
    if (!seconds) return '0m';
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    
    const parts = [];
    if (d > 0) parts.push(`${d}d`);
    if (h > 0) parts.push(`${h}h`);
    if (m > 0 || parts.length === 0) parts.push(`${m}m`);
    return parts.join(' ');
  };

  // Severity style helper
  const getSeverityClass = (sev) => {
    switch (sev?.toLowerCase()) {
      case 'critical': return 'severity-critical';
      case 'warning': return 'severity-warning';
      default: return 'severity-info';
    }
  };

  const getSeverityIcon = (sev) => {
    switch (sev?.toLowerCase()) {
      case 'critical': return <AlertCircle size={14} className="sev-icon text-critical" />;
      case 'warning': return <AlertTriangle size={14} className="sev-icon text-warning" />;
      default: return <Info size={14} className="sev-icon text-info" />;
    }
  };

  return (
    <div className="page-container">
      {/* Dashboard Header */}
      <header className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Real-time edge surveillance and security metrics</p>
        </div>
        <div className="live-status-badge">
          <div className="pulsing-dot green" />
          <span className="live-badge-text">LIVE MONITORING</span>
        </div>
      </header>

      {/* Stats Grid */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <Video size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-value">{stats?.cameras?.active ?? 0}/{stats?.cameras?.total ?? 0}</span>
            <span className="stat-label">Active Cameras</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper teal">
            <Activity size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-value">{events.length}</span>
            <span className="stat-label">Events Logged</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper red">
            <AlertTriangle size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-value">
              {events.filter(e => e.severity === 'critical' || e.severity === 'warning').length}
            </span>
            <span className="stat-label">Active Alerts</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <Clock size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-value">{formatUptime(stats?.hermes?.uptime)}</span>
            <span className="stat-label">System Uptime</span>
          </div>
        </div>
      </section>

      {/* Main Grid Content */}
      <div className="dashboard-content-layout">
        
        {/* Left Column: Camera Feeds */}
        <section className="camera-feeds-section">
          <div className="section-header-row">
            <h2>Camera Feeds</h2>
            <span className="section-meta">{cameras.length} source{cameras.length !== 1 ? 's' : ''}</span>
          </div>

          {cameras.length === 0 ? (
            <div className="empty-state-card">
              <Video size={40} className="empty-state-icon" />
              <h3>No Camera Feeds Connected</h3>
              <p>Add integrated webcams, RTSP streams, or local files in the Cameras page to begin monitoring.</p>
            </div>
          ) : (
            <div className="camera-grid">
              {cameras.map(cam => (
                <div key={cam.id} className="camera-tile">
                  <div className="camera-tile-header">
                    <div className="camera-identity">
                      <div className={`status-indicator-dot ${cam.status === 'connected' ? 'green' : 'red'}`} />
                      <span className="camera-name">{cam.name}</span>
                    </div>
                    <div className="camera-actions">
                      {cam.status === 'connected' && (
                        <button 
                          className="tile-action-btn"
                          onClick={() => setSelectedCamera(cam)}
                          title="Expand Stream"
                        >
                          <Maximize2 size={12} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="camera-video-container">
                    {cam.enabled ? (
                      cam.status === 'connected' ? (
                        <img 
                          src={`http://localhost:8000/api/cameras/${cam.id}/stream?t=${Date.now()}`} 
                          alt={cam.name} 
                          className="camera-feed-img"
                        />
                      ) : (
                        <div className="feed-placeholder loading">
                          <div className="spinner" />
                          <span>Connecting Stream...</span>
                        </div>
                      )
                    ) : (
                      <div className="feed-placeholder disabled">
                        <span>Camera Disabled</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Right Column: Event Feed */}
        <section className="event-feed-section">
          <div className="section-header-row">
            <h2>Event Feed</h2>
            <button className="clear-btn" onClick={clearEvents} title="Clear logs">
              <Trash2 size={14} />
              <span>Clear</span>
            </button>
          </div>

          <div className="event-list-wrapper">
            {events.length === 0 ? (
              <div className="empty-events">
                <Activity size={24} className="empty-events-icon" />
                <span>No events recorded today</span>
              </div>
            ) : (
              <div className="event-list">
                {events.map((ev, index) => (
                  <div key={ev.id || index} className={`event-card-item ${getSeverityClass(ev.severity)}`}>
                    <div className="event-card-left">
                      {getSeverityIcon(ev.severity)}
                      <div className="event-details">
                        <div className="event-main-line">
                          <span className="event-source">{ev.camera_name || 'System'}:</span>
                          <span className="event-desc">{ev.description || ev.event_type}</span>
                        </div>
                        <div className="event-meta-line">
                          <span className="event-time">
                            {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ev.timestamp}
                          </span>
                          {ev.confidence > 0 && (
                            <span className="event-conf">
                              &bull;&nbsp;&nbsp;{(ev.confidence * 100).toFixed(0)}% Confidence
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    {ev.snapshot_path && (
                      <button 
                        className="view-snapshot-btn" 
                        onClick={() => setSelectedSnapshot(ev.snapshot_path)}
                        title="View Snapshot"
                      >
                        <Eye size={12} />
                        <span>Vision</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

      </div>

      {/* Expanded Camera Modal */}
      {selectedCamera && (
        <div className="modal-backdrop" onClick={() => setSelectedCamera(null)}>
          <div className="modal-content large-view" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <div className={`status-indicator-dot ${selectedCamera.status === 'connected' ? 'green' : 'red'}`} />
                <h3>{selectedCamera.name} — Live Analytics Stream</h3>
              </div>
              <button className="modal-close-btn" onClick={() => setSelectedCamera(null)}>&times;</button>
            </div>
            <div className="modal-body">
              <div className="expanded-video-wrapper">
                <img 
                  src={`http://localhost:8000/api/cameras/${selectedCamera.id}/stream`} 
                  alt={selectedCamera.name} 
                  className="expanded-video-feed"
                />
              </div>
              <div className="expanded-video-details">
                <div className="info-badge">Source: {selectedCamera.source_type.toUpperCase()}</div>
                <div className="info-badge">Configured FPS: {selectedCamera.fps}</div>
                <div className="info-badge">Location: Edge Processor</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Vision Snapshot Preview Modal */}
      {selectedSnapshot && (
        <div className="modal-backdrop" onClick={() => setSelectedSnapshot(null)}>
          <div className="modal-content medium-view" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Hermes Vision Snapshot</h3>
              <button className="modal-close-btn" onClick={() => setSelectedSnapshot(null)}>&times;</button>
            </div>
            <div className="modal-body snapshot-body">
              <img 
                src={`http://localhost:8000/api/storage/files/${selectedSnapshot}`} 
                alt="Vision Alert Snapshot" 
                className="vision-snapshot-large"
              />
              <div className="snapshot-footer-meta">
                <span>Alert Snapshot captured at Edge. Fully private local storage.</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
