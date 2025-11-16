# 📁 Project File Map

## Complete Directory Structure

```
voice-clone-app/
│
├── 📖 Documentation Files (READ THESE!)
│   ├── START_HERE.md          ⭐ Read this first!
│   ├── QUICKSTART.md          ⭐ Setup in 10 minutes
│   ├── README.md              📚 Complete guide
│   ├── PROJECT_OVERVIEW.md    🔍 Deep dive into features
│   ├── ARCHITECTURE.md        🏗️ Technical architecture
│   └── TESTING_GUIDE.md       🧪 How to test everything
│
├── 🔧 Setup Scripts
│   ├── setup.sh               🐧 Auto-setup for Mac/Linux
│   └── setup.bat              🪟 Auto-setup for Windows
│
├── 🐍 Backend (Python + FastAPI)
│   ├── main.py                ⚙️ Main API server (400+ lines)
│   ├── requirements.txt       📦 Python dependencies
│   ├── .env.example          📝 Template for environment variables
│   └── .env                  🔐 YOUR API KEYS (create this!)
│
└── ⚛️ Frontend (React + Vite)
    ├── src/
    │   ├── App.jsx            💻 Main React component (UI logic)
    │   ├── App.css            🎨 Beautiful styling
    │   └── main.jsx           🚀 React entry point
    ├── index.html             📄 HTML template
    ├── package.json           📦 Node.js dependencies
    └── vite.config.js         ⚡ Vite configuration
```

## File Purposes at a Glance

### 📖 Documentation (6 files)

| File | Purpose | Read When |
|------|---------|-----------|
| **START_HERE.md** | Introduction & navigation guide | First thing! |
| **QUICKSTART.md** | Fastest path to running app | Want to start NOW |
| **README.md** | Complete documentation | Need full details |
| **PROJECT_OVERVIEW.md** | What, why, how of the project | Want to understand deeply |
| **ARCHITECTURE.md** | Technical design & diagrams | Want to understand code |
| **TESTING_GUIDE.md** | How to test properly | Ready to test |

### 🔧 Setup Scripts (2 files)

| File | OS | What It Does |
|------|-----|--------------|
| **setup.sh** | Mac/Linux | Auto-installs everything |
| **setup.bat** | Windows | Auto-installs everything |

### 🐍 Backend Files (4 files)

| File | Lines | Purpose |
|------|-------|---------|
| **main.py** | ~400 | Complete API server with 6 endpoints |
| **requirements.txt** | ~10 | Python packages needed |
| **.env.example** | ~5 | Template showing what keys needed |
| **.env** | ~5 | YOUR actual API keys |

#### Backend Endpoints in main.py:
1. `GET /` - Health check
2. `POST /clone-voice` - Clone user's voice
3. `POST /transcribe` - Speech to text
4. `POST /chat` - Generate AI response
5. `POST /speak` - Text to speech
6. `POST /full-interaction` - Complete flow

### ⚛️ Frontend Files (6 files)

| File | Lines | Purpose |
|------|-------|---------|
| **App.jsx** | ~250 | All UI logic and state |
| **App.css** | ~200 | Beautiful responsive styling |
| **main.jsx** | ~10 | React initialization |
| **index.html** | ~15 | HTML shell |
| **package.json** | ~25 | Dependencies & scripts |
| **vite.config.js** | ~10 | Dev server config |

## What Each Component Does

