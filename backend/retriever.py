from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
import logging
import re
from datetime import datetime

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class BanglaLegalRetriever(BaseRetriever):
    """
    Advanced retriever for Bangladeshi legal documents
    Supports multiple retrieval strategies and intelligent query processing
    """
    
    # Define Pydantic fields properly
    k: int = 5
    score_threshold: float = 0.7
    
    def __init__(self, k: int = None, score_threshold: float = None, **kwargs):
        super().__init__(**kwargs)
        
        # Set attributes using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'k', k or config.RETRIEVAL_K)
        object.__setattr__(self, 'score_threshold', score_threshold or config.SIMILARITY_THRESHOLD)
        # Import vector_store here to avoid circular imports
        from vector_store import vector_store
        object.__setattr__(self, 'vector_store', vector_store)
        
        # Legal query patterns for better retrieval
        object.__setattr__(self, 'legal_patterns', {
            'article': [
                r'অনুচ্ছেদ\s*([০-৯]+)',     # Bengali article
                r'article\s*(\d+)',        # English article
            ],
            'section': [
                r'ধারা\s*([০-৯]+)',         # Bengali section
                r'section\s*(\d+)',        # English section
            ],
            'chapter': [
                r'অধ্যায়\s*([০-৯]+)',      # Bengali chapter
                r'chapter\s*(\d+)',        # English chapter
            ],
            'amendment': [
                r'সংশোধনী\s*([০-৯]+)',     # Bengali amendment
                r'amendment\s*(\d+)',      # English amendment
            ]
        })
        
        # Legal entity recognition
        object.__setattr__(self, 'legal_entities', {
            'rights': [
                'মৌলিক অধিকার', 'fundamental rights', 'basic rights',
                'human rights', 'constitutional rights'
            ],
            'government': [
                'সরকার', 'government', 'প্রশাসন', 'administration',
                'রাষ্ট্রপতি', 'president', 'প্রধানমন্ত্রী', 'prime minister'
            ],
            'parliament': [
                'সংসদ', 'parliament', 'জাতীয় সংসদ', 'national parliament',
                'আইনসভা', 'legislature'
            ],
            'judiciary': [
                'বিচার বিভাগ', 'judiciary', 'আদালত', 'court',
                'বিচারক', 'judge', 'সুপ্রিম কোর্ট', 'supreme court'
            ]
        })
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Get documents relevant to the query"""
        return self.retrieve_documents(query)
    
    def retrieve_documents(
        self, 
        query: str,
        retrieval_strategy: str = "hybrid",
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """
        Retrieve documents using specified strategy
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        logger.info(f"Retrieving documents for query: {query[:100]}...")
        
        # Preprocess query
        processed_query = self.preprocess_query(query)
        
        # Apply query enhancement
        enhanced_query = self.enhance_query(processed_query)
        
        # Auto-detect document type filters
        auto_filters = self.auto_detect_filters(query)
        if auto_filters:
            filter_metadata = {**(filter_metadata or {}), **auto_filters}
        
        try:
            if retrieval_strategy == "semantic":
                results = self._semantic_retrieval(enhanced_query, filter_metadata)
            elif retrieval_strategy == "keyword":
                results = self._keyword_retrieval(enhanced_query, filter_metadata)
            elif retrieval_strategy == "hybrid":
                results = self._hybrid_retrieval(enhanced_query, filter_metadata)
            elif retrieval_strategy == "mmr":
                results = self._mmr_retrieval(enhanced_query, filter_metadata)
            else:
                logger.warning(f"Unknown strategy {retrieval_strategy}, using hybrid")
                results = self._hybrid_retrieval(enhanced_query, filter_metadata)
            
            # Post-process results
            processed_results = self.post_process_results(results, query)
            
            logger.info(f"Retrieved {len(processed_results)} documents")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in document retrieval: {str(e)}")
            return []
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess query for better retrieval"""
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Expand common abbreviations
        abbreviations = {
            'বাংলাদেশ': 'গণপ্রজাতন্ত্রী বাংলাদেশ',
            'সংবিধান': 'বাংলাদেশের সংবিধান',
            'PM': 'Prime Minister',
            'MP': 'Member of Parliament',
        }
        
        for abbrev, full in abbreviations.items():
            query = query.replace(abbrev, full)
        
        return query
    
    def enhance_query(self, query: str) -> str:
        """Enhance query with related legal terms"""
        enhanced_terms = []
        query_lower = query.lower()
        
        # Add related legal terms based on query content
        for category, terms in self.legal_entities.items():
            for term in terms:
                if term.lower() in query_lower:
                    # Add other related terms from the same category
                    for related_term in terms:
                        if related_term.lower() != term.lower():
                            enhanced_terms.append(related_term)
                    break
        
        if enhanced_terms:
            # Add most relevant enhanced terms (limit to avoid query bloat)
            query += " " + " ".join(enhanced_terms[:3])
        
        return query
    
    def auto_detect_filters(self, query: str) -> Dict[str, Any]:
        """Auto-detect filters based on query content"""
        filters = {}
        
        # Detect specific legal document types
        if any(word in query.lower() for word in ['constitution', 'সংবিধান']):
            filters['category'] = 'constitution'
        elif any(word in query.lower() for word in ['act', 'আইন']):
            filters['category'] = 'legal_acts'
        elif any(word in query.lower() for word in ['ordinance', 'অধ্যাদেশ']):
            filters['category'] = 'ordinances'
        elif any(word in query.lower() for word in ['judgment', 'রায়']):
            filters['category'] = 'court_judgments'
        
        # Detect language preference
        bengali_chars = sum(1 for c in query if '\u0980' <= c <= '\u09FF')
        english_chars = sum(1 for c in query if c.isascii() and c.isalpha())
        
        if bengali_chars > english_chars * 2:
            filters['language'] = 'bn'
        elif english_chars > bengali_chars * 2:
            filters['language'] = 'en'
        
        return filters
    
    def _semantic_retrieval(
        self, 
        query: str, 
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Pure semantic similarity retrieval"""
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=self.k,
                filter_metadata=filter_metadata,
                score_threshold=self.score_threshold
            )
            
            # Extract documents from results
            return [doc for doc, score in results]
            
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {str(e)}")
            return []
    
    def _keyword_retrieval(
        self, 
        query: str, 
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Keyword-based retrieval"""
        try:
            # Use vector store's keyword search
            results = self.vector_store._keyword_search(
                query=query,
                k=self.k,
                filter_metadata=filter_metadata
            )
            
            return [doc for doc, score in results]
            
        except Exception as e:
            logger.error(f"Error in keyword retrieval: {str(e)}")
            return []
    
    def _hybrid_retrieval(
        self, 
        query: str, 
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Hybrid semantic + keyword retrieval"""
        try:
            results = self.vector_store.hybrid_search(
                query=query,
                k=self.k,
                alpha=0.7,  # 70% semantic, 30% keyword
                filter_metadata=filter_metadata
            )
            
            return [doc for doc, score in results]
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {str(e)}")
            return []
    
    def _mmr_retrieval(
        self, 
        query: str, 
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Maximum Marginal Relevance retrieval for diversity"""
        try:
            results = self.vector_store.max_marginal_relevance_search(
                query=query,
                k=self.k,
                fetch_k=self.k * 3,
                lambda_mult=0.7,  # Balance relevance vs diversity
                filter_metadata=filter_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in MMR retrieval: {str(e)}")
            return []
    
    def post_process_results(
        self, 
        documents: List[Document], 
        original_query: str
    ) -> List[Document]:
        """Post-process retrieval results"""
        if not documents:
            return documents
        
        # Remove very short or very long documents that might not be useful
        filtered_docs = []
        
        for doc in documents:
            content_length = len(doc.page_content)
            
            # Skip very short or very long content
            if content_length < 50 or content_length > 10000:
                continue
            
            # Enhance document metadata
            doc.metadata['retrieval_timestamp'] = datetime.now().isoformat()
            doc.metadata['original_query'] = original_query
            doc.metadata['relevance_score'] = self._calculate_relevance_score(doc, original_query)
            
            filtered_docs.append(doc)
        
        # Sort by relevance score if available
        try:
            filtered_docs.sort(
                key=lambda x: x.metadata.get('relevance_score', 0), 
                reverse=True
            )
        except:
            pass
        
        return filtered_docs
    
    def _calculate_relevance_score(self, document: Document, query: str) -> float:
        """Calculate a simple relevance score for ranking"""
        try:
            content = document.page_content.lower()
            query_terms = query.lower().split()
            
            score = 0.0
            
            # Term frequency scoring
            for term in query_terms:
                if term in content:
                    # Simple TF score
                    tf = content.count(term) / len(content.split())
                    score += tf
            
            # Boost score for specific legal document types
            category = document.metadata.get('category', '')
            if category == 'constitution':
                score *= 1.2
            elif category == 'legal_acts':
                score *= 1.1
            
            # Boost score for exact matches of legal patterns
            for pattern_type, patterns in self.legal_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, query, re.IGNORECASE):
                        if re.search(pattern, content, re.IGNORECASE):
                            score *= 1.3
                            break
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
            return 0.0
    
    def get_retriever_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            "retriever_type": "BanglaLegalRetriever",
            "default_k": self.k,
            "score_threshold": self.score_threshold,
            "vector_store_stats": self.vector_store.get_index_stats()
        }

# Create instance WITHOUT vector_store parameter
legal_retriever = BanglaLegalRetriever()
