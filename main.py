# main.py

import os
from config import BASE_DIR
from repo_loader import clone_or_load_repo, get_source_files, read_file
from chunking import chunk_code
from embedding_store import add_documents, query_codebase
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def ask_llm(context, question):
    """Send context + question to OpenRouter for an answer."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Debug API key
    print(f"[DEBUG] API Key length: {len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 'None'}")
    print(f"[DEBUG] API Key prefix: {OPENROUTER_API_KEY[:10] if OPENROUTER_API_KEY else 'None'}...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost:3000",  # Optional: helps with rate limiting
        "X-Title": "Codebase Assistant"  # Optional: helps with monitoring
    }
    data = {
        "model": "deepseek/deepseek-chat",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a helpful AI codebase assistant."},
            {"role": "user", "content": f"Here are relevant code snippets:\n{context}\n\nQuestion: {question}"}
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=data)
        print(f"[DEBUG] Response status: {resp.status_code}")
        print(f"[DEBUG] Response headers: {dict(resp.headers)}")
        print(f"[DEBUG] Response text: {resp.text[:500]}...")  # First 500 chars
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error: {e}")
        print(f"[ERROR] Full response text: {resp.text}")
        raise
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        raise

# --- STEP 1: Load repo ---
REPO_URL = "https://github.com/DaniyalHasan089/Car-Model-Detection-Using-CNN"  # example repo
LOCAL_REPO_PATH = os.path.join(BASE_DIR, "repo")

clone_or_load_repo(REPO_URL, LOCAL_REPO_PATH)

# --- STEP 2: Get source files ---
files = get_source_files(LOCAL_REPO_PATH)
print(f"[INFO] Found {len(files)} source files.")

# --- STEP 3: Chunk and embed ---
all_chunks = []
for file in files:
    text = read_file(file)
    chunks = chunk_code(text)
    all_chunks.extend(chunks)

print(f"[INFO] Total chunks: {len(all_chunks)}")
add_documents(all_chunks)

# --- STEP 4: Query loop ---
while True:
    query = input("\nAsk a question about the codebase (or 'exit'): ")
    if query.lower() == "exit":
        break
    results = query_codebase(query)
    docs = results["documents"][0]
    context = "\n---\n".join(docs)
    answer = ask_llm(context, query)
    print("\n💡 Answer:\n", answer)
