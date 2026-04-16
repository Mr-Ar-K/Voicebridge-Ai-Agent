import os
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from google.cloud import translate_v2
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="VoiceBridge AI Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge.json")

# Initialize clients
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize Qdrant client
try:
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
except Exception as e:
    qdrant_client = None
    logger.warning(f"Qdrant client not initialized: {e}")

# Initialize Google Translate client
try:
    if GOOGLE_TRANSLATE_API_KEY:
        translate_client = translate_v2.Client(
            client_options=ClientOptions(api_key=GOOGLE_TRANSLATE_API_KEY)
        )
    else:
        translate_client = translate_v2.Client()
except Exception:
    translate_client = None
    logger.warning("Google Cloud Translate client not initialized")

# Constants
COLLECTION_NAME = "government_schemes"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# ==================== Pydantic Models ====================

class QueryRequest(BaseModel):
    question: str
    language: str = "en"  # "en" or "te"
    session_id: Optional[str] = None


class SchemeContext(BaseModel):
    scheme_name: str
    description: str
    benefits: str
    eligibility: str
    documents: str
    application_process: str


class QueryResponse(BaseModel):
    answer: str
    schemes: List[SchemeContext]
    follow_up_suggestions: List[str]
    language: str


class EmbeddingRequest(BaseModel):
    text: str


# ==================== Helper Functions ====================

def translate_text(text: str, source_language: str, target_language: str) -> str:
    """Translate text using Google Translate API."""
    if source_language == target_language:
        return text
    
    try:
        if translate_client:
            result = translate_client.translate(
                text,
                source_language=source_language,
                target_language=target_language
            )
            return result["translatedText"]
    except Exception as e:
        logger.error(f"Translation error: {e}")
    
    return text


def get_embeddings(text: str) -> List[float]:
    """Generate embeddings using OpenAI's text-embedding-3-small model."""
    try:
        if not openai_client:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


def search_schemes(query: str, top_k: int = 3) -> List[dict]:
    """Search for relevant schemes using Qdrant semantic search."""
    try:
        if not qdrant_client:
            logger.warning("Qdrant client is not available")
            return []
        # Get embeddings for the query
        query_embedding = get_embeddings(query)
        
        # Search in Qdrant
        search_results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k
        )
        
        schemes = []
        for result in search_results.points:
            scheme_data = result.payload
            schemes.append(scheme_data)
        
        return schemes
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []


def generate_response(question: str, scheme_context: List[dict]) -> tuple:
    """Generate AI response using Gemini with scheme context."""
    try:
        # Prepare context prompt
        context_text = "Relevant Government Schemes Information:\n\n"
        for scheme in scheme_context:
            context_text += f"""
Scheme: {scheme.get('name_en', '')}
Description: {scheme.get('description_en', '')}
Benefits: {scheme.get('benefits_en', '')}
Eligibility: {scheme.get('eligibility_en', '')}
Documents Required: {scheme.get('documents_en', '')}
Application Process: {scheme.get('application_process_en', '')}
---
"""
        
        # Create the prompt
        system_prompt = """You are a helpful AI assistant for explaining government schemes in India. 
        Your job is to:
        1. Provide clear, simple explanations suitable for low literacy users
        2. Focus on benefits, eligibility, and application process
        3. Use everyday language
        4. Be concise and avoid jargon
        5. At the end, suggest 2-3 follow-up questions the user might want to ask"""
        
        full_prompt = f"""{system_prompt}

{context_text}

User Question: {question}

Please provide a helpful response in simple language."""
        
        # Generate response using Gemini
        if not genai_client:
            raise RuntimeError("Gemini service unavailable: GEMINI_API_KEY is not configured")
        response = genai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=full_prompt
        )
        
        answer_text = response.text
        
        # Extract follow-up suggestions from the response
        follow_up_suggestions = extract_follow_up_questions(answer_text)
        
        return answer_text, follow_up_suggestions
    
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        raise


def extract_follow_up_questions(response_text: str) -> List[str]:
    """Extract follow-up suggestions from the generated response."""
    suggestions = []
    
    # Look for bullet points or numbered lists in the response
    lines = response_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("•") or line.startswith("-") or line[0].isdigit():
            # Clean up the suggestion
            suggestion = line.lstrip("•-0123456789. ")
            if suggestion and len(suggestion) > 5:
                suggestions.append(suggestion)
    
    # Return top 3 suggestions
    return suggestions[:3] if suggestions else [
        "What are the eligibility criteria?",
        "How do I apply for this scheme?",
        "What documents do I need?"
    ]


