# VoiceBridge Backend Architecture

## System Overview

VoiceBridge is a multilingual voice-first AI platform designed to provide accessible information about government schemes in India. The backend orchestrates semantic search, natural language generation, and translation to create a seamless experience.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  (Web/Mobile Frontend with Vapi Voice Integration)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   FastAPI Backend (main.py)                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Route Layer                                              │   │
│  │ • /query - Process user question                        │   │
│  │ • /search-schemes - Semantic search                     │   │
│  │ • /embed - Create embeddings                            │   │
│  │ • /initialize-qdrant - Setup database                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Processing Pipeline                                     │   │
│  │                                                         │   │
│  │ 1. Language Detection & Translation                    │   │
│  │    └─→ Google Translate API                           │   │
│  │                                                         │   │
│  │ 2. Embedding Generation                               │   │
│  │    └─→ OpenAI text-embedding-3-small                 │   │
│  │                                                         │   │
│  │ 3. Semantic Search                                    │   │
│  │    └─→ Qdrant Vector Database                        │   │
│  │                                                         │   │
│  │ 4. Response Generation                                │   │
│  │    └─→ Google Gemini 1.5 Flash                       │   │
│  │                                                         │   │
│  │ 5. Response Translation                               │   │
│  │    └─→ Google Translate API                          │   │
│  │                                                         │   │
│  │ 6. Follow-up Suggestions                              │   │
│  │    └─→ Extract from AI response                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Qdrant DB   │  │  Gemini API  │  │  OpenAI API  │
│ (Vectors)    │  │ (Text Gen)   │  │ (Embeddings) │
└──────────────┘  └──────────────┘  └──────────────┘
        │
        ▼
┌──────────────────────┐
│  knowledge.json      │
│  (Scheme Metadata)   │
└──────────────────────┘
```

## Component Details

### 1. FastAPI Application (`main.py`)

**Responsibilities:**
- HTTP request routing
- Request validation using Pydantic models
- Response serialization
- Error handling and logging
- API documentation (Swagger/ReDoc)

**Key Classes:**
- `QueryRequest`: Input model for user queries
- `QueryResponse`: Output model with AI response and metadata
- `SchemeContext`: Individual scheme information

### 2. Embedding Service

**Model:** OpenAI text-embedding-3-small
**Dimensions:** 1536
**Purpose:** Convert text into vector representations for semantic search

**Process:**
```
Text Input
    ↓
OpenAI API
    ↓
1536-dimensional Vector
```

### 3. Vector Database (Qdrant)

**Purpose:** Store and retrieve scheme embeddings based on semantic similarity

**Configuration:**
- Collection: `government_schemes`
- Distance Metric: Cosine Similarity
- Vector Dimension: 1536

**Data Structure:**
```json
{
  "id": 1,
  "vector": [0.123, -0.456, ...],
  "payload": {
    "name_en": "PM Kisan",
    "description_en": "...",
    "category": "Agriculture",
    ...
  }
}
```

### 4. AI Response Generation (Gemini)

**Model:** gemini-1.5-flash
**Purpose:** Generate natural language responses based on context

**Prompt Structure:**
```
System: You are a helpful AI assistant explaining government schemes...

Context: [Relevant scheme information]

