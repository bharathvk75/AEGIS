import React, { useState, useEffect } from 'react';
import { 
  HardDrive, 
  Trash2, 
  Settings, 
  Image, 
  Calendar,
  Layers,
  ZoomIn
} from 'lucide-react';

export default function Storage({ stats, fetchStats }) {
  const [cleaning, setCleaning] = useState(false);
  const [cleanMessage, setCleanMessage] = useState('');
  const [galleryEvents, setGalleryEvents] = useState([]);
  const [activeLightbox, setActiveLightbox] = useState(null);

  useEffect(() => {
    fetchGalleryEvents();
  }, []);

  const fetchGalleryEvents = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/events?limit=50');
      if (res.ok) {
        const data = await res.json();
        // Filter out events that don't have a snapshot path
        const withSnapshots = data.filter(e => e.snapshot_path);
        setGalleryEvents(withSnapshots);
      }
    } catch (err) {
      console.error("Error loading gallery:", err);
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
        fetchStats(); // update storage metrics
        fetchGalleryEvents(); // refresh gallery
      } else {
        setCleanMessage('Failed to run storage cleanup.');
      }
    } catch (err) {
      setCleanMessage('Network error running cleanup.');
    } finally {
      setCleaning(false);
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

      {/* Storage Gauges */}
      <div className="storage-dash-grid">
        
        {/* Resource card */}
        <div className="storage-metric-card">
          <div className="card-top-icon">
            <HardDrive size={24} className="text-blue" />
            <h3>Disk Allocation</h3>
          </div>
          <div className="disk-gauge-section">
            <div className="disk-fraction">
              <span className="used-number">{(stats?.storage?.used_gb ?? 0).toFixed(2)}</span>
              <span className="slash">/</span>
              <span className="total-number">{(stats?.storage?.total_gb ?? 50).toFixed(0)} GB</span>
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
        </div>

        {/* Maintenance card */}
        <div className="storage-maintenance-card">
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
            >
              {cleaning ? 'Running Cleanup...' : 'Prune Storage Now'}
            </button>

            {cleanMessage && (
              <div className="clean-alert-box">
                {cleanMessage}
              </div>
            )}
          </div>
        </div>

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
              <div className="lightbox-footer-metadata">
                <div className="meta-badge"><Calendar size={12} /> {new Date(activeLightbox.created_at).toLocaleString()}</div>
                <div className="meta-badge"><Layers size={12} /> Confidence: {(activeLightbox.confidence * 100).toFixed(0)}%</div>
                <div className={`meta-badge severity ${activeLightbox.severity}`}>Severity: {activeLightbox.severity.toUpperCase()}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
