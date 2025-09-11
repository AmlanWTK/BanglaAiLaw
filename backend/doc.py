# In Python shell/from a script
from data_loader import document_loader
docs = document_loader.load_all_documents()
print(f"Loaded {len(docs)} documents")
