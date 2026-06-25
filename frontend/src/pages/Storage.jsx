import React, { useState, useEffect } from 'react';
import { 
  HardDrive, 
  Trash2, 
  Settings, 
  Image, 
  Calendar,
  Layers,
  ZoomIn,
  Save,
  Clock,
  RefreshCw
} from 'lucide-react';

export default function Storage({ stats, fetchStats }) {
  const [cleaning, setCleaning] = useState(false);
  const [cleanMessage, setCleanMessage] = useState('');
  const [galleryEvents, setGalleryEvents] = useState([]);
  const [activeLightbox, setActiveLightbox] = useState(null);

  // Storage config states
  const [maxSizeGb, setMaxSizeGb] = useState(50);
  const [autoErase, setAutoErase] = useState(true);
  const [snapshotsDays, setSnapshotsDays] = useState(7);
  const [clipsDays, setClipsDays] = useState(3);
  const [logsDays, setLogsDays] = useState(30);
  const [configSuccess, setConfigSuccess] = useState('');
  const [configError, setConfigError] = useState('');

  useEffect(() => {
    fetchGalleryEvents();
    fetchStorageConfig();
  }, []);

  const fetchGalleryEvents = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/events?limit=50');
      if (res.ok) {
        const data = await res.json();
        const withSnapshots = data.filter(e => e.snapshot_path);
        setGalleryEvents(withSnapshots);
      }
    } catch (err) {
      console.error("Error loading gallery:", err);
    }
  };

  const fetchStorageConfig = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/storage/config');
      if (res.ok) {
        const data = await res.json();
        setMaxSizeGb(data.max_size_gb || 50);
        setAutoErase(data.auto_erase !== undefined ? data.auto_erase : true);
        if (data.retention) {
          setSnapshotsDays(data.retention.snapshots_days || 7);
          setClipsDays(data.retention.clips_days || 3);
          setLogsDays(data.retention.logs_days || 30);
        }
      }
    } catch (err) {
      console.error("Error loading storage config:", err);
    }
  };

  const handleCleanStorage = async () => {
    setCleaning(true);
    setCleanMessage('');
    try {
      const res = await fetch('http://localhost:8000/api/storage/clean', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setCleanMessage(`Cleanup complete! Successfully freed ${data.cleaned_mb.toFixed(1)} MB of storage space.`);
        fetchStats();
        fetchGalleryEvents();
      } else {
        setCleanMessage('Failed to run storage cleanup.');
      }
    } catch (err) {
      setCleanMessage('Network error running cleanup.');
    } finally {
      setCleaning(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setConfigSuccess('');
    setConfigError('');

    try {
      const res = await fetch('http://localhost:8000/api/storage/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_size_gb: parseInt(maxSizeGb),
          auto_erase: autoErase,
          snapshots_days: parseInt(snapshotsDays),
          clips_days: parseInt(clipsDays),
          logs_days: parseInt(logsDays)
        })
      });

      if (res.ok) {
        setConfigSuccess('Storage configuration saved successfully!');
        fetchStats(); // Update dashboard metric limits
        setTimeout(() => setConfigSuccess(''), 5000);
      } else {
        setConfigError('Failed to save configuration.');
      }
    } catch (err) {
      setConfigError('Network error saving configuration.');
    }
  };

  const handleResetDefaults = (e) => {
    e.preventDefault();
    setMaxSizeGb(50);
    setAutoErase(true);
    setSnapshotsDays(7);
    setClipsDays(3);
    setLogsDays(30);
    setConfigSuccess('Reset to defaults! Click "Save Configuration" to persist.');
    setTimeout(() => setConfigSuccess(''), 5000);
  };

  const handleDeleteEvent = async (id) => {
    if (!window.confirm("Are you sure you want to permanently delete this vision capture event and its snapshot?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/events/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setActiveLightbox(null);
        fetchGalleryEvents();
        if (fetchStats) fetchStats();
      } else {
        alert("Failed to delete the capture event.");
      }
    } catch (err) {
      console.error("Error deleting event:", err);
      alert("Network error deleting capture event.");
    }
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Storage</h1>
          <p className="page-subtitle">Manage edge data volume, retention policies, and browse vision alert captures</p>
        </div>
      </header>

      {/* Storage config and Gauges Grid */}
      <div className="storage-dash-grid">
        
        {/* Resource card */}
        <div className="storage-metric-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="card-top-icon">
            <HardDrive size={24} className="text-blue" />
            <h3>Disk Allocation</h3>
          </div>
          <div className="disk-gauge-section">
            <div className="disk-fraction">
              <span className="used-number">{(stats?.storage?.used_gb ?? 0).toFixed(2)}</span>
              <span className="slash">/</span>
              <span className="total-number">{(stats?.storage?.total_gb ?? maxSizeGb).toFixed(0)} GB</span>
            </div>
            <div className="gauge-bar-wrapper">
              <div 
                className="gauge-bar-fill"
                style={{ width: `${stats?.storage?.percentage ?? 0}%` }}
              />
            </div>
            <div className="gauge-labels">
              <span>{stats?.storage?.percentage ?? 0}% Allocated</span>
              <span>{(stats?.storage?.total_gb - stats?.storage?.used_gb).toFixed(2)} GB Free</span>
            </div>
          </div>
          <div style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Disk allocation represents the space AEGIS is permitted to occupy. You can configure this threshold on the right.
            </p>
          </div>
        </div>

        {/* Maintenance card */}
        <div className="storage-maintenance-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card-top-icon">
            <Trash2 size={24} className="text-teal" />
            <h3>Maintenance & Clean</h3>
          </div>
          <div className="maintenance-actions-block">
            <p>
              Free up space on your disk instantly by pruning historical vision events, snapshots, and old log entries.
            </p>
            
            <button 
              className="clean-storage-action-btn"
              onClick={handleCleanStorage}
              disabled={cleaning}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              {cleaning && <RefreshCw size={14} className="spinner-icon" />}
              <span>{cleaning ? 'Running Cleanup...' : 'Prune Storage Now'}</span>
            </button>

            {cleanMessage && (
              <div className="clean-alert-box" style={{ marginTop: '8px' }}>
                {cleanMessage}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Storage Configuration form */}
      <div className="admin-form-card" style={{ marginTop: '0px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Settings className="text-blue" size={20} />
          <h3>Retention & Erase Policies</h3>
        </div>

        {configSuccess && <div className="alert alert-success">{configSuccess}</div>}
        {configError && <div className="alert alert-error">{configError}</div>}

        <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="form-grid">
            <div className="form-group">
              <label>Maximum Allowed Size (GB)</label>
              <input 
                type="number" 
                min="5" 
                max="1000" 
                value={maxSizeGb} 
                onChange={e => setMaxSizeGb(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Snapshot Retention (Days)</label>
              <input 
                type="number" 
                min="1" 
                max="365" 
                value={snapshotsDays} 
                onChange={e => setSnapshotsDays(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Video Clip Retention (Days)</label>
              <input 
                type="number" 
                min="1" 
                max="365" 
                value={clipsDays} 
                onChange={e => setClipsDays(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>System Logs Retention (Days)</label>
              <input 
                type="number" 
                min="1" 
                max="365" 
                value={logsDays} 
                onChange={e => setLogsDays(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="checkbox-group">
              <input 
                type="checkbox" 
                id="auto-erase-checkbox" 
                checked={autoErase}
                onChange={e => setAutoErase(e.target.checked)}
              />
              <label htmlFor="auto-erase-checkbox">
                Auto-erase oldest data (FIFO) when allocation limit is exceeded
              </label>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                type="button"
                className="secondary-btn"
                onClick={handleResetDefaults}
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <RefreshCw size={14} />
                <span>Reset to Defaults</span>
              </button>
              <button 
                type="submit" 
                className="primary-btn"
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Save size={14} />
                <span>Save Configuration</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Vision Gallery */}
      <section className="vision-gallery-section">
        <div className="section-header-row">
          <h2>Vision Captures Gallery</h2>
          <span className="section-meta">{galleryEvents.length} snapshots</span>
        </div>

        {galleryEvents.length === 0 ? (
          <div className="empty-state-card">
            <Image size={40} className="empty-state-icon" />
            <h3>No Captures Found</h3>
            <p>Alert snapshots will appear here when visual triggers are activated and record events.</p>
          </div>
        ) : (
          <div className="gallery-grid">
            {galleryEvents.map(ev => (
              <div 
                key={ev.id} 
                className="gallery-item-card"
                onClick={() => setActiveLightbox(ev)}
              >
                <div className="image-hover-trigger">
                  <img 
                    src={`http://localhost:8000/api/storage/files/${ev.snapshot_path}`} 
                    alt={ev.description} 
                    className="gallery-thumbnail"
                    loading="lazy"
                  />
                  <div className="hover-lens-overlay">
                    <ZoomIn size={20} />
                  </div>
                </div>
                <div className="gallery-card-meta">
                  <div className="gallery-main-meta">
                    <span className="gallery-cam-name">{ev.camera_name}</span>
                    <span className={`severity-indicator ${ev.severity}`} />
                  </div>
                  <span className="gallery-event-desc">{ev.description || ev.event_type}</span>
                  <span className="gallery-event-date">
                    {new Date(ev.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Lightbox Modal */}
      {activeLightbox && (
        <div className="modal-backdrop" onClick={() => setActiveLightbox(null)}>
          <div className="modal-content large-view" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>{activeLightbox.camera_name} — Vision Captures</h3>
                <p className="lightbox-subtitle">{activeLightbox.description || activeLightbox.event_type}</p>
              </div>
              <button className="modal-close-btn" onClick={() => setActiveLightbox(null)}>&times;</button>
            </div>
            <div className="modal-body lightbox-body">
              <div className="lightbox-image-wrapper">
                <img 
                  src={`http://localhost:8000/api/storage/files/${activeLightbox.snapshot_path}`} 
                  alt={activeLightbox.description}
                  className="lightbox-img"
                />
              </div>
              <div className="lightbox-footer-metadata" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div className="meta-badge"><Calendar size={12} /> {new Date(activeLightbox.created_at).toLocaleString()}</div>
                  <div className="meta-badge"><Layers size={12} /> Confidence: {(activeLightbox.confidence * 100).toFixed(0)}%</div>
                  <div className={`meta-badge severity ${activeLightbox.severity}`}>Severity: {activeLightbox.severity.toUpperCase()}</div>
                </div>
                <button 
                  className="secondary-btn" 
                  onClick={() => handleDeleteEvent(activeLightbox.id)}
                  style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Trash2 size={13} />
                  <span>Delete Capture</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
