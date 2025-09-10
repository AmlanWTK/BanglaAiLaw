
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.callbacks.manager import get_openai_callback
import logging
import json
from datetime import datetime

from config import config
from data_loader import document_loader
from text_splitter import text_splitter
from embeddings import embedding_service
from vector_store import vector_store
from retriever import legal_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaLegalRAGPipeline:
    """
    Complete RAG pipeline for Bangladeshi legal documents
    Handles document processing, retrieval, and response generation
    """

    def __init__(self):
        self.llm = None
        self.memory = None
        self.qa_chain = None
        self.conversation_chain = None

        # Initialize LLM
        self._initialize_llm()

        # Initialize memory for conversations
        self._initialize_memory()

        # Initialize chains
        self._initialize_chains()

        # Conversation history
        self.conversation_history = []

        # Legal response templates
        self.response_templates = self._load_response_templates()

    def _initialize_llm(self):
        """Initialize the language model"""
        try:
            if config.OPENAI_API_KEY:
                self.llm = ChatOpenAI(
                    model_name=config.OPENAI_MODEL,
                    temperature=0.3,  # Low temperature for factual legal responses
                    openai_api_key=config.OPENAI_API_KEY
                )
                logger.info(f"Initialized OpenAI LLM: {config.OPENAI_MODEL}")
            else:
                # Fallback to HuggingFace (would need additional setup)
                logger.warning("No OpenAI API key found. Please configure OpenAI for best results.")
                raise ValueError("OpenAI API key required")

        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise

    def _initialize_memory(self):
        """Initialize conversation memory"""
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Keep last 5 exchanges
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

    def _initialize_chains(self):
        """Initialize LangChain chains"""
        try:
            # QA Chain for single questions
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=legal_retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": self._get_qa_prompt()
                }
            )

            # Conversational Chain for multi-turn conversations
            self.conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=legal_retriever,
                memory=self.memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={
                    "prompt": self._get_conversation_prompt()
                }
            )

            logger.info("Initialized RAG chains successfully")

        except Exception as e:
            logger.error(f"Error initializing chains: {str(e)}")
            raise

    def _get_qa_prompt(self) -> PromptTemplate:
        """Get prompt template for QA chain"""
        template = """আপনি একজন বিশেষজ্ঞ আইনি সহায়ক যিনি বাংলাদেশের সংবিধান ও আইন সম্পর্কে প্রশ্নের উত্তর দেন।
You are an expert legal assistant specializing in Bangladesh Constitution and laws.

নিম্নলিখিত প্রসঙ্গ ব্যবহার করে প্রশ্নের উত্তর দিন:
Use the following context to answer the question:

Context:
{context}

প্রশ্ন / Question: {question}

নির্দেশনা / Instructions:
1. শুধুমাত্র প্রদত্ত প্রসঙ্গের উপর ভিত্তি করে উত্তর দিন
2. উত্তর সঠিক, স্পষ্ট ও সংক্ষিপ্ত হওয়া উচিত
3. প্রয়োজনে বাংলা ও ইংরেজি উভয় ভাষায় উত্তর দিন
4. যদি প্রসঙ্গে উত্তর না থাকে, তাহলে সেটি স্বীকার করুন
5. আইনি উৎস উল্লেখ করুন যেখানে প্রাসঙ্গিক

Answer only based on the provided context. Be accurate, clear, and concise.
Provide bilingual responses in Bengali and English when appropriate.
If the answer is not in the context, acknowledge that.
Cite relevant legal sources when applicable.

উত্তর / Answer:"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

    def _get_conversation_prompt(self) -> ChatPromptTemplate:
        """Get prompt template for conversational chain"""
        system_message = """আপনি বাংলাদেশের সংবিধান ও আইনের উপর একজন বিশেষজ্ঞ সহায়ক।
You are an expert assistant on Bangladesh Constitution and laws.

আপনার দায়িত্ব:
Your responsibilities:
1. বাংলাদেশের সংবিধান ও আইন সম্পর্কে সঠিক তথ্য প্রদান
2. আইনি প্রশ্নের স্পষ্ট ও বোধগম্য উত্তর
3. প্রাসঙ্গিক আইনি ধারা ও অনুচ্ছেদের রেফারেন্স
4. বাংলা ও ইংরেজি উভয় ভাষায় সাহায্য

Always:
- Base answers on provided legal documents
- Be precise and factual
- Cite relevant constitutional articles and legal sections
- Acknowledge when information is not available
- Maintain professional legal tone"""

        human_message = """Previous conversation:
{chat_history}

Legal context:
{context}

