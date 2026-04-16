import os
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from groq import Groq
from google.cloud import translate_v2
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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge.json")

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Initialize Qdrant client
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize Google Translate client
try:
    translate_client = translate_v2.Client()
except Exception:
    translate_client = None
    logger.warning("Google Cloud Translate client not initialized")

# Constants
COLLECTION_NAME = "government_schemes"
EMBEDDING_DIMENSION = 384

# Simple in-memory conversation memory by session_id.
session_memory = {}

# ==================== Pydantic Models ====================

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


def detect_language(text: str) -> str:
    """Detect language with lightweight script and Roman-keyword heuristics."""
    text_lower = text.lower()
    tokens = text_lower.split()

    # Detect Telugu script characters.
    if any("\u0C00" <= c <= "\u0C7F" for c in text):
        return "te"

    # Detect Hindi (Devanagari) script characters.
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "hi"

    # Roman Telugu keywords.
    telugu_words = [
        "raitu",
        "raithu",
        "panta",
        "unnaya",
        "ela",
        "apply",
        "scheme",
        "documents",
    ]

    # Roman Hindi keywords.
    hindi_words = [
        "kisan",
        "yojana",
        "kaise",
        "apply",
        "documents",
        "kaun",
        "eligible",
    ]

    telugu_markers = ["raitu", "raithu", "panta", "unnaya", "ela"]
    hindi_markers = ["kisan", "yojana", "kaise", "kaun"]

    if any(word in text_lower for word in telugu_markers) or any(word in tokens for word in telugu_words):
        return "te"

    if any(word in text_lower for word in hindi_markers) or any(word in tokens for word in hindi_words):
        return "hi"

    # Default fallback.
    return "en"


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
    """Embeddings are not supported in this deployment."""
    raise RuntimeError("Embeddings are unavailable. Use the /search-schemes endpoint for fallback search.")


def search_schemes(query: str, top_k: int = 5) -> List[dict]:
    """Search for relevant schemes using lightweight category-aware scoring."""
    try:
        schemes = load_schemes_from_json()
        query_lower = query.lower()
        query_tokens = [
            token.strip(".,!?()[]{}:;\"'")
            for token in query_lower.split()
            if token.strip(".,!?()[]{}:;\"'")
        ]

        student_keywords = ["student", "scholarship", "education", "college", "school", "study"]
        farmer_keywords = ["farmer", "kisan", "agriculture", "crop", "raitu", "farming"]
        job_keywords = ["job", "employment", "skill", "training", "pmkvy"]

        student_intent = any(word in query_lower for word in student_keywords)
        farmer_intent = any(word in query_lower for word in farmer_keywords)
        job_intent = any(word in query_lower for word in job_keywords)

        student_scheme_markers = ["student", "scholarship", "education", "school", "college"]
        farmer_scheme_markers = ["farmer", "kisan", "agriculture", "crop", "farming", "raitu"]
        job_scheme_markers = ["job", "employment", "skill", "training", "pmkvy"]

        scored = []

        for scheme in schemes:
            name_text = scheme.get("name_en", "").lower()
            description_text = scheme.get("description_en", "").lower()
            benefits_text = scheme.get("benefits_en", "").lower()
            text = (
                name_text + " " +
                description_text + " " +
                benefits_text
            ).lower()

            score = 0
            for word in query_tokens:
                if word in text:
                    score += 1
                if word in name_text:
                    score += 2

            # Category boosts by user intent.
            if student_intent:
                if any(marker in text for marker in student_scheme_markers):
                    score += 5
                if any(marker in name_text for marker in student_scheme_markers):
                    score += 2
                if any(marker in text for marker in farmer_scheme_markers + job_scheme_markers):
                    score -= 2

            if farmer_intent:
                if any(marker in text for marker in farmer_scheme_markers):
                    score += 5
                if any(marker in name_text for marker in farmer_scheme_markers):
                    score += 2
                if any(marker in text for marker in student_scheme_markers + job_scheme_markers):
                    score -= 2

            if job_intent:
                if any(marker in text for marker in job_scheme_markers):
                    score += 5
                if any(marker in name_text for marker in job_scheme_markers):
                    score += 2
                if any(marker in text for marker in student_scheme_markers + farmer_scheme_markers):
                    score -= 2

            scored.append((score, scheme))

        # Prefer education-category schemes for student intent when category metadata exists.
        if student_intent:
            education_scored = []
            for score, scheme in scored:
                category_text = str(
                    scheme.get("category")
                    or scheme.get("category_en")
                    or ""
                ).lower()
                if "education" in category_text:
                    education_scored.append((score, scheme))
            if education_scored:
                scored = education_scored

        # Remove irrelevant schemes and return only positively matched items.
        scored = [(score, scheme) for score, scheme in scored if score > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [scheme for score, scheme in scored[:top_k]]
    except Exception as e:
        logger.error(f"Search fallback error: {e}")
        return []


def _get_text_from_response(response) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "text") and response.text:
        return response.text
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list) and content:
            return getattr(content[0], "text", None) or str(content[0])
        return str(content)
    if hasattr(response, "output"):
        output = response.output
        if isinstance(output, list) and output:
            return getattr(output[0], "text", None) or str(output[0])
        return str(output)
    return str(response)






