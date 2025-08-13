# database.py

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class CodebaseDatabase:
    def __init__(self, db_path: str = "codebases.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create codebases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS codebases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                repo_url TEXT NOT NULL,
                local_path TEXT,
                storage_mode TEXT DEFAULT 'local',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                commit_hash TEXT,
                repo_metadata TEXT
            )
        ''')
        
        # Create chat_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codebase_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (codebase_id) REFERENCES codebases (id)
            )
        ''')
        
        # Migrate existing database if needed
        self._migrate_database(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_database(self, cursor):
        """Migrate existing database to support new columns."""
        try:
            # Check if storage_mode column exists
            cursor.execute("PRAGMA table_info(codebases)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'storage_mode' not in columns:
                cursor.execute("ALTER TABLE codebases ADD COLUMN storage_mode TEXT DEFAULT 'local'")
                print("[INFO] Added storage_mode column to database")
            
            if 'commit_hash' not in columns:
                cursor.execute("ALTER TABLE codebases ADD COLUMN commit_hash TEXT")
                print("[INFO] Added commit_hash column to database")
            
            if 'repo_metadata' not in columns:
                cursor.execute("ALTER TABLE codebases ADD COLUMN repo_metadata TEXT")
                print("[INFO] Added repo_metadata column to database")
                
            # Make local_path nullable for temporary storage mode
            # SQLite doesn't support modifying column constraints directly,
            # but NULL is allowed by default, so existing data will work
            
        except Exception as e:
            print(f"[WARNING] Database migration error: {e}")
    
    def add_codebase(self, name: str, repo_url: str, local_path: str = None, description: str = "", 
                     storage_mode: str = "local", commit_hash: str = None, repo_metadata: str = None) -> int:
        """Add a new codebase to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO codebases (name, repo_url, local_path, storage_mode, description, commit_hash, repo_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, repo_url, local_path, storage_mode, description, commit_hash, repo_metadata))
            
            codebase_id = cursor.lastrowid
            conn.commit()
            return codebase_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Codebase with name '{name}' already exists")
        finally:
            conn.close()
    
    def get_codebase(self, codebase_id: int) -> Optional[Dict]:
        """Get a codebase by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM codebases WHERE id = ?', (codebase_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'name': row[1], 'repo_url': row[2],
                'local_path': row[3], 'storage_mode': row[4] or 'local', 
                'description': row[5], 'created_at': row[6], 'updated_at': row[7],
                'file_count': row[8], 'chunk_count': row[9],
                'commit_hash': row[10], 'repo_metadata': row[11]
            }
        return None
    
    def get_codebase_by_name(self, name: str) -> Optional[Dict]:
        """Get a codebase by name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM codebases WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'name': row[1], 'repo_url': row[2],
                'local_path': row[3], 'storage_mode': row[4] or 'local', 
                'description': row[5], 'created_at': row[6], 'updated_at': row[7],
                'file_count': row[8], 'chunk_count': row[9],
                'commit_hash': row[10], 'repo_metadata': row[11]
            }
        return None
    
    def list_codebases(self) -> List[Dict]:
        """List all codebases."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM codebases ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        codebases = []
        for row in rows:
            codebases.append({
                'id': row[0], 'name': row[1], 'repo_url': row[2],
                'local_path': row[3], 'storage_mode': row[4] or 'local', 
                'description': row[5], 'created_at': row[6], 'updated_at': row[7],
                'file_count': row[8], 'chunk_count': row[9],
                'commit_hash': row[10], 'repo_metadata': row[11]
            })
        
        return codebases
    
    def update_codebase_stats(self, codebase_id: int, file_count: int, chunk_count: int):
        """Update file and chunk counts for a codebase."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE codebases 
            SET file_count = ?, chunk_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (file_count, chunk_count, codebase_id))
        
        conn.commit()
        conn.close()
    
    def delete_codebase(self, codebase_id: int):
        """Delete a codebase and its chat history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete chat history first (foreign key constraint)
        cursor.execute('DELETE FROM chat_history WHERE codebase_id = ?', (codebase_id,))
        
        # Delete codebase
        cursor.execute('DELETE FROM codebases WHERE id = ?', (codebase_id,))
        
        conn.commit()
        conn.close()
    
    def add_chat_entry(self, codebase_id: int, question: str, answer: str):
        """Add a chat entry to the history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history (codebase_id, question, answer)
            VALUES (?, ?, ?)
        ''', (codebase_id, question, answer))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, codebase_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a codebase."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, answer, created_at 
            FROM chat_history 
            WHERE codebase_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (codebase_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'question': row[0],
                'answer': row[1],
                'created_at': row[2]
            })
        
        return list(reversed(history))  # Return in chronological order

