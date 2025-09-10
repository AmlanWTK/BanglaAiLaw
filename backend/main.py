
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime

from config import config
from rag_pipeline import rag_pipeline, query_constitution, query_fundamental_rights, query_government_structure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BanglaAiLaw - Legal RAG API",
    description="🏛️ AI-powered legal assistant for Bangladeshi Constitution and Laws",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class LegalQuery(BaseModel):
    question: str
    retrieval_strategy: Optional[str] = "hybrid"
    use_conversation: Optional[bool] = False
    language: Optional[str] = "auto"

class LegalResponse(BaseModel):
    answer: str
    source_documents: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ProcessDocumentsRequest(BaseModel):
    force_reprocess: Optional[bool] = False

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str

# Global state
app_state = {
    "documents_processed": False,
    "startup_time": datetime.now(),
    "total_queries": 0
}

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting BanglaAiLaw API...")

    try:
        # Validate configuration
        config.validate_config()

        # Create necessary directories
        config.create_directories()

        # Try to load existing vector store
        if rag_pipeline.process_documents():
            app_state["documents_processed"] = True
            logger.info("Documents loaded successfully")
        else:
            logger.warning("No documents loaded. Please upload documents and process them.")

        logger.info("BanglaAiLaw API started successfully!")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint with health check"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Detailed health check"""
    return HealthCheck(
        status="healthy" if app_state["documents_processed"] else "partial",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/query", response_model=LegalResponse)
async def query_legal_documents(query: LegalQuery):
    """
    Query legal documents using RAG pipeline
    """
    if not app_state["documents_processed"]:
        raise HTTPException(
            status_code=503,
            detail="Documents not processed yet. Please process documents first using /process-documents endpoint."
        )

    if not query.question or not query.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        # Process the query
        result = rag_pipeline.query(
            question=query.question,
            retrieval_strategy=query.retrieval_strategy,
            use_conversation=query.use_conversation
        )

        # Increment query counter
        app_state["total_queries"] += 1

        # Format source documents for response
        formatted_sources = []
        for doc in result.get("source_documents", []):
            formatted_sources.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown")
            })

        return LegalResponse(
            answer=result["answer"],
            source_documents=formatted_sources,
            metadata=result["metadata"]
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your query: {str(e)}"
        )

@app.post("/constitutional/query", response_model=LegalResponse)
async def query_constitutional_law(query: LegalQuery):
    """
    Query specifically about constitutional law
    """
    if not app_state["documents_processed"]:
        raise HTTPException(
            status_code=503,
            detail="Documents not processed yet."
        )

    try:
        result = query_constitution(query.question)
        app_state["total_queries"] += 1

        formatted_sources = []
        for doc in result.get("source_documents", []):
            formatted_sources.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown")
            })

        return LegalResponse(
            answer=result["answer"],
            source_documents=formatted_sources,
            metadata=result["metadata"]
        )

    except Exception as e:
        logger.error(f"Error in constitutional query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing constitutional query: {str(e)}"
        )

@app.post("/rights/query", response_model=LegalResponse)
async def query_fundamental_rights_endpoint(query: LegalQuery):
    """
    Query about fundamental rights
    """
    if not app_state["documents_processed"]:
        raise HTTPException(
            status_code=503,
            detail="Documents not processed yet."
        )

    try:
        result = query_fundamental_rights(query.question)
        app_state["total_queries"] += 1

        formatted_sources = []
        for doc in result.get("source_documents", []):
            formatted_sources.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown")
            })

        return LegalResponse(
            answer=result["answer"],
            source_documents=formatted_sources,
            metadata=result["metadata"]
        )

    except Exception as e:
        logger.error(f"Error in rights query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing rights query: {str(e)}"
        )

@app.post("/government/query", response_model=LegalResponse)
async def query_government_structure_endpoint(query: LegalQuery):
    """
    Query about government structure
    """
    if not app_state["documents_processed"]:
        raise HTTPException(
            status_code=503,
            detail="Documents not processed yet."
        )

    try:
        result = query_government_structure(query.question)
        app_state["total_queries"] += 1

        formatted_sources = []
        for doc in result.get("source_documents", []):
            formatted_sources.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown")
            })

        return LegalResponse(
            answer=result["answer"],
            source_documents=formatted_sources,
            metadata=result["metadata"]
        )

    except Exception as e:
        logger.error(f"Error in government query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing government query: {str(e)}"
        )

@app.post("/process-documents")
async def process_documents(request: ProcessDocumentsRequest, background_tasks: BackgroundTasks):
    """
    Process legal documents and create vector store
    """
    try:
        # Run document processing in background
        def process_docs():
            global app_state
            logger.info("Starting document processing...")
            success = rag_pipeline.process_documents(force_reprocess=request.force_reprocess)
            if success:
                app_state["documents_processed"] = True
                logger.info("Document processing completed successfully")
            else:
                logger.error("Document processing failed")

        background_tasks.add_task(process_docs)

        return {
            "message": "Document processing started in background",
            "status": "processing",
            "force_reprocess": request.force_reprocess
        }

    except Exception as e:
        logger.error(f"Error starting document processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting document processing: {str(e)}"
        )

@app.get("/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    try:
        history = rag_pipeline.get_conversation_history()
        return {
            "conversation_history": history,
            "total_conversations": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation history: {str(e)}"
        )

@app.delete("/conversation/history")
async def clear_conversation_history():
    """Clear conversation history"""
    try:
        rag_pipeline.clear_conversation_history()
        return {
            "message": "Conversation history cleared",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation history: {str(e)}"
        )

@app.get("/stats")
async def get_application_stats():
    """Get application statistics"""
    try:
        pipeline_stats = rag_pipeline.get_pipeline_stats()

        return {
            "app_stats": {
                "startup_time": app_state["startup_time"].isoformat(),
                "uptime_minutes": (datetime.now() - app_state["startup_time"]).total_seconds() / 60,
                "documents_processed": app_state["documents_processed"],
                "total_queries": app_state["total_queries"]
            },
            "pipeline_stats": pipeline_stats
        }

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting application stats: {str(e)}"
        )

@app.get("/config")
async def get_configuration():
    """Get current configuration (excluding sensitive data)"""
    return {
        "api_version": "1.0.0",
        "supported_languages": config.SUPPORTED_LANGUAGES,
        "default_language": config.DEFAULT_LANGUAGE,
        "retrieval_k": config.RETRIEVAL_K,
        "chunk_size": config.CHUNK_SIZE,
        "similarity_threshold": config.SIMILARITY_THRESHOLD,
        "document_categories": config.DOCUMENT_CATEGORIES,
        "has_openai_key": bool(config.OPENAI_API_KEY),
        "has_huggingface_key": bool(config.HUGGINGFACE_API_KEY)
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return HTTPException(
        status_code=500,
        detail="An internal server error occurred"
    )

if __name__ == "__main__":
    # Validate configuration before starting
    try:
        config.validate_config()
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)

    # Run the server
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level="info"
    )
