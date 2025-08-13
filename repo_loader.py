# repo_loader.py

import os
import git

def clone_or_load_repo(repo_url: str, local_path: str):
    # Check if repo exists and if it's the same URL
    if os.path.exists(local_path) and os.listdir(local_path):
        try:
            # Check if existing repo matches the requested URL
            existing_repo = git.Repo(local_path)
            existing_url = existing_repo.remotes.origin.url
            
            if existing_url == repo_url:
                print(f"[INFO] Using existing repo at {local_path}")
                return
            else:
                print(f"[INFO] Different repo URL detected. Removing old repo...")
                print(f"[INFO] Old: {existing_url}")
                print(f"[INFO] New: {repo_url}")
                import shutil
                shutil.rmtree(local_path)
        except Exception as e:
            print(f"[INFO] Error checking existing repo: {e}")
            print(f"[INFO] Removing and re-cloning...")
            import shutil
            shutil.rmtree(local_path)
    
    print(f"[INFO] Cloning {repo_url}...")
    git.Repo.clone_from(repo_url, local_path)

def get_source_files(repo_path: str, exts=(".py", ".js", ".java", ".ts", ".cpp", ".go", ".ipynb", ".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".xml", ".html", ".css", ".sql", ".sh", ".bat", ".r", ".scala", ".kt", ".swift", ".php", ".rb", ".cs", ".c", ".h", ".hpp", ".cc", ".cxx")):
    source_files = []
    for root, _, files in os.walk(repo_path):
        # Skip hidden directories and common non-source directories
        if any(part.startswith('.') for part in root.split(os.sep)) or \
           any(part in ['node_modules', '__pycache__', 'target', 'build', 'dist', 'bin', 'obj'] for part in root.split(os.sep)):
            continue
            
        for file in files:
            # Skip hidden files and common non-source files
            if file.startswith('.') or file.endswith(('.exe', '.dll', '.so', '.dylib', '.class', '.jar', '.war', '.zip', '.tar', '.gz', '.pdf', '.docx', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg')):
                continue
                
            if file.endswith(exts):
                source_files.append(os.path.join(root, file))
    return source_files

def read_file(path: str):
    try:
        # Special handling for Jupyter notebooks
        if path.endswith('.ipynb'):
            import json
            with open(path, "r", encoding="utf-8") as f:
                notebook = json.load(f)
            
            # Extract code and markdown cells
            content = []
            content.append(f"# Jupyter Notebook: {os.path.basename(path)}\n")
            
            for i, cell in enumerate(notebook.get('cells', [])):
                cell_type = cell.get('cell_type', 'unknown')
                source = cell.get('source', [])
                
                if isinstance(source, list):
                    source = ''.join(source)
                
                if cell_type == 'code' and source.strip():
                    content.append(f"\n## Code Cell {i+1}\n```python\n{source}\n```\n")
                elif cell_type == 'markdown' and source.strip():
                    content.append(f"\n## Markdown Cell {i+1}\n{source}\n")
            
            return '\n'.join(content)
        else:
            # Regular file reading
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {path}: {e}")
        return ""
