from langchain.schema import Document
import json
from pathlib import Path
from vector_store import vector_store

# Load processed documents
processed_docs_path = Path("D:/Law-RAG/data/processed/processed_documents.json")
with open(processed_docs_path, "r", encoding="utf-8") as f:
    data = json.load(f)

documents = []
for item in data:
    # Use 'content' key instead of 'page_content'
    documents.append(Document(page_content=item['content'], metadata=item.get('metadata', {})))

print(f"Loaded {len(documents)} documents")

# Create FAISS index
vector_store.create_index(documents)

# Check index stats
stats = vector_store.get_index_stats()
print(stats)
