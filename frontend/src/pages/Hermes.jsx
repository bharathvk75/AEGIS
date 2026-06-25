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
  ExternalLink
} from 'lucide-react';

export default function Hermes() {
  const [activeSubTab, setActiveSubTab] = useState('triggers');
  const [cameras, setCameras] = useState([]);
  const [channels, setChannels] = useState([]);
  const [triggers, setTriggers] = useState([]);

  // Testing states
  const [testingChannelId, setTestingChannelId] = useState(null);
  const [testStatuses, setTestStatuses] = useState({});

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
    // If it contains any letters or the @ symbol, it is invalid
    return /[a-zA-Z@_]/.test(telegramChatId);
  };

  useEffect(() => {
    fetchCameras();
    fetchChannels();
    fetchTriggers();
  }, []);

  const fetchCameras = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/cameras');
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
        if (data.length > 0 && !trCameraId) setTrCameraId(data[0].id);
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
          setTestStatuses(prev => ({ 
            ...prev, 
            [id]: 'passed' 
          }));
        } else {
          setTestStatuses(prev => ({ 
            ...prev, 
            [id]: 'failed' 
          }));
          alert(`Channel Test Failed:\n\n${data.error || 'Unknown error occurred.'}`);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
        alert(`Channel Test Failed:\n\n${errData.detail || 'Server error occurred.'}`);
      }
    } catch (err) {
      setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
      alert(`Channel Test Failed:\n\nNetwork error. Ensure that your backend server is running.`);
    } finally {
      setTestingChannelId(null);
      setTimeout(() => {
        setTestStatuses(prev => {
          const updated = { ...prev };
          delete updated[id];
          return updated;
        });
      }, 7000);
    }
  };

  const handleDeleteChannel = async (id) => {
    if (!window.confirm("Are you sure you want to delete this channel?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/hermes/channels/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchChannels();
        fetchTriggers();
        if (editingChannelId === id) {
          handleCancelChannelEdit();
        }
      }
    } catch (err) {}
  };

  const handleEditChannelClick = (ch) => {
    setEditingChannelId(ch.id);
    setChName(ch.name);
    setChType(ch.channel_type);
    setShowChannelForm(true);

    const config = ch.config || {};
    if (ch.channel_type === 'telegram') {
      setTelegramToken(config.bot_token || '');
      setTelegramChatId(config.chat_id || '');
    } else if (ch.channel_type === 'discord') {
      setDiscordWebhook(config.webhook_url || '');
    } else if (ch.channel_type === 'webhook') {
      setWebhookUrl(config.url || '');
    } else if (ch.channel_type === 'sms' || ch.channel_type === 'whatsapp') {
      setTwilioSid(config.account_sid || '');
      setTwilioToken(config.auth_token || '');
      setTwilioFrom(config.from || '');
      setTwilioTo(config.to || '');
    }
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
          <h1 className="page-title">Hermes Agent</h1>
          <p className="page-subtitle">Configure intelligent automation, visual alert triggers, and communication channels</p>
        </div>
      </header>

      {/* Sub tabs Navigation */}
      <div className="sub-tab-navigation" style={{ marginBottom: '20px' }}>
        <button 
          className={`sub-tab-btn ${activeSubTab === 'triggers' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('triggers')}
        >
          Visual Triggers
        </button>
        <button 
          className={`sub-tab-btn ${activeSubTab === 'channels' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('channels')}
        >
          Notification Channels
        </button>
      </div>

      {/* Secure Tunnel Banner */}
      <div className="admin-form-card" style={{ marginBottom: '25px', background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.7) 100%)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, fontSize: '15px', color: 'var(--text-normal)' }}>
              <Globe size={16} className="text-blue" style={{ color: '#3b82f6' }} />
              <span>AEGIS Live Phone Preview & Control Center</span>
            </h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '650px', lineHeight: '1.4' }}>
              Create a temporary secure public link to view live surveillance feeds on your phone and control the AEGIS system remotely via Telegram.
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

        {tunnelUrl && (
          <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
            <p style={{ fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-normal)' }}>🌐 Public Live Feeds (Accessible Anywhere):</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' }}>
              {cameras.map(c => (
                <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-inset)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '11.5px', fontWeight: '500', color: 'var(--text-normal)' }}>{c.name}</span>
                  <a 
                    href={`${tunnelUrl}/api/cameras/${c.id}/stream`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ color: '#3b82f6', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '3px', textDecoration: 'none' }}
                  >
                    <span>Watch Feed</span>
                    <ExternalLink size={10} />
                  </a>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', fontSize: '10.5px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.02)', padding: '8px 10px', borderRadius: '4px' }}>
              <span>ℹ️</span>
              <span>
                Your public URL is: <code>{tunnelUrl}</code>. Use Telegram command <code>/live</code> to send these feeds directly to your phone.
              </span>
            </div>
          </div>
        )}
      </div>

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
                  <label>Surveillance Camera</label>
                  <select value={trCameraId} onChange={e => setTrCameraId(e.target.value)}>
                    <option value="">All Cameras</option>
                    {cameras.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group span-all">
                  <label>Smart Condition (Natural Language Visual Query)</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Detect if a person is in the frame wearing a red jacket, Detect if a vehicle drives through"
                    value={trCondition}
                    onChange={e => setTrCondition(e.target.value)}
                  />
                  <small className="form-help-text">
                    vlms evaluate conditions containing keywords like "detect", "identify", "analyze" for detailed vision analysis.
                  </small>
                </div>

                <div className="form-group span-all">
                  <label>Route Alerts to Channels</label>
                  {channels.length === 0 ? (
                    <p className="no-channels-warning">Create a notification channel first to link alerts.</p>
                  ) : (
                    <div className="channels-selection-checklist">
                      {channels.map(ch => (
                        <div 
                          key={ch.id} 
                          className={`channel-check-item ${trSelectedChannels.includes(ch.id) ? 'checked' : ''}`}
                          onClick={() => handleSelectChannel(ch.id)}
                        >
                          <div className="checkbox-box">
                            {trSelectedChannels.includes(ch.id) && <Check size={12} />}
                          </div>
                          <span>{ch.name} ({ch.channel_type})</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <div className="checkbox-group">
                    <input 
                      type="checkbox" 
                      id="cap-snapshot" 
                      checked={trCaptureSnapshot}
                      onChange={e => setTrCaptureSnapshot(e.target.checked)}
                    />
                    <label htmlFor="cap-snapshot">Capture Snapshot on Alert (Vision Proof)</label>
                  </div>
                </div>
              </div>

              <div className="form-actions-row">
                <button type="button" className="text-btn" onClick={handleCancelTriggerEdit}>Cancel</button>
                <button type="submit" className="primary-btn" disabled={channels.length === 0}>
                  {editingTriggerId ? 'Save Changes' : 'Save Trigger'}
                </button>
              </div>
            </form>
          )}

          <div className="triggers-list-grid">
            {triggers.length === 0 ? (
              <div className="empty-state-card span-all">
                <ShieldAlert size={40} className="empty-state-icon" />
                <h3>No Triggers Configured</h3>
                <p>Create a visual trigger to start analyzing camera streams for specific activities.</p>
              </div>
            ) : (
              triggers.map(tr => (
                <div key={tr.id} className={`trigger-admin-card ${tr.enabled ? '' : 'inactive'}`}>
                  <div className="trigger-card-top">
                    <div className="trigger-title-block">
                      <h4>{tr.name}</h4>
                      <span className="trigger-camera-assoc">
                        Camera: {cameras.find(c => c.id === tr.camera_id)?.name || 'All Cameras'}
                      </span>
                    </div>
                    <div className="trigger-card-controls">
                      <button 
                        className="delete-icon-btn"
                        onClick={() => handleEditTriggerClick(tr)}
                        title="Edit Trigger"
                        style={{ marginRight: '6px' }}
                      >
                        <Edit2 size={13} />
                      </button>
                      <button 
                        className="toggle-active-btn"
                        onClick={() => handleToggleTrigger(tr)}
                        title={tr.enabled ? "Disable Trigger" : "Enable Trigger"}
                      >
                        {tr.enabled ? <ToggleRight size={24} className="toggle-icon green" /> : <ToggleLeft size={24} className="toggle-icon" />}
                      </button>
                      <button 
                        className="delete-icon-btn"
                        onClick={() => handleDeleteTrigger(tr.id)}
                        title="Delete Trigger"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="trigger-card-body">
                    <p className="trigger-condition-expr">"{tr.condition_text}"</p>
                    
                    <div className="trigger-destinations">
                      <span className="dest-title">Alert Targets:</span>
                      {tr.notification_ids.length === 0 ? (
                        <span className="dest-none">None linked</span>
                      ) : (
                        <div className="dest-badges">
                          {tr.notification_ids.map(nid => {
                            const name = channels.find(c => c.id === nid)?.name || `Channel #${nid}`;
                            return <span key={nid} className="dest-badge">{name}</span>;
                          })}
                        </div>
                      )}
                    </div>
                  </div>
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
            <h2>Alert Channels</h2>
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
                    placeholder="e.g. My Telegram Bot, Security Discord"
                    value={chName}
                    onChange={e => setChName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Channel Type</label>
                  <select value={chType} onChange={e => setChType(e.target.value)}>
                    <option value="telegram">Telegram Bot</option>
                    <option value="discord">Discord Webhook</option>
                    <option value="whatsapp">WhatsApp (Twilio)</option>
                    <option value="sms">SMS Text (Twilio)</option>
                    <option value="webhook">Custom API Webhook</option>
                  </select>
                </div>

                {/* Telegram Fields with numeric validation warning */}
                {chType === 'telegram' && (
                  <>
                    <div className="form-group">
                      <label>Bot Token</label>
                      <input 
                        type="password" 
                        placeholder="e.g. 123456:ABC-DEF"
                        value={telegramToken}
                        onChange={e => setTelegramToken(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Chat ID (Numeric Only)</label>
                      <input 
                        type="text" 
                        placeholder="e.g. 987654321"
                        value={telegramChatId}
                        onChange={e => setTelegramChatId(e.target.value)}
                      />
                      {isTelegramChatIdInvalid() && (
                        <div className="alert alert-info" style={{ marginTop: '6px', padding: '8px 12px', fontSize: '11px', lineHeight: '1.4', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', color: 'var(--text-normal)' }}>
                          <AlertCircle size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom', color: '#3b82f6' }} />
                          <strong>Telegram Username Detected!</strong> We will automatically resolve this to your numeric Chat ID when you click Save or Test.
                          <br />
                          <em>Note: You MUST send a message (e.g. <code>/start</code>) to your bot in Telegram first so the bot can discover you.</em>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* Discord Fields */}
                {chType === 'discord' && (
                  <div className="form-group span-all">
                    <label>Discord Webhook URL</label>
                    <input 
                      type="password" 
                      placeholder="https://discord.com/api/webhooks/..."
                      value={discordWebhook}
                      onChange={e => setDiscordWebhook(e.target.value)}
                    />
                  </div>
                )}

                {/* Custom Webhook */}
                {chType === 'webhook' && (
                  <div className="form-group span-all">
                    <label>Custom Endpoint URL (POST)</label>
                    <input 
                      type="text" 
                      placeholder="https://myapi.com/aegis-alerts"
                      value={webhookUrl}
                      onChange={e => setWebhookUrl(e.target.value)}
                    />
                  </div>
                )}

                {/* Twilio SMS / WhatsApp Fields */}
                {(chType === 'sms' || chType === 'whatsapp') && (
                  <>
                    <div className="form-group">
                      <label>Twilio Account SID</label>
                      <input 
                        type="text" 
                        placeholder="AC..."
                        value={twilioSid}
                        onChange={e => setTwilioSid(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Twilio Auth Token</label>
                      <input 
                        type="password" 
                        value={twilioToken}
                        onChange={e => setTwilioToken(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Twilio Number (From)</label>
                      <input 
                        type="text" 
                        placeholder="+1234567890"
                        value={twilioFrom}
                        onChange={e => setTwilioFrom(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Your Phone Number (To)</label>
                      <input 
                        type="text" 
                        placeholder="+1987654321"
                        value={twilioTo}
                        onChange={e => setTwilioTo(e.target.value)}
                      />
                    </div>
                  </>
                )}

              </div>

              <div className="form-actions-row">
                <button type="button" className="text-btn" onClick={handleCancelChannelEdit}>Cancel</button>
                <button type="submit" className="primary-btn">
                  {editingChannelId ? 'Save Changes' : 'Save Channel'}
                </button>
              </div>
            </form>
          )}

          <div className="channels-list-grid">
            {channels.length === 0 ? (
              <div className="empty-state-card span-all">
                <BellRing size={40} className="empty-state-icon" />
                <h3>No Channels Configured</h3>
                <p>Add a notification channel to receive smart edge alerts directly on your device.</p>
              </div>
            ) : (
              channels.map(ch => (
                <div key={ch.id} className="channel-admin-card">
                  <div className="channel-card-top">
                    <div className="channel-title-block">
                      <h4>{ch.name}</h4>
                      <span className="channel-type-badge">{ch.channel_type.toUpperCase()}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button 
                        className="delete-icon-btn"
                        onClick={() => handleEditChannelClick(ch)}
                        title="Edit Channel"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button 
                        className="delete-icon-btn"
                        onClick={() => handleDeleteChannel(ch.id)}
                        title="Delete Channel"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="channel-card-stats-row">
                    <div className="stat-pill">Sent: {ch.stats?.sent ?? 0}</div>
                    <div className="stat-pill">Failed: {ch.stats?.failed ?? 0}</div>
                  </div>

                  <div className="channel-card-footer">
                    <button 
                      className={`test-channel-btn ${testStatuses[ch.id] || ''}`}
                      onClick={() => handleTestChannel(ch.id)}
                      disabled={testingChannelId !== null}
                    >
                      {testStatuses[ch.id] === 'testing' ? (
                        <RefreshCw size={12} className="spinner-icon" />
                      ) : testStatuses[ch.id] === 'passed' ? (
                        <Check size={12} />
                      ) : testStatuses[ch.id] === 'failed' ? (
                        <AlertCircle size={12} />
                      ) : (
                        <Send size={12} />
                      )}
                      <span>
                        {testStatuses[ch.id] === 'testing' 
                          ? 'Sending...' 
                          : testStatuses[ch.id] === 'passed' 
                          ? 'Test Passed!' 
                          : testStatuses[ch.id] === 'failed' 
                          ? 'Test Failed' 
                          : 'Test Channel'}
                      </span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      )}
    </div>
  );
}
