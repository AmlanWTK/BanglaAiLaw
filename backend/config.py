import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_RELOAD = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # HuggingFace Configuration (alternative to OpenAI)
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./law_rag.db")
    
    # Vector Store Configuration
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    
    # Data Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    EMBEDDINGS_DIR = DATA_DIR / "embeddings"
    
    # Document Processing Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    
    # RAG Configuration
    RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", 5))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.7))
    
    # Language Configuration
    SUPPORTED_LANGUAGES = ["bn", "en"]  # Bengali and English
    DEFAULT_LANGUAGE = "bn"
    
    # Legal Document Categories
    DOCUMENT_CATEGORIES = [
        "constitution",
        "acts",
        "ordinances",
        "regulations",
        "court_judgments",
        "amendments"
    ]
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.EMBEDDINGS_DIR,
            cls.VECTOR_STORE_PATH
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration"""
        required_vars = []
        
        if not cls.OPENAI_API_KEY and not cls.HUGGINGFACE_API_KEY:
            required_vars.append("Either OPENAI_API_KEY or HUGGINGFACE_API_KEY")
        
        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
        
        return True

# Create singleton instance
config = Config()

if __name__ == "__main__":
    print("✅ Config directories being created...")
    config.create_directories()
    print("BASE_DIR:", config.BASE_DIR)
    print("RAW_DATA_DIR:", config.RAW_DATA_DIR)
    print("PROCESSED_DATA_DIR:", config.PROCESSED_DATA_DIR)
    print("EMBEDDINGS_DIR:", config.EMBEDDINGS_DIR)
    print("VECTOR_STORE_PATH:", config.VECTOR_STORE_PATH)
    print("OPENAI_API_KEY loaded:", "Yes" if config.OPENAI_API_KEY else "No")
