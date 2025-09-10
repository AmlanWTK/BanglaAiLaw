from data_loader import document_loader
from text_splitter import text_splitter
from embeddings import embedding_service

# Load processed documents
documents = document_loader.load_processed_documents()
print(f"Loaded {len(documents)} documents")

# Split into chunks
chunks = text_splitter.split_documents(documents)
print(f"Total chunks: {len(chunks)}")

# Embed first 5 chunks for testing
embeddings, metadata = embedding_service.embed_documents(chunks[:5])
print(f"Generated {len(embeddings)} embeddings")
print("Sample embedding dimension:", embeddings[0].shape)
print("Sample metadata:", metadata[0])