User Question: [User's translated question]

Response: [AI-generated explanation]
```

### 5. Translation Layer

**Service:** Google Cloud Translation API
**Supported Languages:** English, Telugu
**Implementation:** Automatic language detection and translation

**Flow:**
```
User Input (Telugu)
    ↓
Translate to English
    ↓
Processing
    ↓
Generate Response
    ↓
Translate back to Telugu
    ↓
User Output (Telugu)
```

## Data Flow

### Query Processing Flow

```
1. USER SENDS QUERY
   Input: user_question (in Telugu/English), language preference

2. LANGUAGE DETECTION & TRANSLATION
   If not English:
   - Translate question to English
   - Log translation

3. EMBEDDING CREATION
   - Convert English question to 1536-dimensional vector
   - Using OpenAI embedding model

4. SEMANTIC SEARCH
   - Query Qdrant with embedding vector
   - Get top 3 most similar schemes
   - Calculate cosine similarity scores

5. CONTEXT PREPARATION
   - Prepare prompt with:
     * System instructions
     * Relevant scheme information
     * User question

6. AI RESPONSE GENERATION
   - Send to Gemini API
   - Get natural language response
   - Extract follow-up suggestions

7. RESPONSE TRANSLATION
   If user language is Telugu:
   - Translate response to Telugu
   - Translate suggestions to Telugu

8. RESPONSE FORMATTING
   - Create QueryResponse object:
     * Answer text
     * Scheme information
     * Follow-up suggestions
     * Language metadata

9. CLIENT RECEIVES RESPONSE
   Output: Fully formatted response ready for voice synthesis
```

## Data Models

### Request/Response Models

```python
class QueryRequest:
    question: str           # User's query
    language: str          # "en" or "te"
    session_id: Optional[str]  # For conversation tracking

class QueryResponse:
    answer: str            # AI-generated response
    schemes: List[SchemeContext]  # Relevant schemes
    follow_up_suggestions: List[str]  # Suggested next questions
    language: str          # Response language

class SchemeContext:
    scheme_name: str
    description: str
    benefits: str
    eligibility: str
    documents: str
    application_process: str
```

## Configuration Management

**File:** `config.py`

**Key Settings:**
- API Keys
- Qdrant connection details
- Embedding model parameters
- Model selection and parameters
- Language configuration
- Search thresholds

## Database Schema

### knowledge.json Structure

```json
{
  "schemes": [
    {
      "id": 1,
      "name_en": "PM Kisan",
      "name_te": "PM కిసాన్",
      "category": "Agriculture",
      "description_en": "...",
      "description_te": "...",
      "benefits_en": "...",
      "eligibility_en": "...",
      "documents_en": "...",
      "application_process_en": "..."
    },
    ...
  ]
}
```

## API Endpoints

### Core Endpoints

```
POST /query
├─ Input: QueryRequest
├─ Process: Full query processing pipeline
└─ Output: QueryResponse

GET /search-schemes
├─ Input: query string, top_k
├─ Process: Semantic search only
└─ Output: List of schemes

POST /embed
├─ Input: text
├─ Process: Create embeddings
└─ Output: embedding vector

POST /initialize-qdrant
├─ Input: None (uses knowledge.json)
├─ Process: Upload all schemes to Qdrant
└─ Output: Status and count

GET /schemes
├─ Input: None
├─ Process: Load from file
└─ Output: All schemes

GET /health
├─ Input: None
├─ Process: Health check
└─ Output: Status

GET /qdrant-info
├─ Input: None
├─ Process: Query Qdrant
└─ Output: Collection info
```

## Error Handling

### Error Types

1. **Validation Errors (400)**
   - Invalid input format
   - Missing required fields

2. **API Errors (500)**
   - API key issues
   - Rate limiting
   - Service unavailable

3. **Database Errors (500)**
   - Qdrant connection failures
   - Query failures

4. **Processing Errors (500)**
   - Embedding generation failures
   - Translation failures
   - AI response generation failures

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Performance Considerations

### Latency Targets
- Health check: <50ms
- Search-only: <500ms
- Full query: <2000ms (including all APIs)

### Optimization Strategies
1. **Caching:**
   - Cache popular queries
   - Cache embeddings

2. **Batching:**
   - Batch API requests
   - Batch embeddings generation

3. **Connection Pooling:**
   - Reuse HTTP connections
   - Connection pools for each API

4. **Async/Parallel:**
   - Parallel API calls where possible
   - Non-blocking I/O

## Security Considerations

1. **API Keys:**
   - Store in environment variables
   - Never commit .env file
   - Rotate keys regularly

2. **Rate Limiting:**
   - Implement per-user/IP limits
   - Prevent abuse

3. **Input Validation:**
   - Validate all inputs
   - Sanitize user input
   - Length limits on queries

4. **HTTPS:**
   - Use HTTPS in production
   - Certificate management

5. **Logging:**
   - Log all requests (except keys)
   - Monitor for anomalies

## Deployment Architecture

### Development
```
Local Machine
├── FastAPI (port 8000)
├── Qdrant - Local or Docker (port 6333)
│   ├── Option A: Local binary (recommended)
│   └── Option B: Docker container
└── APIs (external)
```

### Production
```
Cloud Infrastructure
├── Kubernetes/Container Orchestration (optional)
├── FastAPI (multiple instances)
├── Qdrant (managed service or self-hosted)
├── Load Balancer
├── CDN
└── Monitoring/Logging
```

## Future Enhancements

1. **Conversation Memory:**
   - Track conversation history
   - Context-aware responses

2. **Caching Layer:**
   - Redis for query results
   - Embedding cache

3. **Analytics:**
   - Track popular queries
   - User engagement metrics

4. **Advanced NLP:**
   - Named entity recognition
   - Intent classification

5. **Multi-language Support:**
   - Expand beyond Telugu/English
   - Regional language support

6. **Real-time Updates:**
   - Automatically sync new schemes
   - Live data integration

---

**Architecture Version:** 1.0
**Last Updated:** 16/04/26
**Maintainer:** VoiceBridge Development Team
