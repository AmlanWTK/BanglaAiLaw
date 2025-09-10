from retriever import legal_retriever, retrieve_constitutional_articles, retrieve_fundamental_rights, retrieve_government_structure
from langchain.schema import Document

def print_results(results):
    if not results:
        print("No documents retrieved.")
        return

    for i, doc in enumerate(results, 1):
        print(f"\n--- Document {i} ---")
        print(f"Title / Metadata: {doc.metadata.get('source', 'N/A')}")
        print(f"Category: {doc.metadata.get('category', 'N/A')}")
        print(f"Language: {doc.metadata.get('language', 'N/A')}")
        print(f"Relevance Score: {doc.metadata.get('relevance_score', 'N/A')}")
        print(f"Content (first 300 chars):\n{doc.page_content[:300]}...\n")

if __name__ == "__main__":
    # Test 1: Hybrid retrieval example
    print("=== Hybrid Retrieval Test ===")
    hybrid_results = legal_retriever.retrieve_documents(
        query="মৌলিক অধিকার fundamental rights",
        retrieval_strategy="hybrid"
    )
    print_results(hybrid_results[:5])

    # Test 2: Semantic retrieval example
    print("=== Semantic Retrieval Test ===")
    semantic_results = legal_retriever.retrieve_documents(
        query="সরকার কাঠামো রাষ্ট্রপতি প্রধানমন্ত্রী সংসদ",
        retrieval_strategy="semantic"
    )
    print_results(semantic_results[:5])

    # Test 3: Keyword retrieval example
    print("=== Keyword Retrieval Test ===")
    keyword_results = legal_retriever.retrieve_documents(
        query="সংবিধান অনুচ্ছেদ 15 Article 15",
        retrieval_strategy="keyword"
    )
    print_results(keyword_results[:5])

    # Test 4: Retrieve specific constitutional article
    print("=== Retrieve Constitutional Article 15 ===")
    article_results = retrieve_constitutional_articles(article_number="15")
    print_results(article_results[:5])

    # Test 5: Retrieve fundamental rights
    print("=== Retrieve Fundamental Rights ===")
    rights_results = retrieve_fundamental_rights()
    print_results(rights_results[:5])
