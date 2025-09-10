
from typing import List, Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.schema import Document
import re
import logging

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanglaLegalTextSplitter:
    """
    Specialized text splitter for Bangladeshi legal documents
    Handles both Bengali and English text with legal document awareness
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

        # Bengali-specific separators
        self.bengali_separators = [
            "\n\n",           # Double newlines (paragraph breaks)
            "\n",             # Single newlines
            "।",               # Bengali full stop (dari)
            "?",               # Question mark
            "!",               # Exclamation mark
            ";",               # Semicolon
            ":",               # Colon
            ",",               # Comma
            " ",               # Space
            ""                 # Last resort
        ]

        # Legal document specific separators
        self.legal_separators = [
            "\n\nঅধ্যায়",      # Chapter (Bengali)
            "\n\nChapter",      # Chapter (English)
            "\n\nঅনুচ্ছেদ",     # Article (Bengali)
            "\n\nArticle",      # Article (English)
            "\n\nধারা",         # Section (Bengali)
            "\n\nSection",      # Section (English)
            "\n\n(",           # Subsection markers
            "\n\n[",           # Bracket markers
            "\n\n১।",          # Bengali numbering
            "\n\n1.",          # English numbering
        ] + self.bengali_separators

        # Initialize splitters
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            separators=self.legal_separators,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            keep_separator=True
        )

        self.character_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks with metadata preservation"""
        all_chunks = []

        for doc in documents:
            try:
                # Preprocess the document text
                processed_text = self.preprocess_text(doc.page_content)
                doc.page_content = processed_text

                # Split based on document type and language
                chunks = self._split_single_document(doc)

                # Add chunk metadata
                for i, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        "chunk_id": f"{doc.metadata.get('source', 'unknown')}_{i}",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "original_length": len(doc.page_content),
                        "chunk_length": len(chunk.page_content)
                    })

                all_chunks.extend(chunks)

            except Exception as e:
                logger.error(f"Error splitting document {doc.metadata.get('source', 'unknown')}: {str(e)}")

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

    def _split_single_document(self, document: Document) -> List[Document]:
        """Split a single document based on its characteristics"""
        category = document.metadata.get("category", "")
        language = document.metadata.get("language", "en")

        # Use legal-aware splitting for constitution and acts
        if category in ["constitution", "legal_acts", "ordinances", "regulations"]:
            return self._split_legal_document(document)

        # Use language-aware splitting for other documents
        elif language == "bn":
            return self._split_bengali_document(document)
        else:
            return self._split_english_document(document)

    def _split_legal_document(self, document: Document) -> List[Document]:
        """Split legal documents with structure awareness"""
        # Try to identify and preserve legal structure
        text = document.page_content

        # Check if the document has clear legal structure
        if self._has_legal_structure(text):
            # Use recursive splitter with legal separators
            chunks = self.recursive_splitter.split_documents([document])
        else:
            # Fall back to regular text splitting
            chunks = self._split_by_language(document)

        return chunks

    def _split_bengali_document(self, document: Document) -> List[Document]:
        """Split Bengali documents with language-specific handling"""
        # Use Bengali-aware recursive splitter
        bengali_splitter = RecursiveCharacterTextSplitter(
            separators=self.bengali_separators,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            keep_separator=True
        )

        return bengali_splitter.split_documents([document])

    def _split_english_document(self, document: Document) -> List[Document]:
        """Split English documents"""
        # Use standard recursive splitter for English
        return self.recursive_splitter.split_documents([document])

    def _split_by_language(self, document: Document) -> List[Document]:
        """Split document based on detected language"""
        language = document.metadata.get("language", "en")

        if language == "bn":
            return self._split_bengali_document(document)
        else:
            return self._split_english_document(document)

    def _has_legal_structure(self, text: str) -> bool:
        """Check if text has recognizable legal document structure"""
        legal_markers = [
            r"অধ্যায়\s*[০-৯]+",     # Bengali chapter
            r"Chapter\s*\d+",       # English chapter
            r"অনুচ্ছেদ\s*[০-৯]+",    # Bengali article
            r"Article\s*\d+",       # English article
            r"ধারা\s*[০-৯]+",        # Bengali section
            r"Section\s*\d+",       # English section
            r"\([০-৯]+\)",         # Bengali numbered subsections
            r"\(\d+\)",           # English numbered subsections
        ]

        for pattern in legal_markers:
            if re.search(pattern, text):
                return True

        return False

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better splitting"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Standardize legal numbering
        text = self._standardize_legal_numbering(text)

        # Clean up common OCR errors in Bengali text
        text = self._clean_bengali_ocr_errors(text)

        return text.strip()

    def _standardize_legal_numbering(self, text: str) -> str:
        """Standardize legal document numbering format"""
        # Ensure proper spacing around legal markers
        patterns = [
            (r'(অধ্যায়)([০-৯]+)', r'\1 \2'),
            (r'(Chapter)(\d+)', r'\1 \2'),
            (r'(অনুচ্ছেদ)([০-৯]+)', r'\1 \2'),
            (r'(Article)(\d+)', r'\1 \2'),
            (r'(ধারা)([০-৯]+)', r'\1 \2'),
            (r'(Section)(\d+)', r'\1 \2'),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def _clean_bengali_ocr_errors(self, text: str) -> str:
        """Clean common OCR errors in Bengali text"""
        # Common OCR corrections for Bengali text
        corrections = {
            'ে ্র': 'ের',  # Common conjunct errors
            'া ্র': 'ার',
            'ি ্র': 'ির',
            'ু ্র': 'ুর',
        }

        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)

        return text

    def get_chunk_statistics(self, chunks: List[Document]) -> Dict[str, Any]:
        """Get statistics about the chunks"""
        if not chunks:
            return {}

        chunk_lengths = [len(chunk.page_content) for chunk in chunks]

        stats = {
            "total_chunks": len(chunks),
            "average_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "total_characters": sum(chunk_lengths),
        }

        # Language distribution
        languages = {}
        categories = {}

        for chunk in chunks:
            lang = chunk.metadata.get("language", "unknown")
            cat = chunk.metadata.get("category", "unknown")

            languages[lang] = languages.get(lang, 0) + 1
            categories[cat] = categories.get(cat, 0) + 1

        stats["language_distribution"] = languages
        stats["category_distribution"] = categories

        return stats

# Create instance
text_splitter = BanglaLegalTextSplitter()
