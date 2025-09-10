from data_loader import document_loader
from text_splitter import text_splitter

# Load processed documents
documents = document_loader.load_processed_documents()

# Split into chunks
chunks = text_splitter.split_documents(documents)

# Print some stats
stats = text_splitter.get_chunk_statistics(chunks)
print("Total chunks:", stats["total_chunks"])
print("Average chunk length:", stats["average_chunk_length"])
print("Language distribution:", stats["language_distribution"])
print("Sample chunk content:", chunks[0].page_content[:500])
