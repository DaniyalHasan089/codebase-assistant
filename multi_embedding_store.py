# multi_embedding_store.py

import os
import hashlib
from typing import List, Dict
from config import DB_DIR

# Import ChromaDB with Streamlit Cloud compatibility
try:
    from chromadb_compat import chromadb
except ImportError:
    import chromadb

class MultiCodebaseEmbeddingStore:
    def __init__(self, base_db_dir: str = DB_DIR):
        self.base_db_dir = base_db_dir
        self.clients = {}  # Cache for ChromaDB clients
        self.collections = {}  # Cache for collections
    
    def get_collection_name(self, codebase_id: int) -> str:
        """Generate a unique collection name for a codebase."""
        return f"codebase_{codebase_id}"
    
    def get_db_path(self, codebase_id: int) -> str:
        """Get the database path for a specific codebase."""
        return os.path.join(self.base_db_dir, f"codebase_{codebase_id}")
    
    def get_client_and_collection(self, codebase_id: int):
        """Get or create ChromaDB client and collection for a codebase."""
        if codebase_id not in self.clients:
            db_path = self.get_db_path(codebase_id)
            os.makedirs(db_path, exist_ok=True)
            
            self.clients[codebase_id] = chromadb.PersistentClient(path=db_path)
            collection_name = self.get_collection_name(codebase_id)
            self.collections[codebase_id] = self.clients[codebase_id].get_or_create_collection(
                name=collection_name
            )
        
        return self.clients[codebase_id], self.collections[codebase_id]
    
    def get_embedding(self, text: str) -> List[float]:
        """Get vector embedding using hash-based approach."""
        # Create a hash-based "embedding" as a fallback
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hex to a list of floats to simulate an embedding vector
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            # Convert hex to int, then normalize to [-1, 1] range
            val = (int(hex_pair, 16) - 127.5) / 127.5
            embedding.append(val)
        
        # Pad or truncate to a standard embedding size (16 dimensions)
        target_size = 16
        if len(embedding) < target_size:
            embedding.extend([0.0] * (target_size - len(embedding)))
        else:
            embedding = embedding[:target_size]
        
        return embedding
    
    def add_documents(self, codebase_id: int, documents: List[str], metadata: List[Dict] = None, replace_existing: bool = True):
        """Add documents to a specific codebase collection."""
        if not documents:
            return
        
        client, collection = self.get_client_and_collection(codebase_id)
        
        # Generate IDs, embeddings, and metadata
        ids = [f"doc_{codebase_id}_{i}" for i in range(len(documents))]
        embeddings = [self.get_embedding(doc) for doc in documents]
        
        if metadata is None:
            metadata = [{"chunk_id": i, "codebase_id": codebase_id} for i in range(len(documents))]
        else:
            # Ensure codebase_id is in metadata
            for meta in metadata:
                meta["codebase_id"] = codebase_id
        
        # Clear existing data first (for updates) - but only if replacing
        if replace_existing:
            try:
                # Get all existing IDs for this codebase
                existing_results = collection.get(where={"codebase_id": codebase_id})
                if existing_results and existing_results.get('ids'):
                    existing_ids = existing_results['ids']
                    print(f"[INFO] Removing {len(existing_ids)} existing documents for codebase {codebase_id}")
                    collection.delete(ids=existing_ids)
            except Exception as e:
                print(f"[WARNING] Could not clear existing documents: {e}")
        
        # Add new documents
        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata
            )
            print(f"[INFO] Added {len(documents)} documents to codebase {codebase_id}")
        except Exception as e:
            print(f"[ERROR] Failed to add documents: {e}")
            raise
    
    def query_codebase(self, codebase_id: int, query: str, n_results: int = 3) -> Dict:
        """Query a specific codebase."""
        if codebase_id not in self.collections:
            raise ValueError(f"Codebase {codebase_id} not found in embedding store")
        
        collection = self.collections[codebase_id]
        query_embedding = self.get_embedding(query)
        
        results = collection.query(
            query_embeddings=[query_embedding], 
            n_results=n_results
        )
        
        return results
    
    def delete_codebase(self, codebase_id: int):
        """Delete all data for a specific codebase."""
        import time
        import gc
        
        # Try to properly close ChromaDB connections first
        if codebase_id in self.clients:
            try:
                # Try to close the client connection if possible
                client = self.clients[codebase_id]
                # ChromaDB doesn't have an explicit close method, but we can delete references
                del self.clients[codebase_id]
            except Exception as e:
                print(f"[WARNING] Error closing ChromaDB client: {e}")
        
        if codebase_id in self.collections:
            del self.collections[codebase_id]
        
        # Force garbage collection to release file handles
        gc.collect()
        time.sleep(0.5)  # Give Windows time to release file handles
        
        # Remove database directory with retry logic
        db_path = self.get_db_path(codebase_id)
        if os.path.exists(db_path):
            self._force_remove_directory(db_path)
            print(f"[INFO] Deleted embedding data for codebase {codebase_id}")
    
    def _force_remove_directory(self, path: str):
        """Force remove directory, handling Windows file permission issues."""
        import stat
        import time
        import shutil
        
        def handle_remove_readonly(func, path, exc):
            """Handle read-only files on Windows."""
            if os.path.exists(path):
                # Make file writable and try again
                os.chmod(path, stat.S_IWRITE)
                func(path)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # First attempt: normal removal
                shutil.rmtree(path)
                return
            except (PermissionError, OSError) as e:
                print(f"[INFO] Attempt {attempt + 1}: Handling file permissions issue...")
                
                if attempt < max_retries - 1:
                    # Handle read-only files
                    try:
                        # Walk through and unlock all files
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    os.chmod(file_path, stat.S_IWRITE)
                                except:
                                    pass
                            for dir in dirs:
                                dir_path = os.path.join(root, dir)
                                try:
                                    os.chmod(dir_path, stat.S_IWRITE)
                                except:
                                    pass
                        
                        # Small delay to let Windows release file handles
                        time.sleep(1.0)
                        
                        # Try removal with error handler
                        shutil.rmtree(path, onerror=handle_remove_readonly)
                        return
                        
                    except Exception as retry_error:
                        print(f"[WARNING] Retry {attempt + 1} failed: {retry_error}")
                        if attempt < max_retries - 1:
                            time.sleep(2.0)  # Wait longer between retries
                        continue
                else:
                    # Final attempt: rename instead of delete
                    backup_path = f"{path}_backup_{int(time.time())}"
                    try:
                        os.rename(path, backup_path)
                        print(f"[WARNING] Could not delete {path}, renamed to {backup_path}")
                    except Exception as final_error:
                        print(f"[ERROR] Cannot remove or rename directory {path}: {final_error}")
                        raise
    
    def list_codebases(self) -> List[int]:
        """List all codebase IDs that have embedding data."""
        if not os.path.exists(self.base_db_dir):
            return []
        
        codebase_ids = []
        for item in os.listdir(self.base_db_dir):
            if item.startswith("codebase_") and os.path.isdir(os.path.join(self.base_db_dir, item)):
                try:
                    codebase_id = int(item.split("_")[1])
                    codebase_ids.append(codebase_id)
                except ValueError:
                    continue
        
        return sorted(codebase_ids)
    
    def get_codebase_stats(self, codebase_id: int) -> Dict:
        """Get statistics for a codebase."""
        if codebase_id not in self.collections:
            try:
                self.get_client_and_collection(codebase_id)
            except:
                return {"document_count": 0, "exists": False}
        
        collection = self.collections[codebase_id]
        try:
            count = collection.count()
            return {"document_count": count, "exists": True}
        except:
            return {"document_count": 0, "exists": False}
