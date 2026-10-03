import React, { useState, useEffect } from 'react';
import { 
  BellRing, 
  Plus, 
  Trash2, 
  Send, 
  ShieldAlert, 
  ToggleLeft, 
  ToggleRight, 
  RefreshCw,
  Check,
  AlertCircle,
  Edit2,
  Globe,
  Link2,
  ExternalLink,
  Sparkles,
  Zap,
  Play,
  CheckCircle2
} from 'lucide-react';

export default function Hermes() {
  const [activeSubTab, setActiveSubTab] = useState('triggers'); // triggers, presets, channels
  const [cameras, setCameras] = useState([]);
  const [channels, setChannels] = useState([]);
  const [triggers, setTriggers] = useState([]);
  const [presets, setPresets] = useState([]);

  // Testing states
  const [testingChannelId, setTestingChannelId] = useState(null);
  const [testStatuses, setTestStatuses] = useState({});

  // Interactive AI Tester state
  const [aiTestCameraId, setAiTestCameraId] = useState('');
  const [aiTestPrompt, setAiTestPrompt] = useState('Detect if a person is loitering or holding a package.');
  const [aiTesting, setAiTesting] = useState(false);
  const [aiTestResult, setAiTestResult] = useState(null);

  // Tunnel states
  const [tunnelUrl, setTunnelUrl] = useState('');
  const [generatingTunnel, setGeneratingTunnel] = useState(false);

  const handleGenerateTunnel = async () => {
    setGeneratingTunnel(true);
    try {
      const res = await fetch('http://localhost:8000/api/hermes/tunnel');
      if (res.ok) {
        const data = await res.json();
        if (data.url) {
          setTunnelUrl(data.url);
        } else {
          alert("Failed to establish secure tunnel. Please check system SSH or server logs.");
        }
      } else {
        alert("Server error generating tunnel link.");
      }
    } catch (err) {
      alert("Network error establishing tunnel.");
    } finally {
      setGeneratingTunnel(false);
    }
  };

  // Forms states
  const [showChannelForm, setShowChannelForm] = useState(false);
  const [editingChannelId, setEditingChannelId] = useState(null);
  const [chName, setChName] = useState('');
  const [chType, setChType] = useState('telegram');
  const [telegramToken, setTelegramToken] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const [discordWebhook, setDiscordWebhook] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [twilioSid, setTwilioSid] = useState('');
  const [twilioToken, setTwilioToken] = useState('');
  const [twilioFrom, setTwilioFrom] = useState('');
  const [twilioTo, setTwilioTo] = useState('');

  const [showTriggerForm, setShowTriggerForm] = useState(false);
  const [editingTriggerId, setEditingTriggerId] = useState(null);
  const [trName, setTrName] = useState('');
  const [trCameraId, setTrCameraId] = useState('');
  const [trCondition, setTrCondition] = useState('');
  const [trSelectedChannels, setTrSelectedChannels] = useState([]);
  const [trCaptureSnapshot, setTrCaptureSnapshot] = useState(true);

  // Validation helper: Check if Telegram Chat ID is non-numeric
  const isTelegramChatIdInvalid = () => {
    if (!telegramChatId) return false;
    return /[a-zA-Z@_]/.test(telegramChatId);
  };

  useEffect(() => {
    fetchCameras();
    fetchChannels();
    fetchTriggers();
    fetchPresets();
  }, []);

  const fetchCameras = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/cameras');
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
        if (data.length > 0) {
          if (!trCameraId) setTrCameraId(data[0].id);
          if (!aiTestCameraId) setAiTestCameraId(data[0].id);
        }
      }
    } catch (err) {}
  };

  const fetchChannels = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/hermes/channels');
      if (res.ok) {
        const data = await res.json();
        setChannels(data);
      }
    } catch (err) {}
  };

  const fetchTriggers = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/hermes/triggers');
      if (res.ok) {
        const data = await res.json();
        setTriggers(data);
      }
    } catch (err) {}
  };

  const fetchPresets = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/triggers/presets');
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch (err) {}
  };

  const handleApplyPreset = async (preset) => {
    try {
      const camera_id = cameras.length > 0 ? cameras[0].id : null;
      const notification_ids = channels.length > 0 ? [channels[0].id] : [];
      
      const res = await fetch('http://localhost:8000/api/triggers/presets/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preset_id: preset.id,
          camera_id: camera_id,
          notification_ids: notification_ids
        })
      });

      if (res.ok) {
        alert(`Preset "${preset.name}" applied successfully as active trigger!`);
        fetchTriggers();
        setActiveSubTab('triggers');
      }
    } catch (err) {
      alert("Failed to apply preset.");
    }
  };

  const handleRunAiTest = async () => {
    if (!aiTestCameraId || !aiTestPrompt.trim()) return;
    setAiTesting(true);
    setAiTestResult(null);

    try {
      const res = await fetch('http://localhost:8000/api/ai/test-trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          camera_id: parseInt(aiTestCameraId),
          condition_text: aiTestPrompt
        })
      });

      if (res.ok) {
        const data = await res.json();
        setAiTestResult(data);
      } else {
        alert("Error testing AI condition against camera feed.");
      }
    } catch (err) {
      alert("Network error running AI test.");
    } finally {
      setAiTesting(false);
    }
  };

  // Channel CRUD & Test
  const handleTestChannel = async (id) => {
    setTestingChannelId(id);
    setTestStatuses(prev => ({ ...prev, [id]: 'testing' }));
    
    try {
      const res = await fetch(`http://localhost:8000/api/hermes/channels/${id}/test`, {
        method: 'POST'
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setTestStatuses(prev => ({ ...prev, [id]: 'passed' }));
        } else {
          setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
          alert(`Channel Test Failed:\n\n${data.error || 'Unknown error occurred.'}`);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
        alert(`Channel Test Failed:\n\n${errData.detail || 'Server error occurred.'}`);
      }
    } catch (err) {
      setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
    } finally {
      setTestingChannelId(null);
    }
  };

  const handleEditChannelClick = (ch) => {
    setEditingChannelId(ch.id);
    setChName(ch.name);
    setChType(ch.channel_type);
    
    const cfg = ch.config || {};
    if (ch.channel_type === 'telegram') {
      setTelegramToken(cfg.bot_token || '');
      setTelegramChatId(cfg.chat_id || '');
    } else if (ch.channel_type === 'discord') {
      setDiscordWebhook(cfg.webhook_url || '');
    } else if (ch.channel_type === 'webhook') {
      setWebhookUrl(cfg.url || '');
    } else if (ch.channel_type === 'sms' || ch.channel_type === 'whatsapp') {
      setTwilioSid(cfg.account_sid || '');
      setTwilioToken(cfg.auth_token || '');
      setTwilioFrom(cfg.from || '');
      setTwilioTo(cfg.to || '');
    }
    setShowChannelForm(true);
  };

  const handleDeleteChannel = async (id) => {
    if (!window.confirm("Are you sure you want to delete this notification channel?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/hermes/channels/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchChannels();
        if (editingChannelId === id) {
          handleCancelChannelEdit();
        }
      }
    } catch (err) {}
  };

  const handleCancelChannelEdit = () => {
    setEditingChannelId(null);
    setChName('');
    setChType('telegram');
    setTelegramToken('');
    setTelegramChatId('');
    setDiscordWebhook('');
    setWebhookUrl('');
    setTwilioSid('');
    setTwilioToken('');
    setTwilioFrom('');
    setTwilioTo('');
    setShowChannelForm(false);
  };

  const handleAddChannel = async (e) => {
    e.preventDefault();
    if (!chName.trim()) return;

    let config = {};
    if (chType === 'telegram') {
      config = { bot_token: telegramToken, chat_id: telegramChatId };
    } else if (chType === 'discord') {
      config = { webhook_url: discordWebhook };
    } else if (chType === 'webhook') {
      config = { url: webhookUrl, method: 'POST' };
    } else if (chType === 'sms' || chType === 'whatsapp') {
      config = { account_sid: twilioSid, auth_token: twilioToken, from: twilioFrom, to: twilioTo };
    }

    try {
      const url = editingChannelId 
        ? `http://localhost:8000/api/hermes/channels/${editingChannelId}`
        : 'http://localhost:8000/api/hermes/channels';
      const method = editingChannelId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: chName,
          channel_type: chType,
          config: config
        })
      });
      
      if (res.ok) {
        handleCancelChannelEdit();
        fetchChannels();
      }
    } catch (err) {}
  };

  // Trigger CRUD
  const handleToggleTrigger = async (tr) => {
    try {
      const res = await fetch(`http://localhost:8000/api/hermes/triggers/${tr.id}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !tr.enabled })
      });
      if (res.ok) {
        fetchTriggers();
      }
    } catch (err) {}
  };

  const handleDeleteTrigger = async (id) => {
    if (!window.confirm("Are you sure you want to delete this trigger?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/hermes/triggers/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchTriggers();
        if (editingTriggerId === id) {
          handleCancelTriggerEdit();
        }
      }
    } catch (err) {}
  };

  const handleEditTriggerClick = (tr) => {
    setEditingTriggerId(tr.id);
    setTrName(tr.name);
    setTrCameraId(tr.camera_id || '');
    setTrCondition(tr.condition_text);
    setTrSelectedChannels(tr.notification_ids || []);
    setTrCaptureSnapshot(tr.capture_snapshot);
    setShowTriggerForm(true);
  };

  const handleCancelTriggerEdit = () => {
    setEditingTriggerId(null);
    setTrName('');
    setTrCondition('');
    setTrSelectedChannels([]);
    setTrCaptureSnapshot(true);
    setShowTriggerForm(false);
  };

  const handleSelectChannel = (id) => {
    if (trSelectedChannels.includes(id)) {
      setTrSelectedChannels(prev => prev.filter(x => x !== id));
    } else {
      setTrSelectedChannels(prev => [...prev, id]);
    }
  };

  const handleAddTrigger = async (e) => {
    e.preventDefault();
    if (!trName.trim() || !trCondition.trim()) return;

    try {
      const url = editingTriggerId 
        ? `http://localhost:8000/api/hermes/triggers/${editingTriggerId}`
        : 'http://localhost:8000/api/hermes/triggers';
      const method = editingTriggerId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: trName,
          camera_id: trCameraId ? parseInt(trCameraId) : null,
          condition_text: trCondition,
          notification_ids: trSelectedChannels,
          capture_snapshot: trCaptureSnapshot,
          enabled: true
        })
      });

      if (res.ok) {
        handleCancelTriggerEdit();
        fetchTriggers();
      }
    } catch (err) {}
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Hermes Agent</h1>
            <span className="v2-badge">v2.0 AI Engine</span>
          </div>
          <p className="page-subtitle">Configure natural language security triggers, preset rules, and notifications</p>
        </div>
      </header>

      {/* Sub tabs Navigation */}
      <div className="sub-tab-navigation" style={{ marginBottom: '20px' }}>
        <button 
          className={`sub-tab-btn ${activeSubTab === 'triggers' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('triggers')}
        >
          Visual Triggers ({triggers.length})
        </button>
        <button 
          className={`sub-tab-btn ${activeSubTab === 'presets' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('presets')}
        >
          Preset AI Rules
        </button>
        <button 
          className={`sub-tab-btn ${activeSubTab === 'channels' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('channels')}
        >
          Notification Channels ({channels.length})
        </button>
      </div>

      {/* Secure Tunnel Banner */}
      <div className="admin-form-card" style={{ marginBottom: '25px', background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.7) 100%)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, fontSize: '15px', color: 'var(--text-normal)' }}>
              <Globe size={16} className="text-blue" style={{ color: '#3b82f6' }} />
              <span>AEGIS Live Phone Preview & Remote Control</span>
            </h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '650px', lineHeight: '1.4' }}>
              Create a secure tunnel link to stream video feeds live to mobile devices and send Telegram remote commands.
            </p>
          </div>
          <button 
            type="button" 
            className="secondary-btn"
            onClick={handleGenerateTunnel}
            disabled={generatingTunnel}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', borderColor: 'rgba(59, 130, 246, 0.4)', background: 'rgba(59, 130, 246, 0.05)', fontSize: '11px', padding: '6px 12px' }}
          >
            {generatingTunnel ? <RefreshCw size={12} className="spinner-icon" /> : <Link2 size={12} />}
            <span>{generatingTunnel ? 'Establishing Tunnel...' : tunnelUrl ? 'Refresh Link' : 'Generate Secure Link'}</span>
          </button>
        </div>
      </div>

      {/* --- PRESET RULES TAB --- */}
      {activeSubTab === 'presets' && (
        <section className="presets-tab-content">
          <div className="tab-section-header">
            <div>
              <h2>AI Security Presets</h2>
              <p className="page-subtitle" style={{ margin: 0 }}>Instant one-click security rules powered by Vision LLMs</p>
            </div>
          </div>

          <div className="presets-grid">
            {presets.map(preset => (
              <div key={preset.id} className="preset-card">
                <div className="preset-header">
                  <span className="preset-title">{preset.name}</span>
                  <span className="preset-category">{preset.category}</span>
                </div>
                <p className="preset-desc">{preset.description}</p>
                <div className="preset-prompt-preview">
                  "{preset.condition_text}"
                </div>
                <button 
                  className="primary-btn" 
                  onClick={() => handleApplyPreset(preset)}
                  style={{ width: '100%', justifyContent: 'center', marginTop: 'auto' }}
                >
                  <Plus size={14} />
                  <span>Apply Preset</span>
                </button>
              </div>
            ))}
          </div>

          {/* Interactive AI Tester Card */}
          <div className="admin-form-card" style={{ marginTop: '28px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={16} className="text-amber" />
              <span>Interactive AI Test Runner</span>
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Test any custom natural language prompt against your camera feed right now without creating a permanent trigger.
            </p>

            <div className="form-grid">
              <div className="form-group">
                <label>Select Target Camera Feed</label>
                <select value={aiTestCameraId} onChange={e => setAiTestCameraId(e.target.value)}>
                  {cameras.map(c => (
                    <option key={c.id} value={c.id}>{c.name} ({c.source_type})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Natural Language Prompt / Condition</label>
                <input 
                  type="text" 
                  value={aiTestPrompt} 
                  onChange={e => setAiTestPrompt(e.target.value)} 
                  placeholder="e.g. Detect if someone is opening the door or carrying a box"
                />
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
              <button 
                type="button" 
                className="primary-btn" 
                onClick={handleRunAiTest} 
                disabled={aiTesting}
              >
                {aiTesting ? <RefreshCw size={14} className="spinner-icon" /> : <Play size={14} />}
                <span>{aiTesting ? "Analyzing Frame..." : "Run Live AI Evaluation"}</span>
              </button>
            </div>

            {aiTestResult && (
              <div style={{ marginTop: '20px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span className={`meta-badge severity ${aiTestResult.severity}`}>
                    {aiTestResult.triggered ? 'TRIGGERED (ALERT)' : 'NORMAL (NO MATCH)'}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Confidence: {(aiTestResult.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                  <strong>AI Analysis:</strong> {aiTestResult.description}
                </p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* --- VISUAL TRIGGERS TAB --- */}
      {activeSubTab === 'triggers' && (
        <section className="triggers-tab-content">
          <div className="tab-section-header">
            <h2>Active Triggers</h2>
            <button 
              className="primary-btn" 
              onClick={() => {
                if (showTriggerForm) handleCancelTriggerEdit();
                else setShowTriggerForm(true);
              }}
            >
              <Plus size={14} />
              <span>{showTriggerForm ? "Hide Form" : "Create Trigger"}</span>
            </button>
          </div>

          {showTriggerForm && (
            <form className="admin-form-card" onSubmit={handleAddTrigger}>
              <h3>{editingTriggerId ? `Edit Trigger: ${trName}` : 'Create Visual Trigger'}</h3>
              
              <div className="form-grid">
                <div className="form-group">
                  <label>Trigger Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Person Detector, Vehicle Alert"
                    value={trName}
                    onChange={e => setTrName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Target Camera Feed</label>
                  <select value={trCameraId} onChange={e => setTrCameraId(e.target.value)}>
                    <option value="">All Cameras</option>
                    {cameras.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Natural Language Condition</label>
                <textarea 
                  rows={3}
                  placeholder="Describe what to monitor (e.g., 'Detect if someone is holding a box or package near the door')"
                  value={trCondition}
                  onChange={e => setTrCondition(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Dispatch Notifications To:</label>
                <div className="channels-selection-grid">
                  {channels.map(ch => (
                    <label key={ch.id} className="channel-checkbox-label">
                      <input 
                        type="checkbox"
                        checked={trSelectedChannels.includes(ch.id)}
                        onChange={() => handleSelectChannel(ch.id)}
                      />
                      <span>{ch.name} ({ch.channel_type})</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" className="primary-btn">
                  <span>{editingTriggerId ? "Save Changes" : "Create Trigger"}</span>
                </button>
                <button type="button" className="secondary-btn" onClick={handleCancelTriggerEdit}>
                  Cancel
                </button>
              </div>
            </form>
          )}

          <div className="triggers-list">
            {triggers.length === 0 ? (
              <div className="empty-state-card">
                <ShieldAlert size={36} className="empty-state-icon" />
                <h3>No Visual Triggers Configured</h3>
                <p>Use the AI Presets tab or create a natural language rule above to start edge video analytics.</p>
              </div>
            ) : (
              triggers.map(tr => (
                <div key={tr.id} className="trigger-card">
                  <div className="trigger-card-header">
                    <div className="trigger-info">
                      <span className="trigger-name">{tr.name}</span>
                      <span className="trigger-camera">
                        Target: {tr.camera_id ? cameras.find(c => c.id === tr.camera_id)?.name || `Camera #${tr.camera_id}` : 'All Feeds'}
                      </span>
                    </div>
                    <div className="trigger-card-actions">
                      <button 
                        className="toggle-switch-btn"
                        onClick={() => handleToggleTrigger(tr)}
                        title={tr.enabled ? "Disable Trigger" : "Enable Trigger"}
                      >
                        {tr.enabled ? <ToggleRight size={24} className="text-green" /> : <ToggleLeft size={24} className="text-muted" />}
                      </button>
                      <button className="icon-btn edit" onClick={() => handleEditTriggerClick(tr)}>
                        <Edit2 size={14} />
                      </button>
                      <button className="icon-btn delete" onClick={() => handleDeleteTrigger(tr.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <p className="trigger-condition">"{tr.condition_text}"</p>
                </div>
              ))
            )}
          </div>
        </section>
      )}

      {/* --- NOTIFICATION CHANNELS TAB --- */}
      {activeSubTab === 'channels' && (
        <section className="channels-tab-content">
          <div className="tab-section-header">
            <h2>Notification Dispatchers</h2>
            <button 
              className="primary-btn" 
              onClick={() => {
                if (showChannelForm) handleCancelChannelEdit();
                else setShowChannelForm(true);
              }}
            >
              <Plus size={14} />
              <span>{showChannelForm ? "Hide Form" : "Add Channel"}</span>
            </button>
          </div>

          {showChannelForm && (
            <form className="admin-form-card" onSubmit={handleAddChannel}>
              <h3>{editingChannelId ? `Edit Channel: ${chName}` : 'Add Notification Channel'}</h3>
              
              <div className="form-grid">
                <div className="form-group">
                  <label>Channel Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Personal Telegram, Security Discord"
                    value={chName}
                    onChange={e => setChName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Channel Provider</label>
                  <select value={chType} onChange={e => setChType(e.target.value)}>
                    <option value="telegram">Telegram Bot</option>
                    <option value="discord">Discord Webhook</option>
                    <option value="webhook">Custom HTTP Webhook</option>
                    <option value="sms">Twilio SMS</option>
                    <option value="whatsapp">Twilio WhatsApp</option>
                  </select>
                </div>
              </div>

              {chType === 'telegram' && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>Bot Token</label>
                    <input 
                      type="password" 
                      placeholder="123456789:ABCdef..." 
                      value={telegramToken}
                      onChange={e => setTelegramToken(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Chat ID or Telegram Username</label>
                    <input 
                      type="text" 
                      placeholder="e.g. @your_username or 12345678" 
                      value={telegramChatId}
                      onChange={e => setTelegramChatId(e.target.value)}
                    />
                  </div>
                </div>
              )}

              {chType === 'discord' && (
                <div className="form-group">
                  <label>Discord Webhook URL</label>
                  <input 
                    type="text" 
                    placeholder="https://discord.com/api/webhooks/..." 
                    value={discordWebhook}
                    onChange={e => setDiscordWebhook(e.target.value)}
                  />
                </div>
              )}

              {chType === 'webhook' && (
                <div className="form-group">
                  <label>Target HTTP Webhook Endpoint</label>
                  <input 
                    type="text" 
                    placeholder="https://api.yourdomain.com/alerts" 
                    value={webhookUrl}
                    onChange={e => setWebhookUrl(e.target.value)}
                  />
                </div>
              )}

              <div className="form-actions">
                <button type="submit" className="primary-btn">
                  <span>{editingChannelId ? "Save Changes" : "Save Channel"}</span>
                </button>
                <button type="button" className="secondary-btn" onClick={handleCancelChannelEdit}>
                  Cancel
                </button>
              </div>
            </form>
          )}

          <div className="channels-grid">
            {channels.map(ch => (
              <div key={ch.id} className="channel-card">
                <div className="channel-card-header">
                  <div className="channel-identity">
                    <BellRing size={18} className="text-teal" />
                    <span className="channel-name">{ch.name}</span>
                  </div>
                  <div className="channel-actions">
                    <button 
                      className="secondary-btn small"
                      onClick={() => handleTestChannel(ch.id)}
                      disabled={testingChannelId === ch.id}
                    >
                      {testingChannelId === ch.id ? (
                        <RefreshCw size={12} className="spinner-icon" />
                      ) : (
                        <Send size={12} />
                      )}
                      <span>Test Alert</span>
                    </button>
                    <button className="icon-btn edit" onClick={() => handleEditChannelClick(ch)}>
                      <Edit2 size={14} />
                    </button>
                    <button className="icon-btn delete" onClick={() => handleDeleteChannel(ch.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                <div className="channel-details">
                  <span className="type-badge">{ch.channel_type.toUpperCase()}</span>
                  <div className="channel-stats">
                    <span>Sent: {ch.stats?.sent ?? 0}</span>
                    <span>&bull;</span>
                    <span>Failed: {ch.stats?.failed ?? 0}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
