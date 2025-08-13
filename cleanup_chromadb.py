#!/usr/bin/env python3
"""
ChromaDB Cleanup Utility

This utility helps clean up locked ChromaDB files on Windows when the main application
cannot access them due to file locking issues.

Usage:
    python cleanup_chromadb.py [codebase_id]
    
If no codebase_id is provided, it will list all ChromaDB directories and let you choose.
"""

import os
import sys
import time
import stat
import shutil
import subprocess
from pathlib import Path

def find_chromadb_directories():
    """Find all ChromaDB directories in the vector_db folder."""
    vector_db_dir = Path("vector_db")
    if not vector_db_dir.exists():
        print("❌ No vector_db directory found")
        return []
    
    chromadb_dirs = []
    for item in vector_db_dir.iterdir():
        if item.is_dir() and item.name.startswith("codebase_"):
            try:
                codebase_id = int(item.name.split("_")[1])
                chromadb_dirs.append((codebase_id, item))
            except ValueError:
                continue
    
    return sorted(chromadb_dirs)

def kill_processes_using_directory(directory):
    """Try to kill processes that might be using the directory."""
    try:
        # Use Windows handle.exe if available
        result = subprocess.run(['handle.exe', str(directory)], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("🔍 Found processes using the directory:")
            print(result.stdout)
            
            # Extract process IDs and try to kill them
            lines = result.stdout.split('\n')
            pids = set()
            for line in lines:
                if 'pid:' in line:
                    try:
                        pid = line.split('pid:')[1].strip().split()[0]
                        pids.add(int(pid))
                    except (IndexError, ValueError):
                        continue
            
            for pid in pids:
                try:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                 capture_output=True, timeout=5)
                    print(f"🔥 Killed process {pid}")
                except:
                    print(f"⚠️ Could not kill process {pid}")
                    
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ handle.exe not available, skipping process cleanup")

def force_remove_directory(path):
    """Force remove a directory with Windows-specific handling."""
    path = Path(path)
    
    def handle_remove_readonly(func, path_str, exc):
        """Handle read-only files on Windows."""
        path_obj = Path(path_str)
        if path_obj.exists():
            # Make file writable and try again
            path_obj.chmod(stat.S_IWRITE)
            func(path_str)
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # First attempt: normal removal
            shutil.rmtree(path)
            print(f"✅ Successfully removed {path}")
            return True
            
        except (PermissionError, OSError) as e:
            print(f"🔄 Attempt {attempt + 1}/{max_retries}: {e}")
            
            if attempt < max_retries - 1:
                # Try to kill processes using the directory
                if attempt == 1:
                    print("🔍 Trying to kill processes using the directory...")
                    kill_processes_using_directory(path)
                
                # Handle read-only files
                try:
                    # Walk through and unlock all files
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = Path(root) / file
                            try:
                                file_path.chmod(stat.S_IWRITE)
                            except:
                                pass
                        for dir_name in dirs:
                            dir_path = Path(root) / dir_name
                            try:
                                dir_path.chmod(stat.S_IWRITE)
                            except:
                                pass
                    
                    # Wait longer between retries
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⏳ Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    
                    # Try removal with error handler
                    shutil.rmtree(path, onerror=handle_remove_readonly)
                    print(f"✅ Successfully removed {path}")
                    return True
                    
                except Exception as retry_error:
                    print(f"⚠️ Retry {attempt + 1} failed: {retry_error}")
                    continue
            else:
                # Final attempt: rename instead of delete
                backup_path = path.parent / f"{path.name}_backup_{int(time.time())}"
                try:
                    path.rename(backup_path)
                    print(f"⚠️ Could not delete {path}, renamed to {backup_path}")
                    print("💡 You can manually delete this folder later when no processes are using it")
                    return True
                except Exception as final_error:
                    print(f"❌ Cannot remove or rename directory {path}: {final_error}")
                    return False
    
    return False

def cleanup_codebase(codebase_id):
    """Clean up ChromaDB files for a specific codebase."""
    chromadb_dir = Path(f"vector_db/codebase_{codebase_id}")
    
    if not chromadb_dir.exists():
        print(f"❌ ChromaDB directory for codebase {codebase_id} does not exist")
        return False
    
    print(f"🧹 Cleaning up ChromaDB for codebase {codebase_id}")
    print(f"📁 Directory: {chromadb_dir}")
    
    # Show directory size
    try:
        total_size = sum(f.stat().st_size for f in chromadb_dir.rglob('*') if f.is_file())
        print(f"📊 Directory size: {total_size / 1024 / 1024:.1f} MB")
    except:
        print("📊 Could not calculate directory size")
    
    # Confirm deletion
    response = input(f"\n⚠️ Are you sure you want to delete ChromaDB data for codebase {codebase_id}? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return False
    
    return force_remove_directory(chromadb_dir)

def main():
    """Main function."""
    print("🧹 ChromaDB Cleanup Utility")
    print("=" * 40)
    
    # Check if running from correct directory
    if not Path("config.py").exists():
        print("❌ Please run this script from the codebase-assistant directory")
        sys.exit(1)
    
    # Get codebase ID from command line or prompt user
    if len(sys.argv) > 1:
        try:
            codebase_id = int(sys.argv[1])
            cleanup_codebase(codebase_id)
        except ValueError:
            print("❌ Invalid codebase ID. Please provide a number.")
            sys.exit(1)
    else:
        # List available ChromaDB directories
        chromadb_dirs = find_chromadb_directories()
        
        if not chromadb_dirs:
            print("❌ No ChromaDB directories found")
            sys.exit(1)
        
        print("📁 Available ChromaDB directories:")
        for i, (codebase_id, path) in enumerate(chromadb_dirs, 1):
            try:
                total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                size_mb = total_size / 1024 / 1024
                print(f"  {i}. Codebase {codebase_id} ({size_mb:.1f} MB)")
            except:
                print(f"  {i}. Codebase {codebase_id} (size unknown)")
        
        print("  0. Clean all ChromaDB directories")
        
        try:
            choice = input("\n🔢 Enter your choice (0-{}): ".format(len(chromadb_dirs)))
            choice = int(choice)
            
            if choice == 0:
                # Clean all
                for codebase_id, _ in chromadb_dirs:
                    print(f"\n{'='*20}")
                    cleanup_codebase(codebase_id)
            elif 1 <= choice <= len(chromadb_dirs):
                codebase_id = chromadb_dirs[choice - 1][0]
                cleanup_codebase(codebase_id)
            else:
                print("❌ Invalid choice")
                sys.exit(1)
                
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cleanup cancelled")
            sys.exit(1)
    
    print("\n🎉 Cleanup completed!")
    print("💡 You can now try refreshing/reprocessing your codebases in the GUI")

if __name__ == "__main__":
    main()

