# chunking.py

from config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_code(text: str):
    lines = text.split("\n")
    chunks = []

    for i in range(0, len(lines), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = "\n".join(lines[i:i + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk)

    return chunks
