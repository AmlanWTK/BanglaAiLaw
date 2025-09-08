# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Import your retriever, RAG pipeline, or other modules
# from retriever import retrieve_answer  # example

app = FastAPI()

# Enable CORS so your Flutter frontend can talk to this API
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example root endpoint
@app.get("/")
def read_root():
    return {"message": "API is running!"}

# Example query endpoint
@app.post("/query")
def query_endpoint(payload: dict):
    user_question = payload.get("question")
    if not user_question:
        raise HTTPException(status_code=400, detail="Missing 'question' in payload")
    
    # result = retrieve_answer(user_question)  # Call your RAG/retriever logic here
    result = f"Simulated answer for: {user_question}"  # placeholder
    return {"answer": result}

# ✅ Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
