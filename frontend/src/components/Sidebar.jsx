import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  Cpu, 
  Zap, 
  HardDrive, 
  ChevronLeft, 
  ChevronRight,
  Shield,
  Activity
} from 'lucide-react';

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  isCollapsed, 
  setIsCollapsed, 
  stats 
}) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'cameras', label: 'Cameras', icon: Video },
    { id: 'models', label: 'AI Models', icon: Cpu },
    { id: 'hermes', label: 'Hermes Agent', icon: Zap },
    { id: 'storage', label: 'Storage', icon: HardDrive },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div className="logo-container">
          <Shield className="logo-icon" size={24} />
          {!isCollapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="logo-text">AEGIS</span>
              <span className="v2-badge">v2.0</span>
            </div>
          )}
        </div>
        <button 
          className="collapse-btn" 
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="sidebar-nav">
        <ul>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveTab(item.id)}
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon className="nav-icon" size={18} />
                  {!isCollapsed && <span className="nav-label">{item.label}</span>}
                  {isActive && !isCollapsed && <div className="active-indicator" />}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Sidebar Footer - System Health */}
      <div className="sidebar-footer">
        {!isCollapsed ? (
          <div className="system-health">
            <div className="health-title">
              <Activity size={14} className="health-icon" />
              <span>System Status</span>
            </div>
            
            <div className="health-metrics">
              <div className="metric-item">
                <div className="metric-label">
                  <span>CPU Usage</span>
                  <span>{stats?.cpu_percent ?? '--'}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${stats?.cpu_percent ?? 0}%` }}
                  />
                </div>
              </div>

              <div className="metric-item">
                <div className="metric-label">
                  <span>Memory</span>
                  <span>{stats?.memory_percent ?? '--'}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${stats?.memory_percent ?? 0}%` }}
                  />
                </div>
              </div>

              <div className="metric-item">
                <div className="metric-label">
                  <span>Storage</span>
                  <span>{stats?.storage?.percentage ?? '--'}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${stats?.storage?.percentage ?? 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="status-dot-only" title="All Systems Operational">
            <div className="pulsing-dot green" />
          </div>
        )}
      </div>
    </aside>
  );
}
