#!/usr/bin/env python3
"""
Temporary Repository Processor

This module handles processing Git repositories without storing them permanently.
It clones to a temporary directory, processes the files, then deletes everything.
"""

import os
import json
import tempfile
import shutil
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import git
from repo_loader import get_source_files, read_file
from chunking import chunk_code

class TempRepositoryProcessor:
    """Process repositories temporarily without permanent storage."""
    
    def __init__(self):
        self.temp_dir = None
    
    def process_repository(self, repo_url: str, name: str) -> Tuple[List[str], Dict, str]:
        """
        Process a repository temporarily and return processed data.
        
        Args:
            repo_url: URL of the Git repository
            name: Name for the codebase
            
        Returns:
            Tuple of (chunks, metadata, commit_hash)
        """
        self.temp_dir = tempfile.mkdtemp(prefix=f"codebase_temp_{name}_")
        
        try:
            print(f"[INFO] Cloning {repo_url} to temporary directory...")
            
            # Clone repository
            repo = git.Repo.clone_from(repo_url, self.temp_dir)
            commit_hash = repo.head.commit.hexsha
            
            print(f"[INFO] Processing repository (commit: {commit_hash[:8]})")
            
            # Get source files
            source_files = get_source_files(self.temp_dir)
            print(f"[INFO] Found {len(source_files)} source files")
            
            # Process files and create chunks
            chunks = []
            file_info = []
            
            for file_path in source_files:
                try:
                    content = read_file(file_path)
                    if content:
                        # Get relative path for metadata
                        rel_path = os.path.relpath(file_path, self.temp_dir)
                        file_info.append({
                            'path': rel_path,
                            'size': len(content),
                            'type': os.path.splitext(rel_path)[1]
                        })
                        
                        # Create chunks
                        file_chunks = chunk_code(content)
                        chunks.extend(file_chunks)
                        
                except Exception as e:
                    print(f"[WARNING] Could not process {file_path}: {e}")
                    continue
            
            print(f"[INFO] Created {len(chunks)} chunks from {len(file_info)} files")
            
            # Create metadata
            metadata = {
                'repo_url': repo_url,
                'commit_hash': commit_hash,
                'total_files': len(source_files),
                'processed_files': len(file_info),
                'total_chunks': len(chunks),
                'file_info': file_info,
                'processing_mode': 'temporary'
            }
            
            # Add placeholder if no chunks
            if not chunks:
                chunks = [f"No processable source files found in repository {name}. Repository contains {len(os.listdir(self.temp_dir))} items but no supported code files."]
                metadata['status'] = 'empty'
            else:
                metadata['status'] = 'processed'
            
            return chunks, metadata, commit_hash
            
        except Exception as e:
            print(f"[ERROR] Failed to process repository: {e}")
            raise
        finally:
            # Always cleanup temporary directory
            self._cleanup()
    
    def _cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"[INFO] Cleaned up temporary directory")
            except Exception as e:
                print(f"[WARNING] Could not clean up temporary directory {self.temp_dir}: {e}")
                # Try to rename it for manual cleanup later
                try:
                    backup_name = f"{self.temp_dir}_cleanup_failed"
                    os.rename(self.temp_dir, backup_name)
                    print(f"[INFO] Renamed failed cleanup directory to {backup_name}")
                except:
                    print(f"[WARNING] Temporary directory {self.temp_dir} may need manual cleanup")
            finally:
                self.temp_dir = None
    
    def get_repository_info(self, repo_url: str) -> Dict:
        """Get basic repository information without full processing."""
        temp_dir = tempfile.mkdtemp(prefix="repo_info_")
        
        try:
            print(f"[INFO] Getting repository info for {repo_url}")
            
            # Shallow clone to get basic info
            repo = git.Repo.clone_from(repo_url, temp_dir, depth=1)
            commit_hash = repo.head.commit.hexsha
            
            # Get file count and types
            all_files = []
            for root, dirs, files in os.walk(temp_dir):
                # Skip .git directory
                if '.git' in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    all_files.append(rel_path)
            
            # Get source files
            source_files = get_source_files(temp_dir)
            source_count = len(source_files)
            
            # Get file type distribution
            file_types = {}
            for file_path in all_files:
                ext = os.path.splitext(file_path)[1].lower()
                if not ext:
                    ext = 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            info = {
                'repo_url': repo_url,
                'commit_hash': commit_hash,
                'total_files': len(all_files),
                'source_files': source_count,
                'file_types': file_types,
                'preview_files': all_files[:10],  # First 10 files as preview
                'has_source_code': source_count > 0
            }
            
            return info
            
        except Exception as e:
            print(f"[ERROR] Could not get repository info: {e}")
            raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def estimate_processing_size(self, repo_url: str) -> Dict:
        """Estimate how much data will be processed without full clone."""
        try:
            info = self.get_repository_info(repo_url)
            
            # Rough estimates
            estimated_chunks = info['source_files'] * 3  # Assume ~3 chunks per file
            estimated_size_mb = info['source_files'] * 0.05  # Assume ~50KB per source file
            
            return {
                'estimated_chunks': estimated_chunks,
                'estimated_size_mb': round(estimated_size_mb, 2),
                'source_files': info['source_files'],
                'total_files': info['total_files'],
                'file_types': info['file_types'],
                'suitable_for_temp_processing': info['has_source_code']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'suitable_for_temp_processing': False
            }

def test_temp_processor():
    """Test the temporary processor."""
    processor = TempRepositoryProcessor()
    
    # Test with a small repository
    test_repo = "https://github.com/octocat/Hello-World"
    
    try:
        print("Testing repository info...")
        info = processor.get_repository_info(test_repo)
        print(f"Repository info: {json.dumps(info, indent=2)}")
        
        print("\nTesting size estimation...")
        estimate = processor.estimate_processing_size(test_repo)
        print(f"Size estimate: {json.dumps(estimate, indent=2)}")
        
        print("\nTesting full processing...")
        chunks, metadata, commit_hash = processor.process_repository(test_repo, "test")
        print(f"Processing completed: {len(chunks)} chunks, commit {commit_hash[:8]}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_temp_processor()
