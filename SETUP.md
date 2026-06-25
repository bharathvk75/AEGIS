# AEGIS: Real-Time Edge Video Analytics System

## Complete Setup Guide

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running AEGIS](#running-aegis)
5. [Using Ollama](#using-ollama)
6. [Camera Setup](#camera-setup)
7. [Hermes Agent](#hermes-agent)
8. [Storage Management](#storage-management)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10/11, macOS 10.14+, Ubuntu 18.04+ | Windows 11, macOS 13+ |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 20 GB free | 100 GB SSD |
| **GPU** | Optional (for faster AI) | NVIDIA GPU with 6GB+ VRAM |

### Required Software

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Ollama** - [Download](https://ollama.ai/) or install via terminal:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows - download from ollama.ai
   ```

---

## Installation

### Step 1: Clone or Download AEGIS

```bash
# If using git
git clone <repository-url> AEGIS
cd AEGIS

# Or extract the ZIP file to a folder
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install customtkinter>=5.2.0
pip install opencv-python>=4.9.0
pip install sqlalchemy>=2.0
pip install pillow>=10.0.0
pip install pyyaml>=6.0
pip install langchain>=0.1.0
pip install ollama>=0.1.0
pip install httpx>=0.25.0
pip install requests>=2.31.0
pip install psutil>=5.9.0
```

### Step 4: Install Ollama Models

```bash
# Pull basic vision model (recommended for beginners)
ollama pull llava

# Pull other popular models
ollama pull qwen2-vl      # Multimodal
ollama pull deepseek-r1   # Reasoning
ollama pull llama3.2       # Text-only
```

---

## Configuration

### Edit `config/config.yaml`

```yaml
app:
  name: "AEGIS"
  version: "1.0.0"
  theme: "dark"
  min_to_tray: true

storage:
  max_size_gb: 50          # Max storage for clips/snapshots
  auto_erase: true         # Auto-delete old files when full
  strategy: "fifo"         # fifo, lru, or oldest_first
  retention:
    snapshots_days: 7      # Keep snapshots for 7 days
    clips_days: 3           # Keep video clips for 3 days
    logs_days: 30           # Keep logs for 30 days

ollama:
  host: "http://localhost:11434"
  default_model: "llava"

hermes:
  check_interval: 2        # Seconds between checks
```

---

## Running AEGIS

### Start Ollama First

```bash
# In a separate terminal
ollama serve
```

### Run AEGIS

```bash
# Activate virtual environment first
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Run
python main.py
```

Or:

```bash
python main.py
```

---

## Using Ollama

### Check Ollama Status

Ollama status is shown in the bottom status bar:
- 🟢 Green = Connected
- 🔴 Red = Offline

### Pull New Models

1. Go to **Models** page in AEGIS
2. Enter model name (e.g., `llava`, `qwen2-vl`)
3. Click **Pull Model**

Or via terminal:

```bash
ollama pull <model-name>
```

### Available Models

| Model | Size | Best For |
|-------|------|----------|
| `llava` | 4GB | Image understanding, object detection |
| `llava:latest` | 7GB | Better vision accuracy |
| `qwen2-vl` | 7GB | Multimodal tasks |
| `deepseek-r1` | 8GB | Complex reasoning |
| `llama3.2` | 2GB | Text-only, faster |

---

## Camera Setup

### Supported Sources

1. **RTSP Streams** - IP cameras, NVRs
   ```
   rtsp://192.168.1.100:554/stream1
   rtsp://user:pass@192.168.1.100:554/live
   ```

2. **USB Cameras** - Webcams, capture cards
   ```
   /dev/video0        # Linux
   0                   # Windows (device index)
   ```

3. **Video Files** - For testing
   ```
   /path/to/video.mp4
   ```

### Adding a Camera

1. Go to **Cameras** page
2. Click **+ Add Camera**
3. Fill in details:
   - **Name**: Factory Floor, Store Entrance, etc.
   - **Source Type**: RTSP, USB, or File
   - **URL/Device**: Stream URL or device path
   - **FPS**: 10-30 (higher = more resource usage)
4. Click **Save Camera**

---

## Hermes Agent

The Hermes Agent provides smart notifications when events are detected.

### Notification Channels

#### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your bot token (e.g., `123456:ABC-DEF...`)
3. Start a chat with your bot
4. Get your Chat ID via [@userinfobot](https://t.me/userinfobot)
5. In AEGIS, add Telegram channel with:
   - Bot Token
   - Chat ID

#### Discord Webhook

1. In Discord Server Settings → Integrations → Webhooks
2. Create webhook, copy URL
3. In AEGIS, add Discord channel with webhook URL

#### Custom Webhook

Supports any HTTP endpoint:
- URL: `https://api.example.com/alerts`
- Method: POST, GET, PUT
- Custom headers and body

#### SMS / WhatsApp (via Twilio)

1. Create Twilio account
2. Get Account SID, Auth Token
3. Get a phone number
4. Configure in AEGIS

### Creating Triggers

1. Go to **Hermes Agent** page
2. Click **+ Add Trigger**
3. Configure:
   - **Name**: e.g., "Factory Safety Alert"
   - **Condition**: Natural language, e.g., "Alert when person without helmet is detected"
   - **Capture**: Snapshot, video clip, or both
4. Link notification channels

---

## Storage Management

### Overview Tab

- View total storage used
- Set maximum storage limit (5-500 GB)
- Enable/disable auto-erase
- Auto-erase removes oldest files when limit reached

### Breakdown Tab

Shows storage used by:
- 📷 Snapshots - Images captured by triggers
- 🎬 Video Clips - Video recordings from triggers

### Retention Policies

- **Snapshots**: 1-30 days
- **Video Clips**: 1-30 days

Files older than retention period are automatically deleted.

### Volumes

Storage locations:
```
data/volumes/snapshots/     # Captured images
data/volumes/clips/         # Video recordings
```

---

## Troubleshooting

### Ollama Won't Connect

```bash
# Check if Ollama is running
ollama list

# Restart Ollama
ollama serve

# Try different host in config
ollama:
  host: "http://localhost:11434"
```

### Camera Not Connecting

1. Check stream URL is correct
2. Verify network access
3. Try playing stream in VLC first
4. Check firewall settings

### No Events Triggered

1. Ensure camera is connected (green status)
2. Ollama must be running with a model
3. Check trigger is enabled
4. Review trigger condition text

### Storage Full

1. Increase max storage in Settings
2. Enable auto-erase
3. Shorten retention periods
4. Manually clear old files via Storage page

### GUI Looks Wrong

1. Ensure CustomTkinter is installed: `pip install customtkinter`
2. Try restarting AEGIS
3. Check display scaling settings

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1-5` | Switch pages |
| `Esc` | Close modal |

---

## Data Locations

```
AEGIS/
├── data/
│   ├── aegis.db           # SQLite database
│   ├── volumes/           # Snapshots & clips
│   │   ├── snapshots/
│   │   └── clips/
│   └── logs/              # Application logs
├── config/
│   └── config.yaml        # Configuration
└── main.py                # Entry point
```

---

## Docker Support (Optional)

```yaml
# docker-compose.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

Run with:
```bash
docker-compose up -d
```

---

## Support

For issues or questions:
- Check logs: `data/logs/aegis.log`
- Review troubleshooting section above
- Check SPEC.md for full technical specification

---

**AEGIS - Edge Video Analytics**  
*100% Local • 100% Private • 100% Free*