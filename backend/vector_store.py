
from typing import List, Dict, Any, Optional, Tuple
import faiss
import numpy as np
import json
import pickle
from pathlib import Path
from langchain.schema import Document
from langchain.vectorstores import FAISS
# NEW (correct import)
from langchain_community.vectorstores.utils import maximal_marginal_relevance # type: ignore

import logging

from config import config
from embeddings import embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaLegalVectorStore:
    """
    FAISS-based vector store optimized for Bangladeshi legal documents
    Supports similarity search, hybrid search, and metadata filtering
    """

    def __init__(self):
        self.faiss_index = None
        self.vector_store = None
        self.documents = []
        self.metadata_list = []
        self.embeddings_array = None

        # Paths
        self.index_path = Path(config.FAISS_INDEX_PATH)
        self.documents_path = self.index_path / "documents.pkl"
        self.metadata_path = self.index_path / "metadata.json"
        self.embeddings_path = self.index_path / "embeddings.npy"

        # Create directories
        config.create_directories()
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Load existing index if available
        self.load_index()

    def create_index(self, documents: List[Document], force_recreate: bool = False):
        """
        Create FAISS index from documents
        """
        if self.faiss_index is not None and not force_recreate:
            logger.warning("Index already exists. Use force_recreate=True to recreate.")
            return

        if not documents:
            raise ValueError("No documents provided to create index")

        logger.info(f"Creating FAISS index from {len(documents)} documents...")

        try:
            # Generate embeddings
            embeddings_list, metadata_list = embedding_service.embed_documents(documents)

            if not embeddings_list:
                raise ValueError("Failed to generate embeddings")

            # Convert to numpy array
            embeddings_array = np.array(embeddings_list).astype('float32')

            # Create FAISS index
            dimension = embeddings_array.shape[1]

            # Use IndexFlatIP for inner product (cosine similarity)
            # For better performance, you can use IndexIVFFlat or IndexHNSWFlat
            self.faiss_index = faiss.IndexFlatIP(dimension)

            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)

            # Add embeddings to index
            self.faiss_index.add(embeddings_array)

            # Store data
            self.documents = documents
            self.metadata_list = metadata_list
            self.embeddings_array = embeddings_array

            # Create LangChain FAISS wrapper
            self._create_langchain_wrapper()

            logger.info(f"Successfully created FAISS index with {self.faiss_index.ntotal} vectors")

            # Save index
            self.save_index()

        except Exception as e:
            logger.error(f"Error creating FAISS index: {str(e)}")
            raise

    def _create_langchain_wrapper(self):
        """Create LangChain FAISS wrapper for compatibility"""
        if self.faiss_index is None or not self.documents:
            return

        try:
            # Create text-embedding pairs
            texts = [doc.page_content for doc in self.documents]
            metadatas = [doc.metadata for doc in self.documents]

            # Create FAISS vectorstore
            self.vector_store = FAISS.from_texts(
                texts=texts,
                embedding=embedding_service.embeddings,
                metadatas=metadatas
            )

            logger.info("Created LangChain FAISS wrapper")

        except Exception as e:
            logger.warning(f"Could not create LangChain wrapper: {str(e)}")

    def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter_metadata: Optional[Dict] = None,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search
        """
        if self.faiss_index is None:
            raise ValueError("No index loaded. Please create or load an index first.")

        try:
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            query_vector = np.array([query_embedding]).astype('float32')

            # Normalize query vector
            faiss.normalize_L2(query_vector)

            # Search
            search_k = min(k * 3, self.faiss_index.ntotal)  # Search more than needed for filtering
            scores, indices = self.faiss_index.search(query_vector, search_k)

            # Prepare results
            results = []

            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue

                if score_threshold and score < score_threshold:
                    continue

                doc = self.documents[idx]

                # Apply metadata filtering
                if filter_metadata:
                    if not self._matches_filter(doc.metadata, filter_metadata):
                        continue

                results.append((doc, float(score)))

                if len(results) >= k:
                    break

            logger.debug(f"Similarity search found {len(results)} results for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def similarity_search_with_relevance_scores(
        self, 
        query: str, 
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search and return relevance scores
        """
        return self.similarity_search(query, k, filter_metadata)

    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """
        Perform maximum marginal relevance search to reduce redundancy
        """
        if self.faiss_index is None:
            raise ValueError("No index loaded. Please create or load an index first.")

        try:
            # Get more results than needed
            initial_results = self.similarity_search(query, fetch_k, filter_metadata)

            if not initial_results:
                return []

            # Extract embeddings and documents
            docs = [result[0] for result in initial_results]
            doc_embeddings = []

            for doc in docs:
                # Find the embedding for this document
                doc_idx = self.documents.index(doc)
                doc_embeddings.append(self.embeddings_array[doc_idx])

            # Query embedding
            query_embedding = embedding_service.embed_query(query)

            # Apply MMR
            mmr_selected = maximal_marginal_relevance(
                query_embedding,
                doc_embeddings,
                k=k,
                lambda_mult=lambda_mult
            )

            return [docs[i] for i in mmr_selected]

        except Exception as e:
            logger.error(f"Error in MMR search: {str(e)}")
            return []

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.7,  # Weight for semantic search
        filter_metadata: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Hybrid search combining semantic similarity and keyword matching
        """
        # Semantic search results
        semantic_results = self.similarity_search(query, k * 2, filter_metadata)

        # Simple keyword scoring
        keyword_results = self._keyword_search(query, k * 2, filter_metadata)

        # Combine results
        combined_scores = {}

        # Add semantic scores
        for doc, score in semantic_results:
            doc_id = id(doc)
            combined_scores[doc_id] = {
                'doc': doc,
                'semantic_score': score,
                'keyword_score': 0.0
            }

        # Add keyword scores
        for doc, score in keyword_results:
            doc_id = id(doc)
            if doc_id in combined_scores:
                combined_scores[doc_id]['keyword_score'] = score
            else:
                combined_scores[doc_id] = {
                    'doc': doc,
                    'semantic_score': 0.0,
                    'keyword_score': score
                }

        # Calculate hybrid scores
        hybrid_results = []
        for doc_data in combined_scores.values():
            hybrid_score = (
                alpha * doc_data['semantic_score'] + 
                (1 - alpha) * doc_data['keyword_score']
            )
            hybrid_results.append((doc_data['doc'], hybrid_score))

        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x[1], reverse=True)

        return hybrid_results[:k]

    def _keyword_search(
        self, 
        query: str, 
        k: int, 
        filter_metadata: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Simple keyword-based search"""
        query_words = query.lower().split()
        results = []

        for doc in self.documents:
            if filter_metadata and not self._matches_filter(doc.metadata, filter_metadata):
                continue

            content = doc.page_content.lower()

            # Simple TF scoring
            score = 0.0
            for word in query_words:
                count = content.count(word)
                if count > 0:
                    # Simple TF score
                    score += count / len(content.split())

            if score > 0:
                results.append((doc, score))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:k]

    def _matches_filter(self, metadata: Dict, filter_metadata: Dict) -> bool:
        """Check if document metadata matches filter criteria"""
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True

    def add_documents(self, documents: List[Document]):
        """Add new documents to existing index"""
        if not documents:
            return

        if self.faiss_index is None:
            # Create new index if none exists
            self.create_index(documents)
            return

        logger.info(f"Adding {len(documents)} documents to existing index...")

        try:
            # Generate embeddings for new documents
            embeddings_list, metadata_list = embedding_service.embed_documents(documents)

            if embeddings_list:
                # Convert to numpy array
                new_embeddings = np.array(embeddings_list).astype('float32')
                faiss.normalize_L2(new_embeddings)

                # Add to index
                self.faiss_index.add(new_embeddings)

                # Update stored data
                self.documents.extend(documents)
                self.metadata_list.extend(metadata_list)

                # Update embeddings array
                if self.embeddings_array is not None:
                    self.embeddings_array = np.vstack([self.embeddings_array, new_embeddings])
                else:
                    self.embeddings_array = new_embeddings

                logger.info(f"Added {len(documents)} documents. Total: {self.faiss_index.ntotal}")

                # Save updated index
                self.save_index()

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if self.faiss_index is None:
            logger.warning("No index to save")
            return

        try:
            self.index_path.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss_index_file = self.index_path / "index.faiss"
            faiss.write_index(self.faiss_index, str(faiss_index_file))

            # Save documents
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)

            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_list, f, ensure_ascii=False, indent=2, default=str)

            # Save embeddings array
            if self.embeddings_array is not None:
                np.save(self.embeddings_path, self.embeddings_array)

            logger.info(f"Saved FAISS index with {self.faiss_index.ntotal} vectors")

        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise

    def load_index(self) -> bool:
        """Load FAISS index from disk"""
        faiss_index_file = self.index_path / "index.faiss"

        if not faiss_index_file.exists():
            logger.info("No existing FAISS index found")
            return False

        try:
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(faiss_index_file))

            # Load documents
            if self.documents_path.exists():
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)

            # Load metadata
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata_list = json.load(f)

            # Load embeddings array
            if self.embeddings_path.exists():
                self.embeddings_array = np.load(self.embeddings_path)

            # Create LangChain wrapper
            self._create_langchain_wrapper()

            logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
            return True

        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if self.faiss_index is None:
            return {"status": "No index loaded"}

        stats = {
            "total_vectors": self.faiss_index.ntotal,
            "dimension": self.faiss_index.d,
            "total_documents": len(self.documents),
            "index_type": type(self.faiss_index).__name__
        }

        # Category distribution
        if self.metadata_list:
            categories = {}
            languages = {}

            for metadata in self.metadata_list:
                cat = metadata.get("category", "unknown")
                lang = metadata.get("language", "unknown")

                categories[cat] = categories.get(cat, 0) + 1
                languages[lang] = languages.get(lang, 0) + 1

            stats["category_distribution"] = categories
            stats["language_distribution"] = languages

        return stats

# Create instance
vector_store = BanglaLegalVectorStore()
