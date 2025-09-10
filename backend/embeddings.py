
from typing import List, Optional, Dict, Any
import openai
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import pickle
import json
from pathlib import Path
import logging

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaLegalEmbeddings:
    """
    Embedding service for Bangladeshi legal documents
    Supports both OpenAI and HuggingFace embeddings with Bengali language optimization
    """

    def __init__(self, embedding_type: str = "auto"):
        self.embedding_type = embedding_type
        self.embeddings = None
        self.dimension = None

        # Initialize embedding model
        self._initialize_embeddings()

        # Cache for embeddings
        self.cache_path = config.EMBEDDINGS_DIR / "embeddings_cache.pkl"
        self.metadata_cache_path = config.EMBEDDINGS_DIR / "metadata_cache.json"
        self.embedding_cache = {}
        self.metadata_cache = {}

        # Load existing cache
        self._load_cache()

    def _initialize_embeddings(self):
        """Initialize the embedding model based on configuration"""
        config.create_directories()

        if self.embedding_type == "auto":
            # Auto-select based on available API keys
            if config.OPENAI_API_KEY:
                self.embedding_type = "openai"
            else:
                self.embedding_type = "huggingface"

        try:
            if self.embedding_type == "openai":
                self._initialize_openai()
            elif self.embedding_type == "huggingface":
                self._initialize_huggingface()
            else:
                raise ValueError(f"Unsupported embedding type: {self.embedding_type}")

        except Exception as e:
            logger.error(f"Failed to initialize {self.embedding_type} embeddings: {str(e)}")
            # Fallback to HuggingFace
            if self.embedding_type != "huggingface":
                logger.info("Falling back to HuggingFace embeddings")
                self.embedding_type = "huggingface"
                self._initialize_huggingface()

    def _initialize_openai(self):
        """Initialize OpenAI embeddings"""
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        openai.api_key = config.OPENAI_API_KEY
        self.embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY
        )

        # OpenAI text-embedding-ada-002 has 1536 dimensions
        self.dimension = 1536
        logger.info(f"Initialized OpenAI embeddings with model: {config.EMBEDDING_MODEL}")

    def _initialize_huggingface(self):
        """Initialize HuggingFace embeddings"""
        # Use a multilingual model that works well with Bengali
        model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},  # Change to 'cuda' if GPU available
                encode_kwargs={'normalize_embeddings': True}
            )

            # This model has 768 dimensions
            self.dimension = 768
            logger.info(f"Initialized HuggingFace embeddings with model: {model_name}")

        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {str(e)}")
            # Fallback to a simpler model
            fallback_model = "all-MiniLM-L6-v2"
            self.embeddings = HuggingFaceEmbeddings(
                model_name=f"sentence-transformers/{fallback_model}",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            self.dimension = 384
            logger.info(f"Initialized fallback HuggingFace model: {fallback_model}")

    def embed_documents(self, documents: List[Document]) -> tuple[List[np.ndarray], List[Dict]]:
        """
        Embed a list of documents and return embeddings with metadata
        """
        if not documents:
            logger.warning("No documents provided for embedding")
            return [], []

        embeddings_list = []
        metadata_list = []

        logger.info(f"Embedding {len(documents)} documents...")

        for i, doc in enumerate(documents):
            try:
                # Check cache first
                cache_key = self._get_cache_key(doc.page_content)

                if cache_key in self.embedding_cache:
                    embedding = self.embedding_cache[cache_key]
                    logger.debug(f"Using cached embedding for document {i}")
                else:
                    # Generate new embedding
                    embedding = self._embed_single_text(doc.page_content)

                    # Cache the embedding
                    self.embedding_cache[cache_key] = embedding

                embeddings_list.append(embedding)

                # Prepare metadata
                metadata = doc.metadata.copy()
                metadata.update({
                    "embedding_model": self.embedding_type,
                    "embedding_dimension": self.dimension,
                    "text_length": len(doc.page_content)
                })
                metadata_list.append(metadata)

                if (i + 1) % 10 == 0:
                    logger.info(f"Embedded {i + 1}/{len(documents)} documents")

            except Exception as e:
                logger.error(f"Error embedding document {i}: {str(e)}")
                continue

        # Save cache
        self._save_cache()

        logger.info(f"Successfully embedded {len(embeddings_list)} documents")
        return embeddings_list, metadata_list

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query text"""
        try:
            # Check cache
            cache_key = self._get_cache_key(query)

            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]

            # Generate new embedding
            embedding = self._embed_single_text(query)

            # Cache the embedding
            self.embedding_cache[cache_key] = embedding
            self._save_cache()

            return embedding

        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise

    def _embed_single_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        if not text or not text.strip():
            raise ValueError("Empty text provided for embedding")

        try:
            if self.embedding_type == "openai":
                # OpenAI embeddings
                embedding = self.embeddings.embed_query(text)
            else:
                # HuggingFace embeddings
                embedding = self.embeddings.embed_query(text)

            return np.array(embedding)

        except Exception as e:
            logger.error(f"Error in {self.embedding_type} embedding: {str(e)}")
            raise

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _load_cache(self):
        """Load embedding cache from disk"""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")

            if self.metadata_cache_path.exists():
                with open(self.metadata_cache_path, 'r', encoding='utf-8') as f:
                    self.metadata_cache = json.load(f)

        except Exception as e:
            logger.warning(f"Could not load embedding cache: {str(e)}")
            self.embedding_cache = {}
            self.metadata_cache = {}

    def _save_cache(self):
        """Save embedding cache to disk"""
        try:
            config.create_directories()

            with open(self.cache_path, 'wb') as f:
                pickle.dump(self.embedding_cache, f)

            with open(self.metadata_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_cache, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self.embedding_cache)} embeddings to cache")

        except Exception as e:
            logger.warning(f"Could not save embedding cache: {str(e)}")

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service"""
        return {
            "embedding_type": self.embedding_type,
            "dimension": self.dimension,
            "cached_embeddings": len(self.embedding_cache),
            "cache_size_mb": self.cache_path.stat().st_size / (1024 * 1024) if self.cache_path.exists() else 0
        }

    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache = {}
        self.metadata_cache = {}

        if self.cache_path.exists():
            self.cache_path.unlink()
        if self.metadata_cache_path.exists():
            self.metadata_cache_path.unlink()

        logger.info("Embedding cache cleared")

# Create instance
embedding_service = BanglaLegalEmbeddings()
