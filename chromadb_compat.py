# chromadb_compat.py
# Compatibility layer for ChromaDB to work with Streamlit Cloud

import sys
import os

def setup_chromadb_compatibility():
    """Setup ChromaDB compatibility for Streamlit Cloud deployment."""
    # Check if we're running on Streamlit Cloud
    if 'streamlit' in sys.modules or os.getenv('STREAMLIT_SERVER_PORT'):
        try:
            # Try to import pysqlite3 and replace sqlite3
            import pysqlite3
            sys.modules['sqlite3'] = pysqlite3
            print("[INFO] Using pysqlite3 for ChromaDB compatibility on Streamlit Cloud")
        except ImportError:
            print("[WARNING] pysqlite3 not available, ChromaDB may not work on Streamlit Cloud")
            pass

# Call the setup function when this module is imported
setup_chromadb_compatibility()

# Now import chromadb
import chromadb

# Re-export chromadb for convenience
__all__ = ['chromadb']
