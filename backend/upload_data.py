"""
Script to upload government schemes data to Qdrant vector database.
This prepares the vector database with embeddings for semantic search.
"""

import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure APIs
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Constants
COLLECTION_NAME = "government_schemes"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.json")


def get_embeddings(text: str) -> list:
    """Generate embeddings using OpenAI's text-embedding-3-small model."""
    try:
        if not openai_client:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def load_schemes() -> list:
    """Load schemes from knowledge.json file."""
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            schemes = data.get("schemes", [])
            logger.info(f"Loaded {len(schemes)} schemes from {KNOWLEDGE_FILE}")
            return schemes
    except Exception as e:
        logger.error(f"Error loading schemes: {e}")
        raise


def create_collection():
    """Create Qdrant collection for storing scheme embeddings."""
    try:
        # Delete existing collection if it exists
        try:
            qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.info(f"No existing collection to delete: {e}")
        
        # Create new collection
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
        )
        logger.info(f"Created new collection: {COLLECTION_NAME} with dimension {EMBEDDING_DIMENSION}")
        
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise


def upload_schemes_to_qdrant():
    """Upload scheme embeddings to Qdrant."""
    try:
        # Load schemes
        schemes = load_schemes()
        
        # Create collection
        create_collection()
        
        # Generate embeddings and create points
        points = []
        for idx, scheme in enumerate(schemes):
            try:
                # Create combined text for embedding (includes name, description, and benefits)
                combined_text = (
                    f"{scheme.get('name_en', '')} "
                    f"{scheme.get('description_en', '')} "
                    f"{scheme.get('benefits_en', '')} "
                    f"{scheme.get('category', '')}"
                )
                
                logger.info(f"Processing scheme {idx + 1}/{len(schemes)}: {scheme.get('name_en', '')}")
                
                # Generate embedding
                embedding = get_embeddings(combined_text)
                
                # Create point for Qdrant
                point = PointStruct(
                    id=idx + 1,
                    vector=embedding,
                    payload=scheme
                )
                points.append(point)
                
            except Exception as e:
                logger.warning(f"Error processing scheme {idx + 1}: {e}")
                continue
        
        # Upload points to Qdrant in batches
        batch_size = 10
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch
                )
                logger.info(f"Uploaded batch {i // batch_size + 1} ({len(batch)} schemes)")
            except Exception as e:
                logger.error(f"Error uploading batch: {e}")
                raise
        
        logger.info(f"Successfully uploaded {len(points)} schemes to Qdrant")
        
        # Verify collection info
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        logger.info(f"Collection info: {collection_info.points_count} points stored")
        
        return len(points)
    
    except Exception as e:
        logger.error(f"Error uploading schemes to Qdrant: {e}")
        raise


def verify_setup():
    """Verify the Qdrant setup and test a sample search."""
    try:
        logger.info("Verifying Qdrant setup...")
        
        # Check collection exists
        collections = qdrant_client.get_collections()
        logger.info(f"Available collections: {[c.name for c in collections.collections]}")
        
        # Get collection info
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' has {collection_info.points_count} points")
        
        # Test search
        test_query = "farmer financial support"
        test_embedding = get_embeddings(test_query)
        search_results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=test_embedding,
            limit=3
        )
        
        logger.info(f"Test search results for '{test_query}':")
        for result in search_results.points:
            scheme_name = result.payload.get('name_en', 'Unknown')
            logger.info(f"  - {scheme_name} (similarity: {result.score:.2f})")
        
        logger.info("Verification complete!")
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.info("Starting Qdrant data upload...")
        
        # Upload schemes
        scheme_count = upload_schemes_to_qdrant()
        
        # Verify setup
        verify_setup()
        
        logger.info(f"Successfully uploaded {scheme_count} schemes to Qdrant!")
        
    except Exception as e:
        logger.error(f"Failed to complete data upload: {e}")
        exit(1)