def load_schemes_from_json() -> List[dict]:
    """Load schemes from knowledge.json file."""
    try:
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("schemes", [])
    except Exception as e:
        logger.error(f"Error loading schemes: {e}")
        return []


# ==================== API Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "VoiceBridge AI Agent"}


@app.post("/embed", response_model=dict)
async def create_embedding(request: EmbeddingRequest):
    """Create embeddings for given text."""
    try:
        embedding = get_embeddings(request.text)
        return {"text": request.text, "embedding": embedding, "dimension": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-schemes", response_model=List[dict])
async def search_schemes_endpoint(query: str, top_k: int = 3):
    """Search for relevant schemes based on query."""
    try:
        schemes = search_schemes(query, top_k)
        return schemes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search-schemes", response_model=List[dict])
async def search_schemes_endpoint_get(query: str, top_k: int = 3):
    """Search for relevant schemes based on query (GET variant)."""
    try:
        schemes = search_schemes(query, top_k)
        return schemes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query and return AI response with relevant schemes."""
    try:
        # Translate question to English if needed for processing
        question_en = request.question
        user_language = request.language
        
        if user_language == "te":
            # Translate Telugu to English for processing
            question_en = translate_text(request.question, "te", "en")
            logger.info(f"Translated question: {request.question} -> {question_en}")
        
        # Search for relevant schemes
        relevant_schemes = search_schemes(question_en, top_k=3)
        
        # Generate AI response
        response_text, follow_up_questions = generate_response(question_en, relevant_schemes)
        
        # Translate response back to user's language if needed
        if user_language == "te":
            response_text = translate_text(response_text, "en", "te")
            follow_up_questions = [translate_text(q, "en", "te") for q in follow_up_questions]
        
        # Prepare scheme context for response
        schemes_context = []
        for scheme in relevant_schemes:
            scheme_key = "name_en" if user_language == "en" else "name_te"
            desc_key = "description_en" if user_language == "en" else "description_te"
            benefits_key = "benefits_en" if user_language == "en" else "benefits_en"  # Note: keeping English for now
            eligibility_key = "eligibility_en"
            documents_key = "documents_en"
            application_key = "application_process_en"
            
            schemes_context.append(
                SchemeContext(
                    scheme_name=scheme.get(scheme_key, ""),
                    description=scheme.get(desc_key, ""),
                    benefits=scheme.get(benefits_key, ""),
                    eligibility=scheme.get(eligibility_key, ""),
                    documents=scheme.get(documents_key, ""),
                    application_process=scheme.get(application_key, "")
                )
            )
        
        return QueryResponse(
            answer=response_text,
            schemes=schemes_context,
            follow_up_suggestions=follow_up_questions,
            language=user_language
        )
    
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schemes")
async def get_all_schemes():
    """Get all available schemes."""
    try:
        schemes = load_schemes_from_json()
        return {"count": len(schemes), "schemes": schemes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/initialize-qdrant")
async def initialize_qdrant():
    """Initialize Qdrant with scheme data. Call this once to set up vector database."""
    try:
        # Load schemes from JSON
        schemes = load_schemes_from_json()
        
        # Delete existing collection if it exists
        try:
            qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass
        
        # Create new collection
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {COLLECTION_NAME}")
        
        # Add schemes to Qdrant
        points = []
        for idx, scheme in enumerate(schemes):
            # Create combined text for embedding
            combined_text = f"{scheme.get('name_en', '')} {scheme.get('description_en', '')} {scheme.get('benefits_en', '')}"
            
            # Generate embedding
            embedding = get_embeddings(combined_text)
            
            # Create point for Qdrant
            point = PointStruct(
                id=idx + 1,
                vector=embedding,
                payload=scheme
            )
            points.append(point)
        
        # Upload points to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        logger.info(f"Added {len(points)} schemes to Qdrant")
        
        return {
            "status": "success",
            "message": f"Qdrant initialized with {len(points)} schemes",
            "collection": COLLECTION_NAME
        }
    
    except Exception as e:
        logger.error(f"Qdrant initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qdrant-info")
async def get_qdrant_info():
    """Get information about Qdrant collections."""
    try:
        collections = qdrant_client.get_collections()
        collection_names = [collection.name for collection in collections.collections]
        return {"collections": collection_names, "count": len(collection_names)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