Current question: {question}
Please provide a comprehensive answer based on the legal context and conversation history."""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for different legal topics"""
        return {
            "constitution": "এই প্রশ্নটি বাংলাদেশের সংবিধান সম্পর্কিত। This question relates to the Constitution of Bangladesh.",
            "rights": "মৌলিক অধিকার সম্পর্কিত প্রশ্ন। This is about fundamental rights.",
            "government": "সরকারি কাঠামো সম্পর্কিত। This relates to government structure.",
            "not_found": "দুঃখিত, প্রদত্ত তথ্যে এই প্রশ্নের উত্তর পাওয়া যায়নি। Sorry, the answer is not found in the available documents.",
            "clarification": "আরও স্পষ্ট তথ্যের জন্য অনুগ্রহ করে প্রশ্নটি আরও বিস্তারিতভাবে করুন। Please ask your question more specifically for clearer information."
        }

    def process_documents(self, force_reprocess: bool = False) -> bool:
        """
        Process legal documents and create vector store
        """
        logger.info("Starting document processing pipeline...")

        try:
            # Check if vector store already exists
            if vector_store.faiss_index is not None and not force_reprocess:
                logger.info("Vector store already exists. Use force_reprocess=True to recreate.")
                return True

            # Step 1: Load documents
            logger.info("Loading legal documents...")
            documents = document_loader.load_all_documents()

            if not documents:
                logger.error("No documents loaded. Please check your data directory.")
                return False

            logger.info(f"Loaded {len(documents)} documents")

            # Step 2: Split documents into chunks
            logger.info("Splitting documents into chunks...")
            chunks = text_splitter.split_documents(documents)

            if not chunks:
                logger.error("No chunks created from documents.")
                return False

            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Create vector store
            logger.info("Creating vector store with embeddings...")
            vector_store.create_index(chunks, force_recreate=force_reprocess)

            logger.info("Document processing completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Error in document processing: {str(e)}")
            return False

    def query(
        self, 
        question: str, 
        retrieval_strategy: str = "hybrid",
        use_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        Process a legal query and return response
        """
        if not question or not question.strip():
            return {
                "answer": "অনুগ্রহ করে একটি প্রশ্ন করুন। Please ask a question.",
                "source_documents": [],
                "metadata": {"error": "Empty question"}
            }

        logger.info(f"Processing query: {question[:100]}...")

        try:
            with get_openai_callback() as cb:
                if use_conversation and self.conversation_chain:
                    # Use conversational chain
                    result = self.conversation_chain({
                        "question": question
                    })
                else:
                    # Use QA chain
                    result = self.qa_chain({
                        "query": question
                    })

                # Prepare response
                response = {
                    "answer": result.get("answer", ""),
                    "source_documents": result.get("source_documents", []),
                    "metadata": {
                        "tokens_used": cb.total_tokens,
                        "cost": cb.total_cost,
                        "retrieval_strategy": retrieval_strategy,
                        "timestamp": datetime.now().isoformat(),
                        "language": self._detect_language(question)
                    }
                }

                # Add to conversation history
                self.conversation_history.append({
                    "question": question,
                    "answer": response["answer"],
                    "timestamp": datetime.now().isoformat(),
                    "sources_count": len(response["source_documents"])
                })

                # Keep only last 10 conversations
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]

                logger.info(f"Query processed successfully. Used {cb.total_tokens} tokens.")
                return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"দুঃখিত, প্রশ্ন প্রক্রিয়াকরণে সমস্যা হয়েছে। Sorry, there was an error processing your question: {str(e)}",
                "source_documents": [],
                "metadata": {"error": str(e)}
            }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history.copy()

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.memory.clear()
        logger.info("Conversation history cleared")

    def _detect_language(self, text: str) -> str:
        """Detect language of the text"""
        bengali_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        if bengali_chars > english_chars:
            return "bn"
        else:
            return "en"

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        stats = {
            "llm_model": config.OPENAI_MODEL if config.OPENAI_API_KEY else "None",
            "total_conversations": len(self.conversation_history),
            "memory_size": len(self.memory.chat_memory.messages) if self.memory else 0,
            "vector_store_stats": vector_store.get_index_stats(),
            "embedding_stats": embedding_service.get_embedding_stats()
        }

        return stats

    def export_conversation_history(self, filename: str = None) -> str:
        """Export conversation history to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_history_{timestamp}.json"

        filepath = config.DATA_DIR / "exports" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_conversations": len(self.conversation_history),
            "conversations": self.conversation_history
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Conversation history exported to {filepath}")
        return str(filepath)

# Convenience functions for specific legal queries
def query_constitution(question: str) -> Dict[str, Any]:
    """Query specifically about the constitution"""
    pipeline = BanglaLegalRAGPipeline()

    # Enhance question with constitutional context
    enhanced_question = f"বাংলাদেশের সংবিধান সম্পর্কে: {question}"

    return pipeline.query(
        enhanced_question,
        retrieval_strategy="semantic"
    )

def query_fundamental_rights(question: str) -> Dict[str, Any]:
    """Query about fundamental rights"""
    pipeline = BanglaLegalRAGPipeline()

    enhanced_question = f"মৌলিক অধিকার সম্পর্কে: {question}"

    return pipeline.query(
        enhanced_question,
        retrieval_strategy="hybrid"
    )

def query_government_structure(question: str) -> Dict[str, Any]:
    """Query about government structure"""
    pipeline = BanglaLegalRAGPipeline()

    enhanced_question = f"সরকার কাঠামো সম্পর্কে: {question}"

    return pipeline.query(
        enhanced_question,
        retrieval_strategy="hybrid"
    )

# Create global pipeline instance
rag_pipeline = BanglaLegalRAGPipeline()
