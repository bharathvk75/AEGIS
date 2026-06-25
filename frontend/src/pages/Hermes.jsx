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
  AlertCircle
} from 'lucide-react';

export default function Hermes() {
  const [activeSubTab, setActiveSubTab] = useState('triggers');
  const [cameras, setCameras] = useState([]);
  const [channels, setChannels] = useState([]);
  const [triggers, setTriggers] = useState([]);

  // Testing states
  const [testingChannelId, setTestingChannelId] = useState(null);
  const [testStatuses, setTestStatuses] = useState({});

  // Forms states
  const [showChannelForm, setShowChannelForm] = useState(false);
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
  const [trName, setTrName] = useState('');
  const [trCameraId, setTrCameraId] = useState('');
  const [trCondition, setTrCondition] = useState('');
  const [trSelectedChannels, setTrSelectedChannels] = useState([]);
  const [trCaptureSnapshot, setTrCaptureSnapshot] = useState(true);

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
        setTestStatuses(prev => ({ 
          ...prev, 
          [id]: data.success ? 'passed' : 'failed' 
        }));
      } else {
        setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
      }
    } catch (err) {
      setTestStatuses(prev => ({ ...prev, [id]: 'failed' }));
    } finally {
      setTestingChannelId(null);
      // reset test message after 5 seconds
      setTimeout(() => {
        setTestStatuses(prev => {
          const updated = { ...prev };
          delete updated[id];
          return updated;
        });
      }, 5000);
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
        fetchTriggers(); // reload triggers since channel linkage may change
      }
    } catch (err) {}
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
      const res = await fetch('http://localhost:8000/api/hermes/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: chName,
          channel_type: chType,
          config: config
        })
      });
      
      if (res.ok) {
        setChName('');
        setTelegramToken('');
        setTelegramChatId('');
        setDiscordWebhook('');
        setWebhookUrl('');
        setTwilioSid('');
        setTwilioToken('');
        setTwilioFrom('');
        setTwilioTo('');
        setShowChannelForm(false);
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
      }
    } catch (err) {}
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
      const res = await fetch('http://localhost:8000/api/hermes/triggers', {
        method: 'POST',
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
        setTrName('');
        setTrCondition('');
        setTrSelectedChannels([]);
        setShowTriggerForm(false);
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
      <div className="sub-tab-navigation">
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

      {/* --- VISUAL TRIGGERS TAB --- */}
      {activeSubTab === 'triggers' && (
        <section className="triggers-tab-content">
          <div className="tab-section-header">
            <h2>Active Triggers</h2>
            <button className="primary-btn" onClick={() => setShowTriggerForm(!showTriggerForm)}>
              <Plus size={14} />
              <span>{showTriggerForm ? "Hide Form" : "Create Trigger"}</span>
            </button>
          </div>

          {showTriggerForm && (
            <form className="admin-form-card" onSubmit={handleAddTrigger}>
              <h3>Create Visual Trigger</h3>
              
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
                <button type="button" className="text-btn" onClick={() => setShowTriggerForm(false)}>Cancel</button>
                <button type="submit" className="primary-btn" disabled={channels.length === 0}>Save Trigger</button>
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
            <button className="primary-btn" onClick={() => setShowChannelForm(!showChannelForm)}>
              <Plus size={14} />
              <span>{showChannelForm ? "Hide Form" : "Add Channel"}</span>
            </button>
          </div>

          {showChannelForm && (
            <form className="admin-form-card" onSubmit={handleAddChannel}>
              <h3>Add Notification Channel</h3>
              
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

                {/* Telegram Fields */}
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
                      <label>Chat ID</label>
                      <input 
                        type="text" 
                        placeholder="e.g. 987654321"
                        value={telegramChatId}
                        onChange={e => setTelegramChatId(e.target.value)}
                      />
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
                <button type="button" className="text-btn" onClick={() => setShowChannelForm(false)}>Cancel</button>
                <button type="submit" className="primary-btn">Save Channel</button>
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
                    <button 
                      className="delete-icon-btn"
                      onClick={() => handleDeleteChannel(ch.id)}
                      title="Delete Channel"
                    >
                      <Trash2 size={14} />
                    </button>
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
