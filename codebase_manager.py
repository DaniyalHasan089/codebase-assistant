# codebase_manager.py

import os
import shutil
from typing import List, Dict, Optional
from database import CodebaseDatabase
from multi_embedding_store import MultiCodebaseEmbeddingStore
from repo_loader import clone_or_load_repo, get_source_files, read_file
from chunking import chunk_code
from config import BASE_DIR, OPENROUTER_API_KEY, DEFAULT_MODEL, AVAILABLE_MODELS, STORAGE_MODE_LOCAL, STORAGE_MODE_TEMP
import requests
import json
import sqlite3
from temp_processor import TempRepositoryProcessor

class CodebaseManager:
    def __init__(self):
        self.db = CodebaseDatabase()
        self.embedding_store = MultiCodebaseEmbeddingStore()
        self.temp_processor = TempRepositoryProcessor()
        self.current_codebase_id = None
    
    def add_codebase(self, name: str, repo_url: str, description: str = "", storage_mode: str = STORAGE_MODE_LOCAL) -> int:
        """Add a new codebase from a Git repository."""
        print(f"[INFO] Adding codebase: {name} (mode: {storage_mode})")
        
        try:
            if storage_mode == STORAGE_MODE_TEMP:
                return self._add_codebase_temp(name, repo_url, description)
            else:
                return self._add_codebase_local(name, repo_url, description)
                
        except Exception as e:
            print(f"[ERROR] Failed to add codebase: {e}")
            raise
    
    def _add_codebase_local(self, name: str, repo_url: str, description: str = "") -> int:
        """Add codebase with local storage (original behavior)."""
        # Create local path
        local_path = os.path.join(BASE_DIR, "repos", name.replace(" ", "_").lower())
        
        try:
            # Add to database first
            codebase_id = self.db.add_codebase(name, repo_url, local_path, description, STORAGE_MODE_LOCAL)
            
            # Clone repository
            clone_or_load_repo(repo_url, local_path)
            
            # Process files and create embeddings
            self._process_codebase(codebase_id, local_path)
            
            print(f"[SUCCESS] Added codebase '{name}' with ID {codebase_id}")
            return codebase_id
            
        except Exception as e:
            # Cleanup on failure
            try:
                self.db.delete_codebase(codebase_id)
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
            except:
                pass
            raise e
    
    def _add_codebase_temp(self, name: str, repo_url: str, description: str = "") -> int:
        """Add codebase with temporary processing (no permanent storage)."""
        try:
            # Process repository temporarily
            print(f"[INFO] Processing repository temporarily...")
            chunks, metadata, commit_hash = self.temp_processor.process_repository(repo_url, name)
            
            # Add to database (no local_path for temp mode)
            codebase_id = self.db.add_codebase(
                name=name,
                repo_url=repo_url,
                local_path=None,
                description=description,
                storage_mode=STORAGE_MODE_TEMP,
                commit_hash=commit_hash,
                repo_metadata=json.dumps(metadata)
            )
            
            print(f"[INFO] Adding {len(chunks)} chunks to embedding store...")
            
            # Add chunks to embedding store
            self.embedding_store.add_documents(codebase_id, chunks, replace_existing=True)
            
            # Update database stats
            self.db.update_codebase_stats(codebase_id, metadata.get('processed_files', 0), len(chunks))
            
            print(f"[SUCCESS] Added temporary codebase '{name}' with ID {codebase_id}")
            print(f"[INFO] Repository files processed and deleted, only embeddings stored")
            return codebase_id
            
        except Exception as e:
            print(f"[ERROR] Failed to add temporary codebase: {e}")
            raise
    
    def _process_codebase(self, codebase_id: int, local_path: str):
        """Process a codebase: extract files, create chunks, and embeddings."""
        print(f"[INFO] Processing codebase {codebase_id}...")
        
        # Get source files
        files = get_source_files(local_path)
        print(f"[INFO] Found {len(files)} source files")
        
        if not files:
            print("[WARNING] No source files found!")
            return
        
        # Create chunks
        all_chunks = []
        chunk_metadata = []
        
        for i, file_path in enumerate(files):
            try:
                content = read_file(file_path)
                if content.strip():  # Only process non-empty files
                    chunks = chunk_code(content)
                    
                    # Add metadata for each chunk
                    rel_path = os.path.relpath(file_path, local_path)
                    for j, chunk in enumerate(chunks):
                        all_chunks.append(chunk)
                        chunk_metadata.append({
                            "file_path": rel_path,
                            "file_index": i,
                            "chunk_index": j,
                            "chunk_id": len(all_chunks) - 1
                        })
            except Exception as e:
                print(f"[WARNING] Could not process file {file_path}: {e}")
                continue
        
        print(f"[INFO] Created {len(all_chunks)} chunks")
        
        # Store embeddings
        if all_chunks:
            self.embedding_store.add_documents(codebase_id, all_chunks, chunk_metadata)
            print(f"[SUCCESS] Processed codebase {codebase_id}")
        else:
            # Create empty collection to avoid errors
            self.embedding_store.add_documents(codebase_id, ["No processable source files found in this repository."], [{"file_path": "README", "file_index": 0, "chunk_index": 0, "chunk_id": 0}])
            print(f"[WARNING] No processable content found in codebase {codebase_id}")
        
        # Update database stats
        self.db.update_codebase_stats(codebase_id, len(files), len(all_chunks))
    
    def list_codebases(self) -> List[Dict]:
        """List all available codebases."""
        return self.db.list_codebases()
    
    def get_codebase(self, codebase_id: int) -> Optional[Dict]:
        """Get codebase information by ID."""
        return self.db.get_codebase(codebase_id)
    
    def get_codebase_by_name(self, name: str) -> Optional[Dict]:
        """Get codebase information by name."""
        return self.db.get_codebase_by_name(name)
    
    def switch_codebase(self, codebase_id: int) -> bool:
        """Switch to a different codebase."""
        codebase = self.db.get_codebase(codebase_id)
        if codebase:
            self.current_codebase_id = codebase_id
            print(f"[INFO] Switched to codebase: {codebase['name']}")
            return True
        return False
    
    def delete_codebase(self, codebase_id: int) -> bool:
        """Delete a codebase completely."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return False
        
        try:
            # Delete from database
            self.db.delete_codebase(codebase_id)
            
            # Delete embeddings
            self.embedding_store.delete_codebase(codebase_id)
            
            # Delete local repository
            if os.path.exists(codebase['local_path']):
                shutil.rmtree(codebase['local_path'])
            
            # Clear current codebase if it was deleted
            if self.current_codebase_id == codebase_id:
                self.current_codebase_id = None
            
            print(f"[SUCCESS] Deleted codebase: {codebase['name']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete codebase: {e}")
            return False
    
    def refresh_codebase(self, codebase_id: int) -> bool:
        """Refresh a codebase (re-process existing files or re-clone if needed)."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return False
        
        try:
            storage_mode = codebase.get('storage_mode', STORAGE_MODE_LOCAL)
            
            if storage_mode == STORAGE_MODE_TEMP:
                # For temporary storage, re-process from repository
                print(f"[INFO] Re-processing temporary codebase: {codebase['name']}")
                return self._refresh_temp_codebase(codebase_id)
            else:
                # For local storage, try existing files first
                if codebase['local_path'] and os.path.exists(codebase['local_path']):
                    try:
                        print(f"[INFO] Re-processing existing files (safe mode)...")
                        self._safe_process_codebase(codebase_id, codebase['local_path'])
                        print(f"[SUCCESS] Refreshed codebase: {codebase['name']}")
                        return True
                    except Exception as e:
                        print(f"[INFO] Safe refresh failed: {e}")
                
                # If simple refresh fails or directory doesn't exist, try re-cloning
                print("[INFO] Attempting to re-clone repository...")
                return self._reclone_codebase(codebase_id)
            
        except Exception as e:
            print(f"[ERROR] Failed to refresh codebase: {e}")
            return False
    
    def _full_refresh_codebase(self, codebase_id: int, codebase: dict) -> bool:
        """Perform full refresh by re-cloning the repository."""
        try:
            # Handle Windows file permission issues with Git repositories
            if os.path.exists(codebase['local_path']):
                print(f"[INFO] Removing existing repository...")
                self._force_remove_directory(codebase['local_path'])
            
            # Re-clone and process
            print(f"[INFO] Re-cloning repository...")
            clone_or_load_repo(codebase['repo_url'], codebase['local_path'])
            
            print(f"[INFO] Re-processing files...")
            self._process_codebase(codebase_id, codebase['local_path'])
            
            print(f"[SUCCESS] Refreshed codebase: {codebase['name']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Full refresh failed: {e}")
            return False
    
    def _force_remove_directory(self, path: str):
        """Force remove directory, handling Windows file permission issues."""
        import stat
        import time
        
        def handle_remove_readonly(func, path, exc):
            """Handle read-only files on Windows."""
            if os.path.exists(path):
                # Make file writable and try again
                os.chmod(path, stat.S_IWRITE)
                func(path)
        
        try:
            # First attempt: normal removal
            shutil.rmtree(path)
        except (PermissionError, OSError) as e:
            print(f"[INFO] Handling file permissions issue...")
            
            # Second attempt: handle read-only files
            try:
                shutil.rmtree(path, onerror=handle_remove_readonly)
            except (PermissionError, OSError):
                # Third attempt: force unlock files
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
                    time.sleep(0.5)
                    
                    # Final removal attempt
                    shutil.rmtree(path, onerror=handle_remove_readonly)
                    
                except Exception as final_error:
                    print(f"[WARNING] Could not fully remove {path}: {final_error}")
                    # Create a backup directory name and rename instead
                    backup_path = f"{path}_backup_{int(time.time())}"
                    try:
                        os.rename(path, backup_path)
                        print(f"[INFO] Moved problematic directory to: {backup_path}")
                    except:
                        raise Exception(f"Cannot remove or rename directory: {path}")
    
    def reprocess_codebase(self, codebase_id: int) -> bool:
        """Reprocess an existing codebase without re-cloning (faster, no Git issues)."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return False
        
        if not os.path.exists(codebase['local_path']):
            print(f"[ERROR] Repository directory not found: {codebase['local_path']}")
            return False
        
        try:
            print(f"[INFO] Reprocessing codebase: {codebase['name']}")
            
            # Process the codebase (safe mode - no file deletion)
            self._safe_process_codebase(codebase_id, codebase['local_path'])
            
            print(f"[SUCCESS] Reprocessed codebase: {codebase['name']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to reprocess codebase: {e}")
            return False
    
    def _refresh_temp_codebase(self, codebase_id: int) -> bool:
        """Refresh a temporary codebase by re-processing from repository."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return False
        
        try:
            # Re-process repository temporarily
            chunks, metadata, commit_hash = self.temp_processor.process_repository(codebase['repo_url'], codebase['name'])
            
            # Update database with new commit hash and metadata
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE codebases 
                SET commit_hash = ?, repo_metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (commit_hash, json.dumps(metadata), codebase_id))
            conn.commit()
            conn.close()
            
            # Replace documents in embedding store
            self.embedding_store.add_documents(codebase_id, chunks, replace_existing=True)
            
            # Update stats
            self.db.update_codebase_stats(codebase_id, metadata.get('processed_files', 0), len(chunks))
            
            print(f"[SUCCESS] Refreshed temporary codebase: {codebase['name']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to refresh temporary codebase: {e}")
            return False
    
    def _safe_process_codebase(self, codebase_id: int, local_path: str):
        """Process codebase without deleting existing ChromaDB files."""
        # Get source files
        source_files = get_source_files(local_path)
        print(f"[INFO] Found {len(source_files)} source files")
        
        if not source_files:
            # If no source files found, add placeholder
            docs = ["No processable source files found in this repository. It may contain only documentation, images, or other non-code files."]
            print("[WARNING] No processable source files found, adding placeholder")
        else:
            # Read and chunk files
            docs = []
            for file_path in source_files:
                content = read_file(file_path)
                if content:
                    chunks = chunk_code(content)
                    docs.extend(chunks)
        
        print(f"[INFO] Created {len(docs)} chunks")
        
        # Add to embedding store (this will replace existing documents safely)
        self.embedding_store.add_documents(codebase_id, docs, replace_existing=True)
        
        # Update database stats
        self.db.update_codebase_stats(codebase_id, len(source_files), len(docs))
        
        print(f"[SUCCESS] Processed codebase {codebase_id}")
    
    def _reclone_codebase(self, codebase_id: int) -> bool:
        """Re-clone a codebase repository."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return False
        
        try:
            # Remove existing directory if it exists (but don't touch ChromaDB)
            if os.path.exists(codebase['local_path']):
                print(f"[INFO] Removing existing repository...")
                self._force_remove_directory(codebase['local_path'])
            
            # Clone repository
            print(f"[INFO] Cloning {codebase['repo_url']}...")
            clone_or_load_repo(codebase['repo_url'], codebase['local_path'])
            
            # Process the codebase
            self._safe_process_codebase(codebase_id, codebase['local_path'])
            
            print(f"[SUCCESS] Re-cloned and processed codebase: {codebase['name']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to re-clone codebase: {e}")
            return False
    
    def query_current_codebase(self, question: str, n_results: int = 3, model: str = None) -> str:
        """Query the currently selected codebase."""
        if not self.current_codebase_id:
            return "No codebase selected. Please select a codebase first."
        
        return self.query_codebase(self.current_codebase_id, question, n_results, model)
    
    def query_codebase(self, codebase_id: int, question: str, n_results: int = 3, model: str = None) -> str:
        """Query a specific codebase."""
        codebase = self.db.get_codebase(codebase_id)
        if not codebase:
            return "Codebase not found."
        
        # Use default model if none specified
        if model is None:
            model = DEFAULT_MODEL
        
        try:
            # Get relevant context from embeddings
            results = self.embedding_store.query_codebase(codebase_id, question, n_results)
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant code found for your question. The codebase might be empty or not properly processed."
            
            # Prepare context
            context_chunks = results['documents'][0]
            context = "\n---\n".join(context_chunks)
            
            # Check if we only have the placeholder message
            if len(context_chunks) == 1 and "No processable source files" in context_chunks[0]:
                return f"This codebase appears to contain no processable source code files. It may contain only documentation, images, or other non-code files. Files found: {', '.join([os.path.basename(f) for f in os.listdir(codebase['local_path']) if os.path.isfile(os.path.join(codebase['local_path'], f))])}"
            
            # Get answer from LLM
            answer = self._ask_llm(context, question, codebase['name'], model)
            
            # Save to chat history (just the clean answer)
            self.db.add_chat_entry(codebase_id, question, answer)
            
            return answer
            
        except Exception as e:
            error_msg = f"Error querying codebase: {e}"
            print(f"[ERROR] {error_msg}")
            
            # Provide more helpful error messages
            if "not found in embedding store" in str(e):
                return "This codebase hasn't been properly processed yet. Try refreshing the codebase from the Manage tab."
            else:
                return f"An error occurred while processing your question: {e}"
    
    def _ask_llm(self, context: str, question: str, codebase_name: str, model: str = None) -> str:
        """Send context + question to OpenRouter for an answer."""
        if model is None:
            model = DEFAULT_MODEL
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000",
            "X-Title": "Codebase Assistant"
        }
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": f"You are a helpful AI assistant analyzing the '{codebase_name}' codebase. Provide clear, accurate answers based on the provided code context."
                },
                {
                    "role": "user", 
                    "content": f"Here are relevant code snippets from {codebase_name}:\n\n{context}\n\nQuestion: {question}"
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error getting AI response: {e}"
    
    def get_chat_history(self, codebase_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a codebase."""
        return self.db.get_chat_history(codebase_id, limit)
    
    def get_current_codebase(self) -> Optional[Dict]:
        """Get the currently selected codebase."""
        if self.current_codebase_id:
            return self.db.get_codebase(self.current_codebase_id)
        return None
    
    def test_model_availability(self, model_id: str) -> Dict:
        """Test if a model is available and working on OpenRouter."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000",
            "X-Title": "Codebase Assistant - Model Test"
        }
        
        # Simple test message
        data = {
            "model": model_id,
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello! Please respond with just 'OK' to confirm you're working."
                }
            ],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return {
                            "available": True,
                            "response": result["choices"][0]["message"]["content"].strip(),
                            "error": None
                        }
                    else:
                        return {
                            "available": False,
                            "response": None,
                            "error": "No response choices in API result"
                        }
                except Exception as json_error:
                    return {
                        "available": False,
                        "response": None,
                        "error": f"JSON decode error: {json_error}"
                    }
            else:
                return {
                    "available": False,
                    "response": None,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "available": False,
                "response": None,
                "error": "Request timeout (30s)"
            }
        except Exception as e:
            return {
                "available": False,
                "response": None,
                "error": f"Request error: {e}"
            }
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of models that are actually available and working."""
        print("[INFO] Testing model availability...")
        available_models = {}
        
        for model_id, model_info in AVAILABLE_MODELS.items():
            print(f"[INFO] Testing {model_info['name']}...")
            test_result = self.test_model_availability(model_id)
            
            if test_result["available"]:
                available_models[model_id] = {
                    **model_info,
                    "status": "available",
                    "test_response": test_result["response"]
                }
                print(f"[SUCCESS] ✅ {model_info['name']} is working")
            else:
                print(f"[WARNING] ❌ {model_info['name']} failed: {test_result['error']}")
                # Still include in list but mark as unavailable
                available_models[model_id] = {
                    **model_info,
                    "status": "unavailable",
                    "error": test_result["error"]
                }
        
        return available_models
