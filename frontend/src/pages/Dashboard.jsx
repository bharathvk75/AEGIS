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
  Info,
  Grid,
  Volume2,
  VolumeX,
  Cpu,
  HardDrive,
  Layers,
  Sparkles
} from 'lucide-react';

export default function Dashboard({ stats, socketEvents, setSocketEvents }) {
  const [cameras, setCameras] = useState([]);
  const [events, setEvents] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [gridLayout, setGridLayout] = useState('grid-auto'); // grid-1, grid-2, grid-auto
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [metrics, setMetrics] = useState(null);

  // Fetch cameras, recent events, and system metrics
  useEffect(() => {
    fetchCameras();
    fetchEvents();
    fetchMetrics();
    
    const interval = setInterval(() => {
      fetchCameras();
      fetchMetrics();
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  // Sync real-time events from App WebSocket with optional audio alert
  useEffect(() => {
    if (socketEvents.length > 0) {
      const newEvent = socketEvents[0];
      setEvents(prev => [newEvent, ...prev].slice(0, 50));

      if (soundEnabled && (newEvent.severity === 'critical' || newEvent.severity === 'warning')) {
        try {
          const ctx = new (window.AudioContext || window.webkitAudioContext)();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(newEvent.severity === 'critical' ? 880 : 587.33, ctx.currentTime);
          gain.gain.setValueAtTime(0.1, ctx.currentTime);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          osc.stop(ctx.currentTime + 0.25);
        } catch (e) {
          // Audio context suppressed by browser policy if unclicked
        }
      }
    }
  }, [socketEvents, soundEnabled]);

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

  const fetchMetrics = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/system/metrics');
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error("Error fetching metrics:", err);
    }
  };

  const clearEvents = () => {
    setEvents([]);
    setSocketEvents([]);
  };

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Dashboard</h1>
            <span className="v2-badge">v2.0 HUD</span>
          </div>
          <p className="page-subtitle">Real-time edge video intelligence & AI multi-stream monitor</p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            className="grid-btn"
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? "Mute alert chime" : "Enable alert chime"}
            style={{ padding: '8px 14px', borderRadius: '8px' }}
          >
            {soundEnabled ? <Volume2 size={16} className="text-teal" /> : <VolumeX size={16} className="text-muted" />}
            <span>{soundEnabled ? "Audio Alert ON" : "Muted"}</span>
          </button>
          
          <div className="live-status-badge">
            <div className="pulsing-dot green" />
            <span className="live-badge-text">HERMES ENGINE ONLINE</span>
          </div>
        </div>
      </header>

      {/* AEGIS V2 Real-Time Hardware & AI Gauges */}
      <section className="metrics-bar-container">
        <div className="metric-gauge-card">
          <div className="metric-gauge-header">
            <span>CPU Load</span>
            <Cpu size={14} className="text-blue" />
          </div>
          <div className="metric-gauge-val">{metrics?.cpu_percent ?? stats?.cpu_percent ?? 0}%</div>
          <div className="progress-track">
            <div 
              className="progress-fill blue" 
              style={{ width: `${metrics?.cpu_percent ?? stats?.cpu_percent ?? 0}%` }} 
            />
          </div>
        </div>

        <div className="metric-gauge-card">
          <div className="metric-gauge-header">
            <span>RAM Usage</span>
            <Layers size={14} className="text-purple" />
          </div>
          <div className="metric-gauge-val">
            {metrics?.memory_percent ?? stats?.memory_percent ?? 0}% ({metrics?.memory_used_gb ?? 0}GB)
          </div>
          <div className="progress-track">
            <div 
              className="progress-fill purple" 
              style={{ width: `${metrics?.memory_percent ?? stats?.memory_percent ?? 0}%` }} 
            />
          </div>
        </div>

        <div className="metric-gauge-card">
          <div className="metric-gauge-header">
            <span>Disk Volume</span>
            <HardDrive size={14} className="text-green" />
          </div>
          <div className="metric-gauge-val">
            {metrics?.storage_percent ?? stats?.storage?.percentage ?? 0}% ({metrics?.storage_used_gb ?? 0}GB)
          </div>
          <div className="progress-track">
            <div 
              className="progress-fill green" 
              style={{ width: `${metrics?.storage_percent ?? stats?.storage?.percentage ?? 0}%` }} 
            />
          </div>
        </div>

        <div className="metric-gauge-card">
          <div className="metric-gauge-header">
            <span>Active Feeds</span>
            <Video size={14} className="text-amber" />
          </div>
          <div className="metric-gauge-val">
            {metrics?.active_cameras ?? stats?.cameras?.active ?? 0}/{metrics?.total_cameras ?? stats?.cameras?.total ?? 0}
          </div>
          <div className="progress-track">
            <div 
              className="progress-fill amber" 
              style={{ 
                width: `${((metrics?.active_cameras || 1) / (metrics?.total_cameras || 1)) * 100}%` 
              }} 
            />
          </div>
        </div>
      </section>

      {/* Main Grid Content */}
      <div className="dashboard-content-layout">
        
        {/* Left Column: Camera Feeds with Grid Layout Switcher */}
        <section className="camera-feeds-section">
          <div className="section-header-row">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2>Live Camera Grid</h2>
              <span className="section-meta">{cameras.length} feed{cameras.length !== 1 ? 's' : ''}</span>
            </div>

            {/* Grid Layout Switcher */}
            <div className="grid-controls">
              <button 
                className={`grid-btn ${gridLayout === 'grid-1' ? 'active' : ''}`}
                onClick={() => setGridLayout('grid-1')}
                title="Single Large Feed"
              >
                1x1
              </button>
              <button 
                className={`grid-btn ${gridLayout === 'grid-2' ? 'active' : ''}`}
                onClick={() => setGridLayout('grid-2')}
                title="2x2 Grid View"
              >
                2x2
              </button>
              <button 
                className={`grid-btn ${gridLayout === 'grid-auto' ? 'active' : ''}`}
                onClick={() => setGridLayout('grid-auto')}
                title="Responsive Multi-Grid"
              >
                Auto Grid
              </button>
            </div>
          </div>

          {cameras.length === 0 ? (
            <div className="empty-state-card">
              <Video size={40} className="empty-state-icon" />
              <h3>No Camera Feeds Connected</h3>
              <p>Add webcams, RTSP streams, or local files in the Cameras page to begin monitoring.</p>
            </div>
          ) : (
            <div className={`camera-grid-layout ${gridLayout}`}>
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
                          title="Expand Fullscreen Stream"
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
                          <span>Connecting Edge Stream...</span>
                        </div>
                      )
                    ) : (
                      <div className="feed-placeholder disabled">
                        <span>Camera Feed Disabled</span>
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2>Live Event Stream</h2>
              <Sparkles size={14} className="text-amber" />
            </div>
            <button className="clear-btn" onClick={clearEvents} title="Clear logs">
              <Trash2 size={14} />
              <span>Clear</span>
            </button>
          </div>

          <div className="event-list-wrapper">
            {events.length === 0 ? (
              <div className="empty-events">
                <Activity size={24} className="empty-events-icon" />
                <span>No events recorded. Hermes AI is actively scanning camera feeds.</span>
              </div>
            ) : (
              <div className="event-list">
                {events.map((ev, index) => (
                  <div key={ev.id || index} className={`event-card-item ${getSeverityClass(ev.severity)}`}>
                    <div className="event-card-left">
                      {getSeverityIcon(ev.severity)}
                      <div className="event-details">
                        <div className="event-main-line">
                          <span className="event-source">{ev.camera_name || 'Camera'}:</span>
                          <span className="event-desc">{ev.description || ev.event_type}</span>
                        </div>
                        <div className="event-meta-line">
                          <span className="event-time">
                            {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ev.timestamp}
                          </span>
                          {ev.confidence > 0 && (
                            <span className="event-conf">
                              &bull;&nbsp;&nbsp;{(ev.confidence * 100).toFixed(0)}% AI Conf.
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    {ev.snapshot_path && (
                      <button 
                        className="view-snapshot-btn" 
                        onClick={() => setSelectedSnapshot(ev.snapshot_path)}
                        title="View Annotated Vision Snapshot"
                      >
                        <Eye size={12} />
                        <span>HUD Vision</span>
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
                <h3>{selectedCamera.name} — AEGIS V2 Live Feed</h3>
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
                <div className="info-badge">Engine: Hermes Edge V2</div>
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
              <h3>AEGIS V2 HUD Vision Snapshot</h3>
              <button className="modal-close-btn" onClick={() => setSelectedSnapshot(null)}>&times;</button>
            </div>
            <div className="modal-body snapshot-body">
              <img 
                src={`http://localhost:8000/api/storage/files/${selectedSnapshot}`} 
                alt="Vision Alert Snapshot" 
                className="vision-snapshot-large"
              />
              <div className="snapshot-footer-meta">
                <span>Annotated event snapshot processed by AEGIS Edge V2 engine.</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
