import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Settings, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  HelpCircle,
  Eye,
  EyeOff
} from 'lucide-react';

export default function Models() {
  const [modelConfig, setModelConfig] = useState(null);
  const [testingProvider, setTestingProvider] = useState('');
  const [testResults, setTestResults] = useState({});

  // Input states
  const [ollamaHost, setOllamaHost] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llava');
  const [lmStudioHost, setLmStudioHost] = useState('http://localhost:1234');
  const [lmStudioEnabled, setLmStudioEnabled] = useState(false);
  const [geminiKey, setGeminiKey] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);

  useEffect(() => {
    fetchModelsConfig();
  }, []);

  const fetchModelsConfig = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/models');
      if (res.ok) {
        const data = await res.json();
        setModelConfig(data);
        
        // Populate inputs
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

  const handleConnect = async (provider) => {
    setTestingProvider(provider);
    setTestResults(prev => ({ ...prev, [provider]: 'testing' }));
    
    let payload = { provider };
    if (provider === 'ollama') {
      payload.host = ollamaHost;
      payload.default_model = ollamaModel;
    } else if (provider === 'lmstudio') {
      payload.host = lmStudioHost;
      payload.enabled = lmStudioEnabled;
    } else if (provider === 'gemini') {
      payload.api_key = geminiKey;
      payload.enabled = true;
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

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">AI Models</h1>
          <p className="page-subtitle">Configure Vision-Language Models (VLM) for smart image analysis and object detection</p>
        </div>
      </header>

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
              {testResults.ollama === 'connected' || (modelConfig?.ollama?.enabled && testResults.ollama !== 'failed') ? (
                <span className="badge-connected"><CheckCircle size={14} /> Connected</span>
              ) : testResults.ollama === 'failed' ? (
                <span className="badge-offline"><XCircle size={14} /> Offline</span>
              ) : (
                <span className="badge-unknown"><HelpCircle size={14} /> Ready</span>
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
              onClick={() => handleConnect('ollama')}
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
              {modelConfig?.lmstudio?.enabled && testResults.lmstudio !== 'failed' ? (
                <span className="badge-connected"><CheckCircle size={14} /> Connected</span>
              ) : testResults.lmstudio === 'failed' ? (
                <span className="badge-offline"><XCircle size={14} /> Offline</span>
              ) : (
                <span className="badge-unknown"><HelpCircle size={14} /> Ready</span>
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
              onClick={() => handleConnect('lmstudio')}
              disabled={testingProvider === 'lmstudio'}
            >
              {testingProvider === 'lmstudio' ? <RefreshCw className="spinner-icon" size={14} /> : null}
              <span>{testingProvider === 'lmstudio' ? 'Connecting...' : 'Connect & Verify'}</span>
            </button>
          </div>
        </div>

        {/* Google Gemini Card */}
        <div className="model-provider-card">
          <div className="provider-header">
            <div className="provider-info-block">
              <Cpu className="provider-icon green" size={24} />
              <div>
                <h3>Google Gemini (Cloud Vision)</h3>
                <span className="status-label">High-performance cloud intelligence</span>
              </div>
            </div>
            <div className="connection-status-badge">
              {modelConfig?.gemini?.enabled ? (
                <span className="badge-connected"><CheckCircle size={14} /> Active</span>
              ) : (
                <span className="badge-offline"><XCircle size={14} /> Inactive</span>
              )}
            </div>
          </div>

          <div className="provider-body">
            <p className="provider-desc">
              Uses Google Gemini 1.5 Pro/Flash models for advanced and highly detailed image reasoning. Requires an active internet connection.
            </p>

            <div className="form-group">
              <label>Gemini API Key</label>
              <div className="password-input-wrapper">
                <input 
                  type={showGeminiKey ? "text" : "password"} 
                  value={geminiKey}
                  onChange={e => setGeminiKey(e.target.value)}
                  placeholder={modelConfig?.gemini?.has_key ? "••••••••••••••••••••••••••••••••" : "AIzaSy..."}
                />
                <button 
                  type="button" 
                  className="password-toggle-btn"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                >
                  {showGeminiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button 
              className="connect-action-btn"
              onClick={() => handleConnect('gemini')}
              disabled={testingProvider === 'gemini'}
            >
              {testingProvider === 'gemini' ? <RefreshCw className="spinner-icon" size={14} /> : null}
              <span>{testingProvider === 'gemini' ? 'Connecting...' : 'Save & Activate Key'}</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
