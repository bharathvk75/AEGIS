import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Settings, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  HelpCircle,
  Eye,
  EyeOff,
  Plus,
  Key,
  Globe,
  Layers
} from 'lucide-react';

export default function Models() {
  const [modelConfig, setModelConfig] = useState(null);
  const [testingProvider, setTestingProvider] = useState('');
  const [testResults, setTestResults] = useState({});

  // Local models inputs
  const [ollamaHost, setOllamaHost] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llava');
  const [lmStudioHost, setLmStudioHost] = useState('http://localhost:1234');
  const [lmStudioEnabled, setLmStudioEnabled] = useState(false);

  // General cloud provider form states
  const [selectedPreset, setSelectedPreset] = useState('openai');
  const [customName, setCustomName] = useState('OpenAI');
  const [customEndpoint, setCustomEndpoint] = useState('https://api.openai.com/v1');
  const [customModel, setCustomModel] = useState('gpt-4o');
  const [customApiKey, setCustomApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  // Presets configuration
  const presets = {
    openai: {
      name: 'OpenAI',
      endpoint: 'https://api.openai.com/v1',
      model: 'gpt-4o'
    },
    gemini: {
      name: 'Gemini',
      endpoint: 'https://generativelanguage.googleapis.com',
      model: 'gemini-1.5-flash'
    },
    deepseek: {
      name: 'DeepSeek',
      endpoint: 'https://api.deepseek.com/v1',
      model: 'deepseek-chat'
    },
    openrouter: {
      name: 'OpenRouter',
      endpoint: 'https://openrouter.ai/api/v1',
      model: 'meta-llama/llama-3.1-8b-instruct:free'
    },
    anthropic_proxy: {
      name: 'Anthropic',
      endpoint: 'https://openrouter.ai/api/v1',
      model: 'anthropic/claude-3.5-sonnet'
    },
    custom: {
      name: 'Custom-VLM',
      endpoint: '',
      model: ''
    }
  };

  useEffect(() => {
    fetchModelsConfig();
  }, []);

  // Update form inputs when preset changes
  useEffect(() => {
    const preset = presets[selectedPreset];
    if (preset) {
      setCustomName(preset.name);
      setCustomEndpoint(preset.endpoint);
      setCustomModel(preset.model);
      setCustomApiKey('');
      setFormError('');
      setFormSuccess('');
    }
  }, [selectedPreset]);

  const fetchModelsConfig = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/models');
      if (res.ok) {
        const data = await res.json();
        setModelConfig(data);
        
        // Populate local inputs
        if (data.ollama) {
          setOllamaHost(data.ollama.host || 'http://localhost:11434');
          setOllamaModel(data.ollama.default_model || 'llava');
        }
        if (data.lmstudio) {
          setLmStudioHost(data.lmstudio.host || 'http://localhost:1234');
          setLmStudioEnabled(data.lmstudio.enabled || false);
        }
      }
    } catch (err) {
      console.error("Error loading models config:", err);
    }
  };

  const handleConnectLocal = async (provider) => {
    setTestingProvider(provider);
    setTestResults(prev => ({ ...prev, [provider]: 'testing' }));
    
    let payload = { provider };
    if (provider === 'ollama') {
      payload.host = ollamaHost;
      payload.default_model = ollamaModel;
    } else if (provider === 'lmstudio') {
      payload.host = lmStudioHost;
      payload.enabled = lmStudioEnabled;
    }

    try {
      const res = await fetch('http://localhost:8000/api/models/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const data = await res.json();
        setTestResults(prev => ({ 
          ...prev, 
          [provider]: data.connected ? 'connected' : 'failed' 
        }));
        fetchModelsConfig();
      } else {
        setTestResults(prev => ({ ...prev, [provider]: 'failed' }));
      }
    } catch (err) {
      setTestResults(prev => ({ ...prev, [provider]: 'failed' }));
    } finally {
      setTestingProvider('');
    }
  };

  const handleSaveCloudProvider = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');

    if (!customName.trim()) {
      setFormError("Please enter a provider name.");
      return;
    }
    if (!customEndpoint.trim()) {
      setFormError("Please enter an API endpoint URL.");
      return;
    }
    if (!customModel.trim()) {
      setFormError("Please enter a model name.");
      return;
    }

    setTestingProvider('cloud_form');
    
    try {
      const payload = {
        provider: customName,
        endpoint: customEndpoint,
        default_model: customModel,
        api_key: customApiKey || undefined,
        enabled: true
      };

      const res = await fetch('http://localhost:8000/api/models/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        if (data.connected) {
          setFormSuccess(`${customName} connected and verified successfully!`);
          setCustomApiKey('');
          fetchModelsConfig();
        } else {
          setFormError(`${customName} saved, but the connection check failed (Offline or Invalid API Key).`);
          fetchModelsConfig();
        }
      } else {
        setFormError("Failed to connect to provider.");
      }
    } catch (err) {
      setFormError("Network error connecting to cloud provider.");
    } finally {
      setTestingProvider('');
    }
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">AI Models</h1>
          <p className="page-subtitle">Configure Vision-Language Models (VLM) for smart image analysis and object detection</p>
        </div>
      </header>

      {/* Local Providers Grid */}
      <section className="local-providers-section">
        <h2 className="section-title-tag">Local AI Engines</h2>
        <div className="models-config-grid">
          
          {/* Ollama Card */}
          <div className="model-provider-card">
            <div className="provider-header">
              <div className="provider-info-block">
                <Cpu className="provider-icon blue" size={24} />
                <div>
                  <h3>Ollama (Local VLM)</h3>
                  <span className="status-label">Recommended for local setups</span>
                </div>
              </div>
              <div className="connection-status-badge">
                {modelConfig?.ollama?.connected ? (
                  <span className="badge-connected"><CheckCircle size={14} /> Connected</span>
                ) : (
                  <span className="badge-offline"><XCircle size={14} /> Offline</span>
                )}
              </div>
            </div>

            <div className="provider-body">
              <p className="provider-desc">
                Connect to your local Ollama server. Requires a vision model like <code>llava</code> or <code>bakllava</code> installed.
              </p>

              <div className="form-group">
                <label>Ollama Server URL</label>
                <input 
                  type="text" 
                  value={ollamaHost}
                  onChange={e => setOllamaHost(e.target.value)}
                  placeholder="http://localhost:11434"
                />
              </div>

              <div className="form-group">
                <label>Default Vision Model</label>
                <input 
                  type="text" 
                  value={ollamaModel}
                  onChange={e => setOllamaModel(e.target.value)}
                  placeholder="llava"
                />
              </div>

              <button 
                className="connect-action-btn"
                onClick={() => handleConnectLocal('ollama')}
                disabled={testingProvider === 'ollama'}
              >
                {testingProvider === 'ollama' ? <RefreshCw className="spinner-icon" size={14} /> : null}
                <span>{testingProvider === 'ollama' ? 'Connecting...' : 'Connect & Verify'}</span>
              </button>
            </div>
          </div>

          {/* LM Studio Card */}
          <div className="model-provider-card">
            <div className="provider-header">
              <div className="provider-info-block">
                <Cpu className="provider-icon purple" size={24} />
                <div>
                  <h3>LM Studio (Local Server)</h3>
                  <span className="status-label">Run local LLMs with OpenAI compatibility</span>
                </div>
              </div>
              <div className="connection-status-badge">
                {modelConfig?.lmstudio?.connected ? (
                  <span className="badge-connected"><CheckCircle size={14} /> Connected</span>
                ) : (
                  <span className="badge-offline"><XCircle size={14} /> Offline</span>
                )}
              </div>
            </div>

            <div className="provider-body">
              <p className="provider-desc">
                Connect to LM Studio running in Local Server mode. Ensure a vision-capable model is loaded.
              </p>

              <div className="form-group">
                <label>Server URL</label>
                <input 
                  type="text" 
                  value={lmStudioHost}
                  onChange={e => setLmStudioHost(e.target.value)}
                  placeholder="http://localhost:1234"
                />
              </div>

              <div className="checkbox-group">
                <input 
                  type="checkbox" 
                  id="lmstudio-enable" 
                  checked={lmStudioEnabled}
                  onChange={e => setLmStudioEnabled(e.target.checked)}
                />
                <label htmlFor="lmstudio-enable">Route vision requests to LM Studio</label>
              </div>

              <button 
                className="connect-action-btn"
                onClick={() => handleConnectLocal('lmstudio')}
                disabled={testingProvider === 'lmstudio'}
              >
                {testingProvider === 'lmstudio' ? <RefreshCw className="spinner-icon" size={14} /> : null}
                <span>{testingProvider === 'lmstudio' ? 'Connecting...' : 'Connect & Verify'}</span>
              </button>
            </div>
          </div>

        </div>
      </section>

      {/* Cloud & General API Keys Section */}
      <section className="cloud-providers-section" style={{ marginTop: '16px' }}>
        <h2 className="section-title-tag">Cloud AI API Keys</h2>
        
        <div className="cloud-providers-layout" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
          
          {/* Left Column: Form to configure general API keys */}
          <div className="admin-form-card" style={{ height: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Key className="text-blue" size={20} />
              <h3>Add / Configure API Key</h3>
            </div>
            
            {formError && <div className="alert alert-error" style={{ padding: '8px 12px', fontSize: '12px' }}>{formError}</div>}
            {formSuccess && <div className="alert alert-success" style={{ padding: '8px 12px', fontSize: '12px' }}>{formSuccess}</div>}

            <form onSubmit={handleSaveCloudProvider} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label>VLM Provider Preset</label>
                <select 
                  value={selectedPreset} 
                  onChange={e => setSelectedPreset(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="openai">OpenAI API (gpt-4o)</option>
                  <option value="gemini">Google Gemini API (gemini-1.5-flash)</option>
                  <option value="deepseek">DeepSeek API (deepseek-chat)</option>
                  <option value="openrouter">OpenRouter API (llama-3.1-8b)</option>
                  <option value="anthropic_proxy">Anthropic Claude (via OpenRouter Proxy)</option>
                  <option value="custom">Custom OpenAI-Compatible Endpoint</option>
                </select>
              </div>

              <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
                <div className="form-group">
                  <label>Provider Name</label>
                  <input 
                    type="text" 
                    value={customName}
                    onChange={e => setCustomName(e.target.value)}
                    placeholder="e.g. DeepSeek, OpenRouter"
                    disabled={selectedPreset !== 'custom'}
                  />
                </div>

                <div className="form-group">
                  <label>API Endpoint Base URL</label>
                  <input 
                    type="text" 
                    value={customEndpoint}
                    onChange={e => setCustomEndpoint(e.target.value)}
                    placeholder="https://api.openai.com/v1"
                    disabled={selectedPreset !== 'custom' && selectedPreset !== 'anthropic_proxy'}
                  />
                </div>

                <div className="form-group">
                  <label>Default Vision Model</label>
                  <input 
                    type="text" 
                    value={customModel}
                    onChange={e => setCustomModel(e.target.value)}
                    placeholder="gpt-4o"
                  />
                </div>

                <div className="form-group">
                  <label>API Authentication Key</label>
                  <div className="password-input-wrapper">
                    <input 
                      type={showApiKey ? "text" : "password"} 
                      value={customApiKey}
                      onChange={e => setCustomApiKey(e.target.value)}
                      placeholder="sk-..."
                    />
                    <button 
                      type="button" 
                      className="password-toggle-btn"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>

              <button 
                type="submit" 
                className="primary-btn" 
                style={{ width: '100%', justifyContent: 'center' }}
                disabled={testingProvider === 'cloud_form'}
              >
                {testingProvider === 'cloud_form' ? <RefreshCw className="spinner-icon" size={14} /> : null}
                <span>{testingProvider === 'cloud_form' ? 'Verifying Key...' : 'Save & Verify Key'}</span>
              </button>
            </form>
          </div>

          {/* Right Column: List of configured active providers */}
          <div className="configured-providers-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Configured VLM Endpoints</h3>
            
            <div className="providers-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {modelConfig?.external_providers?.length === 0 ? (
                <div className="empty-state-card" style={{ padding: '30px' }}>
                  <HelpCircle size={24} className="empty-state-icon" />
                  <p style={{ fontSize: '12px', marginTop: '6px' }}>No external API keys configured yet.</p>
                </div>
              ) : (
                modelConfig?.external_providers?.map((prov, index) => (
                  <div 
                    key={index} 
                    className="provider-status-row"
                    style={{
                      background: 'var(--bg-inset)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '10px',
                      padding: '14px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '70%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h4 style={{ fontSize: '14px', fontWeight: '600' }}>{prov.name}</h4>
                        <span 
                          style={{ 
                            fontSize: '9px', 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-muted)'
                          }}
                        >
                          {prov.enabled ? 'ENABLED' : 'DISABLED'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <Globe size={11} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={prov.endpoint}>
                          {prov.endpoint}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <Layers size={11} />
                        <span>Model: <code>{prov.default_model}</code></span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                      {prov.connected ? (
                        <span className="badge-connected" style={{ fontSize: '10px', padding: '4px 8px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(16,185,129,0.08)', color: 'var(--accent-green)', border: '1px solid rgba(16,185,129,0.2)' }}>
                          <CheckCircle size={10} /> Online
                        </span>
                      ) : (
                        <span className="badge-offline" style={{ fontSize: '10px', padding: '4px 8px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(220,38,38,0.08)', color: '#ef4444', border: '1px solid rgba(220,38,38,0.2)' }}>
                          <XCircle size={10} /> Offline
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </section>
    </div>
  );
}
