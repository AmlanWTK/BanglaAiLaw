import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Test if API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key found")
print(f"API Key length: {len(api_key) if api_key else 0}")
