# VoiceBridge AI Backend - Setup & Deployment Guide

## Overview
The VoiceBridge Backend is a FastAPI application that integrates with Gemini AI, Qdrant vector database, and translation APIs to handle government scheme queries via voice.

## System Architecture

```
User Voice Input (Vapi)
        ↓
FastAPI Backend
        ├── Query Translation (English)
        ├── Semantic Search (Qdrant)
        ├── Context Retrieval
        ├── AI Response Generation (Gemini)
        └── Response Translation
        ↓
User Voice Output (Vapi)
```

## Prerequisites

- Python 3.9+
- Qdrant Server (local or cloud)
- API Keys for:
  - Google Gemini
  - OpenAI (for embeddings)
  - Google Cloud Translation (optional)
  - Vapi (for voice integration)

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key (if using cloud)
```

### 3. Set up Qdrant Vector Database

#### Option A: Download & Run Locally (Recommended)
```bash
# Linux/macOS
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-unknown-linux-gnu -o qdrant
chmod +x qdrant
./qdrant

# Windows: Download from https://github.com/qdrant/qdrant/releases

# macOS with Homebrew:
# brew install qdrant (if available)
```

#### Option B: Local Qdrant (Docker)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Option C: Qdrant Cloud
Create account at https://cloud.qdrant.io and get your API key.
Update `QDRANT_URL` and `QDRANT_API_KEY` in `.env`

### 4. Upload Scheme Data to Qdrant

```bash
python upload_data.py
```

This will:
- Load schemes from `knowledge.json`
- Generate embeddings for each scheme
- Upload to Qdrant with semantic search capability

## Running the Server

### Development Mode
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### 1. Health Check
- **Endpoint:** `GET /health`
- **Response:** `{"status": "ok", "service": "VoiceBridge AI Agent"}`

### 2. Initialize Qdrant (Run Once)
- **Endpoint:** `POST /initialize-qdrant`
- **Purpose:** Set up Qdrant collection with scheme embeddings
- **Response:** Success message with scheme count

### 3. Process Query
- **Endpoint:** `POST /query`
- **Request:**
```json
{
  "question": "What are benefits for farmers?",
  "language": "en"
}
```
- **Response:**
```json
{
  "answer": "PM Kisan provides ₹6,000 per year...",
  "schemes": [
    {
      "scheme_name": "PM Kisan",
      "description": "...",
      "benefits": "...",
      "eligibility": "...",
      "documents": "...",
      "application_process": "..."
    }
  ],
  "follow_up_suggestions": [
    "How do I apply?",
    "What documents do I need?"
  ],
  "language": "en"
}
```

### 4. Search Schemes
- **Endpoint:** `GET /search-schemes?query=farmer&top_k=3`
- **Purpose:** Semantic search for relevant schemes
- **Response:** List of matching schemes

### 5. Get All Schemes
- **Endpoint:** `GET /schemes`
- **Response:** All available schemes with details

### 6. Create Embeddings
- **Endpoint:** `POST /embed`
- **Request:** `{"text": "your text here"}`
- **Response:** Embedding vector and dimensions

## Key Features

### 1. Multilingual Support
- Telugu ↔ English translation integration
- Automatic language detection

### 2. Semantic Search
- Vector embeddings using text-embedding-3-small
- Qdrant cosine similarity search
- Context-aware scheme retrieval

### 3. AI Response Generation
- Gemini 1.5 Flash for natural language generation
- Simple explanations for low literacy users
- Follow-up suggestion generation

### 4. Context Management
- Session tracking (for future enhancements)
- Conversation history (optional)
- Multi-turn support ready

## File Structure

```
backend/
├── main.py                 # FastAPI app with all endpoints
├── upload_data.py          # Data upload script for Qdrant
├── knowledge.json          # Government schemes database
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (keep secret)
├── .env.example            # Example environment file
└── README_BACKEND.md       # This file
```

## Testing the API

### Using curl

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

# Search schemes
curl "http://localhost:8000/search-schemes?query=education&top_k=3"
```

### Using Python

```python
import requests

# Process query
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "I want to learn new skills, what options are available?",
        "language": "en"
    }
)

print(response.json())
```

## Troubleshooting

### Issue: Qdrant Connection Failed
- Ensure Qdrant server is running
- Check `QDRANT_URL` in `.env`

### Issue: API Key Errors
- Verify all API keys in `.env` are correct
- Check API key permissions/quotas

### Issue: Low Search Quality
- Run `upload_data.py` again to refresh embeddings
- Check if knowledge.json has been updated

### Issue: Translation Not Working
- Google Cloud Translation requires service account setup
- Fallback to English translation

## Performance Optimization

### For Production:
1. Use connection pooling for APIs
2. Implement caching for frequent queries
3. Use Qdrant cloud for scalability
4. Add rate limiting
5. Implement request batching

## Security Considerations

1. Never commit `.env` file (add to `.gitignore`)
2. Use environment variables for all secrets
3. Implement API authentication
4. Add request validation
5. Use HTTPS in production
6. Implement rate limiting

## Future Enhancements

1. Real-time web search integration
2. More government schemes database
3. Personalized recommendations
4. Regional language expansion (Hindi, Tamil, etc.)
5. Admin dashboard for scheme management
6. Analytics and usage tracking

## Support

For issues or questions:
1. Check error logs in terminal
2. Review Qdrant collection status
3. Test API endpoints individually
4. Verify all environment variables

---

**VoiceBridge Backend v1.0.0** | Accessibility & Impact through AI