```
┌─────────────────────────────────────────────────────────────┐
│                     App.jsx                                 │
│  Main React Component - The Brain of the Frontend          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎤 Recording Logic                                         │
│  ├─ startRecording() - Activate microphone                 │
│  ├─ stopRecording() - Stop & get audio blob                │
│  └─ MediaRecorder API integration                          │
│                                                             │
│  🔊 Voice Cloning Flow                                      │
│  ├─ handleCloneVoice() - Main cloning function             │
│  ├─ cloneVoice() - API call to backend                     │
│  └─ Store voice_id for later use                           │
│                                                             │
│  💬 Chat Flow                                               │
│  ├─ handleChatInteraction() - Handle user questions        │
│  ├─ sendChatMessage() - Send to backend                    │
│  └─ Play audio response                                    │
│                                                             │
│  🎨 UI States                                               │
│  ├─ step: 'clone' | 'chat'                                 │
│  ├─ isRecording: true | false                              │
│  ├─ isProcessing: true | false                             │
│  └─ messages: array of conversation                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     main.py                                 │
│  FastAPI Backend - The Brain of the Backend                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔌 API Endpoints                                           │
│  ├─ / - Health check                                       │
│  ├─ /clone-voice - Voice cloning                           │
│  ├─ /transcribe - Speech-to-text                           │
│  ├─ /chat - Generate response                              │
│  ├─ /speak - Text-to-speech                                │
│  └─ /full-interaction - Complete flow                      │
│                                                             │
│  🤖 AI Integrations                                         │
│  ├─ ElevenLabs client - Voice cloning & TTS                │
│  └─ OpenAI client - Whisper & GPT-4                        │
│                                                             │
│  💾 Data Management                                         │
│  ├─ user_voices{} - In-memory voice storage                │
│  └─ Temporary file handling                                │
│                                                             │
│  🔒 Security                                                │
│  ├─ CORS configuration                                     │
│  └─ Environment variable handling                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Dependencies Overview

### Backend Python Packages
```
fastapi          - Web framework
uvicorn          - ASGI server
python-multipart - File upload handling
elevenlabs       - Voice cloning & TTS
openai           - Whisper & GPT-4
python-dotenv    - Environment variables
```

### Frontend Node Packages
```
react        - UI framework
react-dom    - React rendering
vite         - Build tool & dev server
```

## File Size Summary

```
Documentation:  ~15 KB  (6 files, very detailed!)
Backend Code:   ~12 KB  (Python)
Frontend Code:  ~15 KB  (React + CSS)
Config Files:   ~2 KB   (JSON, env templates)
Total:          ~45 KB  of actual code
```

## What Gets Created When You Run It

### During Installation:
```
backend/
├── venv/              ← Python virtual environment (100+ MB)
└── .env               ← Your API keys file

frontend/
└── node_modules/      ← JavaScript dependencies (200+ MB)
```

### During Runtime:
```
In Memory Only:
├── user_voices = {}   ← Voice ID mappings
└── temp files         ← Automatically deleted
```

## Data Flow Through Files

```
1. User interacts with → App.jsx
                          ↓
2. Audio recorded by → Web Audio API (browser)
                          ↓
3. Sent to → main.py (/clone-voice endpoint)
                          ↓
4. Processed by → ElevenLabs API
                          ↓
5. Voice ID stored in → main.py (user_voices{})
                          ↓
6. User asks question → App.jsx
                          ↓
7. Sent to → main.py (/full-interaction endpoint)
                          ↓
8. Transcribed by → OpenAI Whisper
                          ↓
9. Response from → OpenAI GPT-4
                          ↓
10. Spoken by → ElevenLabs TTS (with cloned voice)
                          ↓
11. Audio returned to → App.jsx
                          ↓
12. Played by → Browser Audio API
```

## Which Files You Need to Edit

### Required Edits:
- ✏️ **backend/.env** - Add your API keys

### Optional Edits:
- **main.py** - Change AI model, add features
- **App.jsx** - Modify UI, add functionality
- **App.css** - Change colors, styling

### Never Edit:
- ❌ Documentation files (unless fixing typos)
- ❌ Setup scripts (unless you know what you're doing)
- ❌ Config files (unless you need to change ports)

## Quick Reference Commands

```bash
# Backend
cd backend
python main.py              # Run server

# Frontend
cd frontend
npm run dev                 # Run dev server
npm run build              # Build for production

# Both
./setup.sh                 # Setup everything (Mac/Linux)
setup.bat                  # Setup everything (Windows)
```

## Total Project Stats

- **Documentation**: 6 comprehensive guides
- **Code Files**: 7 main files (3 backend, 4 frontend)
- **Languages**: Python, JavaScript, CSS, HTML
- **APIs Used**: 2 (ElevenLabs, OpenAI)
- **Lines of Code**: ~850 lines
- **Setup Scripts**: 2 (Windows & Mac/Linux)
- **Time to Setup**: 10 minutes
- **Time to First Voice Clone**: 2 minutes

---

**You now have a complete map of the entire project!** 🗺️✨
