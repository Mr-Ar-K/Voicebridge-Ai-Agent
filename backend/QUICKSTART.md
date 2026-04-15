# 🚀 VoiceBridge Backend - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GEMINI_API_KEY: Get from https://makersuite.google.com/app/apikey
# - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys
```

### Step 3: Start Qdrant Server

#### Option A: Download & Run Locally (Recommended)
```bash
# Download Qdrant (Linux/macOS)
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-unknown-linux-gnu -o qdrant
chmod +x qdrant
./qdrant

# On macOS, you may also use Homebrew:
# brew install qdrant (if available)

# On Windows, download from:
# https://github.com/qdrant/qdrant/releases
```

#### Option B: Use Qdrant Cloud (Managed)
- Sign up at https://cloud.qdrant.io
- Create a cluster
- Update `QDRANT_URL` and `QDRANT_API_KEY` in `.env`

### Step 4: Upload Scheme Data
```bash
python upload_data.py
```

### Step 5: Start FastAPI Server
```bash
python main.py
```

Server will be available at: **http://localhost:8000**

## Testing

### In a new terminal:
```bash
python test_api.py
```

### Or manually test:
```bash
# Health check
curl http://localhost:8000/health

# Process a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What schemes for farmers?", "language": "en"}'
```

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Directory Structure

```
backend/
├── main.py                 # FastAPI application
├── upload_data.py          # Data upload script
├── config.py              # Configuration settings
├── test_api.py            # API tests
├── knowledge.json         # Scheme database
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README_BACKEND.md      # Full documentation
```

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'google'"
**Solution:** Run `pip install -r requirements.txt`

### ❌ "Connection refused" (Qdrant)
**Solution:** Ensure Qdrant is running:
```bash
# Local binary
./qdrant
```

### ❌ "API key error"
**Solution:** Check your `.env` file has all required keys

### ❌ "No schemes in search results"
**Solution:** Run `python upload_data.py` to populate Qdrant

## Next Steps

1. ✅ Backend API is running
2. ⏳ Integrate with Vapi for voice input
3. ⏳ Connect frontend for user interface
4. ⏳ Add more government schemes to knowledge.json
5. ⏳ Deploy to production (AWS/GCP)

## Environment Variables Reference

```
GEMINI_API_KEY              # Required: Google Gemini API key
OPENAI_API_KEY              # Required: OpenAI API key (for embeddings)
QDRANT_URL                  # Default: http://localhost:6333
QDRANT_API_KEY             # Optional: For Qdrant cloud
GOOGLE_TRANSLATE_API_KEY   # Optional: For advanced translation
VAPI_API_KEY               # Optional: For Vapi integration
ENVIRONMENT                # Default: development
LOG_LEVEL                  # Default: INFO
```

## Commands Summary

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env

# Start services
./qdrant                           # Terminal 1 (Local Qdrant)
python upload_data.py              # Terminal 2
python main.py                     # Terminal 3

# Test
python test_api.py                 # Terminal 4
```

## Production Deployment

### Manual Setup
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

**Ready to build!** 🎉 The backend is now set up and ready to handle government scheme queries.
