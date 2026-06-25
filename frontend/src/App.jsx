import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Strands from './components/Strands';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Models from './pages/Models';
import Hermes from './pages/Hermes';
import Storage from './pages/Storage';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [stats, setStats] = useState(null);
  const [socketEvents, setSocketEvents] = useState([]);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Poll system status every 5 seconds
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Setup real-time WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/status');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Error fetching system status:", err);
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket('ws://localhost:8000/ws/events');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected to AEGIS event hub');
    };

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        setSocketEvents(prev => [event, ...prev]);
      } catch (err) {
        console.error("Error parsing WebSocket event:", err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed. Reconnecting in 3s...');
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      ws.close();
    };
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard stats={stats} socketEvents={socketEvents} setSocketEvents={setSocketEvents} />;
      case 'cameras':
        return <Cameras />;
      case 'models':
        return <Models />;
      case 'hermes':
        return <Hermes />;
      case 'storage':
        return <Storage stats={stats} fetchStats={fetchStats} />;
      default:
        return <Dashboard stats={stats} socketEvents={socketEvents} setSocketEvents={setSocketEvents} />;
    }
  };

  return (
    <div className="app-container">
      {/* Premium background WebGL strands (Teal, Indigo, Slate) */}
      <div className="bg-strands-wrapper">
        <Strands
          colors={["#4F46E5", "#0D9488", "#1E293B"]}
          count={3}
          speed={0.3}
          amplitude={1.2}
          waviness={1}
          thickness={0.6}
          glow={2.0}
          taper={2.8}
          spread={1.2}
          intensity={0.4}
          saturation={1.0}
          opacity={0.35}
          scale={1.2}
          glass={false}
        />
      </div>

      {/* Main Flex Layout */}
      <div className="app-layout">
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          isCollapsed={isCollapsed} 
          setIsCollapsed={setIsCollapsed} 
          stats={stats}
        />
        
        {/* Main Content with 3D Depth spatial effect */}
        <main className={`main-content-panel ${isCollapsed ? 'flat' : 'depth-3d'}`}>
          <div className="content-inner-scroller">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}
