from retriever import legal_retriever

question = "What are the fundamental rights in Bangladesh?"
docs = legal_retriever.retrieve_documents(question)
print(f"Retrieved {len(docs)} documents")
for doc in docs[:3]:
    print(doc.page_content[:300])
