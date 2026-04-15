"""
Configuration module for VoiceBridge backend.
Centralizes all configuration settings and environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== API Keys ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
VAPI_API_KEY = os.getenv("VAPI_API_KEY")

# ==================== Qdrant Configuration ====================
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "government_schemes"

# ==================== Embedding Configuration ====================
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# ==================== LLM Configuration ====================
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7

# ==================== Application Configuration ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_HOST = "0.0.0.0"
API_PORT = 8000

# ==================== Application Metadata ====================
APP_TITLE = "VoiceBridge AI Agent"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Multilingual Voice AI for Government Schemes in India"

# ==================== Search Configuration ====================
DEFAULT_TOP_K = 3
MAX_TOP_K = 10
MIN_SIMILARITY_SCORE = 0.3

# ==================== Language Configuration ====================
SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "Telugu"
}
DEFAULT_LANGUAGE = "en"

# ==================== File Paths ====================
KNOWLEDGE_FILE = "knowledge.json"

# ==================== Validation ====================
def validate_configuration():
    """Validate that all required configuration is present."""
    required_keys = [
        "GEMINI_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
    
    return True

if __name__ == "__main__":
    try:
        validate_configuration()
        print("✓ Configuration validated successfully")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