def generate_response(question, schemes, user_language):
    if groq_client is None:
        raise RuntimeError("GROQ_API_KEY is not configured")

    context = ""

    for s in schemes:
        context += f"""
Scheme: {s.get('name_en')}

Description:
{s.get('description_en')}

Benefits:
{s.get('benefits_en')}

Eligibility:
{s.get('eligibility_en')}

Application:
{s.get('application_process_en')}

Link:
{s.get('link', '')}

Website:
{s.get('website', '')}

---
"""

    one_scheme_instruction = ""
    if len(schemes) == 1:
        one_scheme_instruction = "I found 1 relevant scheme:"

    prompt = f"""
You are an AI assistant that explains Indian government schemes.

IMPORTANT RULES:

Only use information from the provided context.
Do NOT invent schemes.
If no relevant scheme found, say:
"I could not find a relevant scheme. Please rephrase your question."

Respond in simple English only.

Focus on matching scheme category with user question.

Example:
If question is about students -> return scholarship schemes.
If question is about farmers -> return agriculture schemes.
If question is about jobs -> return skill or employment schemes.

Provide:

1. short explanation
2. key benefits
3. who can apply
4. how to apply

If a scheme includes a link, include it clearly in the answer.
Example: "You can apply online at https://scholarships.gov.in"

Speak website links naturally in simple spoken format.
Example:
https://scholarships.gov.in
should be spoken as:
scholarships dot gov dot in
Do not spell letters one by one.

User may speak Indian languages using English letters.
Understand meaning even if language is mixed.

Examples:
raitu schemes
vidyarthi scholarship
pension scheme details
Examples:
telugu written in english letters
hinglish
mixed language
Understand intent correctly.
Example:
vidyarthula schemes unnaya
means
student schemes available

If user asks for link or website:
Provide only the relevant scheme link clearly.
Example response:
You can apply online at scholarships.gov.in

Then provide 2 follow-up questions.

If only one relevant scheme exists, start with this exact line:
{one_scheme_instruction}

Context:
{context}

User question:
{question}

Answer clearly.
Do not mix languages.
Use simple sentences.
"""

    models_to_try = [GROQ_MODEL] + GROQ_FALLBACK_MODELS
    tried_models = []

    for model_name in models_to_try:
        if not model_name or model_name in tried_models:
            continue
        tried_models.append(model_name)
        try:
            completion = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            text = completion.choices[0].message.content or ""
            followups = extract_follow_up_questions(text)
            return text, followups
        except Exception as e:
            logger.warning("Groq generation failed for model %s: %s", model_name, e)

    raise RuntimeError(
        "Groq generation failed for all models. "
        f"Tried: {', '.join(tried_models)}"
    )


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


def get_localized_scheme_value(scheme: dict, field_base: str, language: str) -> str:
    """Return the localized scheme field value, falling back to English."""
    localized_key = f"{field_base}_{language}"
    fallback_key = f"{field_base}_en"
    return scheme.get(localized_key) or scheme.get(fallback_key, "")


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
async def search_schemes_endpoint(query: str, top_k: int = 5):
    """Search for relevant schemes based on query."""
    try:
        schemes = search_schemes(query, top_k)
        return schemes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search-schemes", response_model=List[dict])
async def search_schemes_endpoint_get(query: str, top_k: int = 5):
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
        question_text = request.question or ""
        session_id = request.session_id.strip() if request.session_id else None

        # Detect user language from the incoming question
        user_language = detect_language(question_text)
        question_en = question_text
        
        if user_language != "en":
            question_en = translate_text(question_text, user_language, "en")
            logger.info(f"Detected language: {user_language}; translated question for processing: {question_text} -> {question_en}")
        else:
            logger.info(f"Detected language: {user_language}")

        # Reuse prior schemes for short or vague follow-up queries in the same session.
        question_lower = question_text.lower()
        question_tokens = [token for token in question_lower.split() if token]
        vague_phrases = {
            "eligibility",
            "how to apply",
            "documents needed",
            "benefits",
        }
        is_short_or_vague = len(question_tokens) <= 3 or any(phrase in question_lower for phrase in vague_phrases)

        if session_id and session_id in session_memory and is_short_or_vague:
            previous_data = session_memory[session_id]
            relevant_schemes = previous_data.get("last_schemes", [])
            if not relevant_schemes:
                relevant_schemes = search_schemes(question_text, top_k=5)
        else:
            relevant_schemes = search_schemes(question_text, top_k=5)

        response_language = "en"
        
        # Generate AI response
        response_text, follow_up_questions = generate_response(question_en, relevant_schemes, user_language)

        if session_id:
            session_memory[session_id] = {
                "last_question": question_text,
                "last_schemes": relevant_schemes,
            }
        
        # Prepare scheme context for response
        schemes_context = []
        for scheme in relevant_schemes:
            schemes_context.append(
                SchemeContext(
                    scheme_name=get_localized_scheme_value(scheme, "name", response_language),
                    description=get_localized_scheme_value(scheme, "description", response_language),
                    benefits=get_localized_scheme_value(scheme, "benefits", response_language),
                    eligibility=get_localized_scheme_value(scheme, "eligibility", response_language),
                    documents=get_localized_scheme_value(scheme, "documents", response_language),
                    application_process=get_localized_scheme_value(scheme, "application_process", response_language)
                )
            )
        
        return QueryResponse(
            answer=response_text,
            schemes=schemes_context,
            follow_up_suggestions=follow_up_questions,
            language=response_language
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
        
        # Add schemes to Qdrant where embeddings are available
        points = []
        for idx, scheme in enumerate(schemes):
            combined_text = f"{scheme.get('name_en', '')} {scheme.get('description_en', '')} {scheme.get('benefits_en', '')}"
            try:
                embedding = get_embeddings(combined_text)
                point = PointStruct(
                    id=idx + 1,
                    vector=embedding,
                    payload=scheme
                )
                points.append(point)
            except Exception as embed_err:
                logger.warning("Skipping scheme %s due to missing embedding: %s", scheme.get("name_en", ""), embed_err)

        if points:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            logger.info(f"Added {len(points)} schemes to Qdrant")
        else:
            logger.warning("No Qdrant points uploaded because embeddings are unavailable")

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
