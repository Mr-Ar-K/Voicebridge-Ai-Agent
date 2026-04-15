# VoiceBridge Backend - Local Setup (Without Docker)

## Quick Setup - No Docker Required ⚡

This guide covers setting up VoiceBridge backend entirely locally without Docker.

---

## Prerequisites

- **Python 3.9+** installed
- **Internet connection** (for API calls)
- **API Keys:**
  - Google Gemini API key
  - OpenAI API key
  - (Optional) Google Cloud Translate key

---

## Step 1: Clone & Navigate

```bash
cd /workspaces/Voicebridge-Ai-Agent
cd backend
```

---

## Step 2: Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected time: 2-5 minutes

---

## Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Example .env file
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
QDRANT_URL=http://localhost:6333
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Step 5: Setup Qdrant Vector Database (Locally)

### Option A: Download & Run Qdrant Binary (Recommended)

```bash
# Linux/macOS - Download Qdrant
# Choose the appropriate version from:
# https://github.com/qdrant/qdrant/releases

# For Linux:
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-unknown-linux-gnu -o qdrant
chmod +x qdrant

# For macOS (Intel):
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-apple-darwin -o qdrant
chmod +x qdrant

# For macOS (Apple Silicon):
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-aarch64-apple-darwin -o qdrant
chmod +x qdrant

# For Windows:
# Download from: https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-pc-windows-gnu.exe
```

### Option B: Using Homebrew (macOS)

```bash
brew install qdrant
```

### Option C: Build from Source

```bash
git clone https://github.com/qdrant/qdrant.git
cd qdrant
cargo build --release
```

---

## Step 6: Start Qdrant Server

Open a **new terminal** (keep this one running):

```bash
# Navigate to backend folder
cd /workspaces/Voicebridge-Ai-Agent/backend

# Run Qdrant
./qdrant

# You should see output like:
# [INFO] Starting Qdrant server...
# [INFO] Listening on 0.0.0.0:6333
```

Qdrant will be available at: **http://localhost:6333**

---

## Step 7: Upload Scheme Data

Open **another new terminal** (keep Qdrant running):

```bash
# Navigate to backend folder
cd /workspaces/Voicebridge-Ai-Agent/backend

# Activate virtual environment
source venv/bin/activate

# Upload schemes to Qdrant
python upload_data.py
```

Expected output:
```
Loading 10 schemes from knowledge.json
Processing scheme 1/10: PM Kisan...
...
Successfully uploaded 10 schemes to Qdrant!
```

---

## Step 8: Start FastAPI Server

Open **another new terminal** (keep both Qdrant and upload running):

```bash
# Navigate to backend folder
cd /workspaces/Voicebridge-Ai-Agent/backend

# Activate virtual environment
source venv/bin/activate

# Run the FastAPI server
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Step 9: Test the API

Open **another terminal** to test:

```bash
# Navigate to backend folder
cd /workspaces/Voicebridge-Ai-Agent/backend

# Activate virtual environment
source venv/bin/activate

# Run tests
python test_api.py
```

Or manually test:

```bash
# Health check
curl http://localhost:8000/health

# Process a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What schemes are available for farmers?",
    "language": "en"
  }'
```

---

## Step 10: Access API Documentation

Once the server is running, visit:

- **Swagger UI (Interactive):** http://localhost:8000/docs
- **ReDoc (Beautiful docs):** http://localhost:8000/redoc

---

## Terminal Layout

For easy management, arrange terminals like this:

```
┌─────────────────────────────────────────────┐
│  Terminal 1: Qdrant Server                  │
│  $ ./qdrant                                 │
│  [Running in background]                    │
├─────────────────────────────────────────────┤
│  Terminal 2: Upload Schemes                 │
│  $ python upload_data.py                    │
│  [Completed]                                │
├─────────────────────────────────────────────┤
│  Terminal 3: FastAPI Backend                │
│  $ python main.py                           │
│  [Running in background]                    │
├─────────────────────────────────────────────┤
│  Terminal 4: Testing/Development            │
│  $ python test_api.py                       │
│  [Use for testing]                          │
└─────────────────────────────────────────────┘
```

---

## Verifying Everything Works

### Check Qdrant Status
```bash
curl http://localhost:6333/health
# Should return: {"status":"ok"}
```

### Check Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"VoiceBridge AI Agent"}
```

### Test Full Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "I am a farmer looking for financial help",
    "language": "en"
  }'
```

Should return a JSON response with:
- `answer`: AI-generated response
- `schemes`: Relevant schemes found
- `follow_up_suggestions`: Suggested follow-up questions

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'google'"
**Solution:** Make sure virtual environment is activated and requirements installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Connection refused" when uploading data
**Solution:** Ensure Qdrant is running in another terminal
```bash
./qdrant
```

### Issue: Qdrant won't start / "Permission denied"
**Solution:** Give execute permission
```bash
chmod +x qdrant
./qdrant
```

### Issue: "API key error" from Gemini/OpenAI
**Solution:** Verify your `.env` file has correct keys
```bash
# Check .env
cat .env

# Make sure keys are filled in:
GEMINI_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

### Issue: "No schemes in search results"
**Solution:** Re-run upload script
```bash
python upload_data.py
```

### Issue: Port 6333 (Qdrant) already in use
**Solution:** Change port in `.env`
```bash
QDRANT_URL=http://localhost:6334  # Use different port
```

Then start Qdrant on that port:
```bash
./qdrant --grpc-port 6334
```

### Issue: Port 8000 (FastAPI) already in use
**Solution:** Run FastAPI on different port
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## Next Steps

### Development
- Modify `knowledge.json` to add more schemes
- Update `main.py` for custom features
- Run tests with `python test_api.py`

### Integration
- Connect to Vapi for voice (see Vapi documentation)
- Build frontend interface (web/mobile)
- Add user authentication

### Production Deployment
- See `DEPLOYMENT.md` for production options
- Qdrant Cloud vs. self-hosted
- Scaling considerations

---

## Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI backend (don't modify unless needed) |
| `upload_data.py` | Load schemes into Qdrant |
| `knowledge.json` | Edit to add/modify schemes |
| `.env` | Your configuration file |
| `test_api.py` | Test suite to verify setup |

---

## Quick Commands Cheatsheet

```bash
# Activate venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Start Qdrant
./qdrant

# Upload data
python upload_data.py

# Run backend
python main.py

# Run tests
python test_api.py

# Deactivate venv
deactivate
```

---

## Environment Variables

```bash
# Required
GEMINI_API_KEY              # Get from: https://makersuite.google.com/app/apikey
OPENAI_API_KEY              # Get from: https://platform.openai.com/api-keys

# Other services (optional)
QDRANT_URL=http://localhost:6333
GOOGLE_TRANSLATE_API_KEY=your_key
VAPI_API_KEY=your_key

# App config
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Support

- **FastAPI:** https://fastapi.tiangolo.com
- **Qdrant:** https://qdrant.tech/documentation
- **Gemini API:** https://ai.google.dev
- **OpenAI API:** https://platform.openai.com/docs

---

**✅ Ready to go!** Your VoiceBridge backend is now running locally. 🎉
