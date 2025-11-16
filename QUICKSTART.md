# 🚀 QUICK START GUIDE

## Get Your API Keys First!

1. **ElevenLabs API Key**: 
   - Go to https://elevenlabs.io/app/settings/api-keys
   - Sign up (free tier available)
   - Create a new API key
   - Copy it

2. **OpenAI API Key**:
   - Go to https://platform.openai.com/api-keys
   - Sign up (you'll need to add payment info)
   - Create a new API key
   - Copy it

## Installation (Choose Your OS)

### Windows:
```cmd
# Double-click setup.bat
# OR run in Command Prompt:
setup.bat
```

### Mac/Linux:
```bash
# Run in Terminal:
chmod +x setup.sh
./setup.sh
```

### Manual Setup:
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys

# Frontend (in new terminal)
cd frontend
npm install
```

## Add Your API Keys

Edit `backend/.env`:
```
ELEVENLABS_API_KEY=sk_your_actual_key_here
OPENAI_API_KEY=sk-your_actual_key_here
```

## Run the App

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Open Browser:**
- Go to http://localhost:3000

## How to Use

1. **Clone Your Voice:**
   - Click "Start Recording"
   - Speak for 1-2 minutes
   - Click "Stop Recording & Clone Voice"
   - Wait ~20 seconds

2. **Chat:**
   - Click "Record Question"
   - Ask anything
   - Click "Stop Recording & Send"
   - Listen to YOUR voice respond!

## Troubleshooting

**Backend won't start?**
- Check you activated the virtual environment
- Check your API keys in .env file
- Run: `pip install -r requirements.txt`

**Frontend won't start?**
- Run: `npm install`
- Make sure you're on Node.js 18+

**No sound?**
- Check browser console (F12)
- Allow microphone permissions
- Make sure backend is running

**Poor voice quality?**
- Re-record in a quiet room
- Speak clearly for 1-2 minutes
- Use a better microphone

## Need Help?

Check the full README.md for detailed documentation!

Enjoy chatting with yourself! 🎤✨
