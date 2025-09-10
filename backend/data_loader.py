
import os
import json
import PyPDF2
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.schema import Document
import logging

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaLegalDocumentLoader:
    """
    Simplified document loader for Bangladeshi legal documents
    Scans only raw/ and processed/ directories for PDF, TXT, and JSON files
    """

    def __init__(self):
        self.supported_extensions = ['.pdf', '.txt', '.json']
        self.documents = []

    def load_all_documents(self) -> List[Document]:
        """Load all documents from raw and processed directories"""
        all_documents = []

        # Load from raw
        raw_path = config.RAW_DATA_DIR
        if raw_path.exists():
            for file_path in raw_path.glob("**/*"):
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        docs = self._load_single_file(file_path, category="raw")
                        all_documents.extend(docs)
                        logger.info(f"Loaded {len(docs)} docs from {file_path}")
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {str(e)}")
        else:
            logger.warning(f"Raw directory not found: {raw_path}")

        # Load from processed
        processed_path = config.PROCESSED_DATA_DIR
        if processed_path.exists():
            for file_path in processed_path.glob("**/*"):
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        docs = self._load_single_file(file_path, category="processed")
                        all_documents.extend(docs)
                        logger.info(f"Loaded {len(docs)} docs from {file_path}")
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {str(e)}")
        else:
            logger.warning(f"Processed directory not found: {processed_path}")

        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def _load_single_file(self, file_path: Path, category: str) -> List[Document]:
        """Load a single file and return list of documents"""
        documents = []

        try:
            if file_path.suffix.lower() == '.pdf':
                documents = self._load_pdf(file_path, category)
            elif file_path.suffix.lower() == '.txt':
                documents = self._load_text(file_path, category)
            elif file_path.suffix.lower() == '.json':
                documents = self._load_json(file_path, category)
            else:
                logger.warning(f"Unsupported file format: {file_path}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")

        return documents

    def _load_pdf(self, file_path: Path, category: str) -> List[Document]:
        """Load PDF document"""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()

            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "category": category,
                    "file_type": "pdf",
                    "language": self._detect_language(doc.page_content)
                })

            return documents

        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            return []

    def _load_text(self, file_path: Path, category: str) -> List[Document]:
        """Load text document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            document = Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "category": category,
                    "file_type": "text",
                    "language": self._detect_language(content)
                }
            )
            return [document]

        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {str(e)}")
            return []

    def _load_json(self, file_path: Path, category: str) -> List[Document]:
        """Load structured JSON document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            documents = []

            if isinstance(data, list):
                for i, item in enumerate(data):
                    content = self._extract_content_from_json(item)
                    if content:
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": str(file_path),
                                "category": category,
                                "file_type": "json",
                                "item_index": i,
                                "language": self._detect_language(content),
                                **item.get("metadata", {})
                            }
                        )
                        documents.append(doc)
            else:
                content = self._extract_content_from_json(data)
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(file_path),
                            "category": category,
                            "file_type": "json",
                            "language": self._detect_language(content),
                            **data.get("metadata", {})
                        }
                    )
                    documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            return []

    def _extract_content_from_json(self, data: Dict) -> str:
        """Extract text content from JSON data"""
        content_fields = ["content", "text", "body", "description", "summary"]

        for field in content_fields:
            if field in data and data[field]:
                return str(data[field])

        content_parts = []
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10:
                content_parts.append(value)

        return " ".join(content_parts) if content_parts else ""

    def _detect_language(self, text: str) -> str:
        """Simple language detection for Bengali/English"""
        bengali_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        if bengali_chars > english_chars:
            return "bn"
        else:
            return "en"

    def save_processed_documents(self, documents: List[Document], filename: str = "processed_documents.json"):
        """Save processed documents to JSON file"""
        config.create_directories()
        output_path = config.PROCESSED_DATA_DIR / filename

        documents_data = []
        for doc in documents:
            documents_data.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(documents)} processed documents to {output_path}")

    def load_processed_documents(self, filename: str = "processed_documents.json") -> List[Document]:
        """Load previously processed documents from JSON file"""
        file_path = config.PROCESSED_DATA_DIR / filename

        if not file_path.exists():
            logger.warning(f"Processed documents file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            documents = []
            for item in data:
                doc = Document(
                    page_content=item["content"],
                    metadata=item["metadata"]
                )
                documents.append(doc)

            logger.info(f"Loaded {len(documents)} processed documents from {file_path}")
            return documents

        except Exception as e:
            logger.error(f"Error loading processed documents: {str(e)}")
            return []

# Create instance
document_loader = BanglaLegalDocumentLoader()

if __name__ == "__main__":
    print("🔍 Testing data_loader...")

    # Try loading all documents
    docs = document_loader.load_all_documents()
    print(f"✅ Loaded {len(docs)} documents")

    # Print first few for sanity check
    if docs:
        print("Sample document content:", docs[0].page_content[:200], "...")
        print("Sample metadata:", docs[0].metadata)

    # Save and reload processed docs
    document_loader.save_processed_documents(docs)
    reloaded_docs = document_loader.load_processed_documents()
    print(f"♻️ Reloaded {len(reloaded_docs)} documents")

