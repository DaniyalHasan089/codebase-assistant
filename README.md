# 🤖 Codebase Assistant

A powerful AI-powered tool that lets you **chat with your codebases** using natural language. Simply add any Git repository and ask questions about the code - the AI will analyze the codebase and provide intelligent answers based on the actual source code.

![Codebase Assistant Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-Open%20Source-green)

## 📸 Project Showcase

### 🖥️ Main Interface
![Main Interface](screenshots/main-interface.png)
*Clean, intuitive web interface built with Streamlit - chat with your code naturally*

### 💬 AI Chat in Action
![Chat Demo](screenshots/chat-demo.png)
*Ask questions about your codebase and get intelligent, context-aware responses*

### 📚 Codebase Management
![Codebase Management](screenshots/manage-codebases.png)
*Easily add, refresh, and manage multiple repositories from the sidebar*

### 🔍 Smart Code Search
![Code Search](screenshots/code-search.png)
*Semantic search finds relevant code sections based on your natural language queries*

### 📊 Processing & Analytics
![Processing Status](screenshots/processing-status.png)
*Real-time processing status with file counts, chunks, and health indicators*

### 🎯 Query Results
![Query Results](screenshots/query-results.png)
*Detailed responses with code context and explanations from your AI assistant*

---

## ✨ Features

- 🔍 **Semantic Code Search**: Find relevant code using natural language queries
- 💬 **AI Chat Interface**: Get intelligent answers about your codebase with context
- 📚 **Multiple Codebases**: Manage and switch between different repositories seamlessly
- 📝 **Persistent Chat History**: Keep track of conversations for each codebase
- 🔄 **Auto-Refresh**: Update repositories with latest changes automatically
- 🌐 **Modern Web GUI**: Beautiful, responsive interface built with Streamlit
- 🚀 **Fast Processing**: Efficient code chunking and vector embeddings
- 📊 **Smart Analytics**: File counts, chunk statistics, and processing status
- 🔧 **Extensive File Support**: Python, JavaScript, Java, C++, Go, Jupyter notebooks, Markdown, and 30+ file types

## 🎯 Use Cases

- **Code Understanding**: "What does this codebase do?"
- **Architecture Analysis**: "How is this application structured?"
- **Getting Started**: "How do I run this project?"
- **Feature Location**: "Where is the authentication implemented?"
- **Documentation**: "What are the main classes and their purposes?"
- **Dependencies**: "What libraries does this project use?"
- **Best Practices**: "What design patterns are used here?"

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+** ([Download Python](https://python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **OpenRouter API Key** ([Get free API key](https://openrouter.ai))

### Quick Start (3 Steps)

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd codebase-assistant
   ```

2. **Create environment file**:
   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
   ```

3. **Launch the application**:
   ```bash
   python run_gui.py
   ```
   
   This will:
   - ✅ Install all dependencies automatically
   - ✅ Start the web interface
   - ✅ Open your browser to `http://localhost:8501`

### Manual Installation

If you prefer manual setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the GUI
streamlit run gui_app.py

# Or use the launcher
python run_gui.py
```

## 🚀 Getting Started

### Adding Your First Codebase

1. **Open the web interface** at `http://localhost:8501`
2. **In the sidebar**, click the "➕ Add" tab
3. **Fill out the form**:
   - **Name**: Give your codebase a memorable name
   - **Repository URL**: Any public Git repository URL
   - **Description**: Optional brief description
4. **Click "Add Codebase"** and wait for processing
5. **Start chatting** once the green "✅ Ready" status appears!

### Example Repositories to Try

- `https://github.com/karpathy/micrograd` - Simple neural network library
- `https://github.com/pallets/flask` - Python web framework
- `https://github.com/facebook/react` - JavaScript UI library
- Any of your own repositories!

### Sample Questions

**Understanding the Code**:
- "What does this codebase do?"
- "Can you explain the main architecture?"
- "What's the purpose of the main classes?"

**Getting Started**:
- "How do I install and run this project?"
- "What are the dependencies?"
- "Where is the main entry point?"

**Deep Dive**:
- "How does the authentication system work?"
- "Show me the database models"
- "What design patterns are implemented?"

## 📱 User Interface Guide

### Sidebar Navigation

**📋 List Tab**:
- View all your codebases
- See status indicators (Active/Inactive)
- Quick stats (file count, chunk count)
- One-click switching between codebases

**➕ Add Tab**:
- Add new repositories
- Form validation and error handling
- Automatic processing and indexing

**⚙️ Manage Tab**:
- Refresh codebases with latest changes
- View detailed statistics
- Delete codebases (with confirmation)

### Main Chat Interface

**Status Dashboard**:
- File count and processing status
- Chunk count for search optimization
- Quick refresh button for problematic repos

**Chat History**:
- Persistent conversation history per codebase
- Clean, readable message format
- Automatic scrolling and timestamps

**Question Input**:
- Natural language query interface
- Real-time processing indicators
- Form validation and error handling

## 🔧 Advanced Configuration

### Supported File Types

**Programming Languages**:
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`)
- Go (`.go`)
- Rust (`.rs`)
- PHP (`.php`)
- Ruby (`.rb`)
- C# (`.cs`)
- Kotlin (`.kt`)
- Swift (`.swift`)
- Scala (`.scala`)
- R (`.r`)

**Documentation & Config**:
- Markdown (`.md`)
- reStructuredText (`.rst`)
- Plain text (`.txt`)
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)
- XML (`.xml`)
- HTML/CSS (`.html`, `.css`)

**Special Files**:
- Jupyter Notebooks (`.ipynb`) - Full cell extraction
- Shell scripts (`.sh`, `.bat`)
- SQL files (`.sql`)

### Configuration Options

Edit `config.py` to customize:

```python
# Code chunking settings
CHUNK_SIZE = 40        # Lines per chunk
CHUNK_OVERLAP = 10     # Overlap between chunks

# Database location
DB_DIR = "vector_db"   # Vector storage directory
```

### AI Model Configuration

Modify the AI model in `codebase_manager.py`:

```python
# Available models on OpenRouter
"model": "deepseek/deepseek-chat",           # Fast and free
"model": "anthropic/claude-3-sonnet",       # High quality
"model": "openai/gpt-4-turbo",              # OpenAI's latest
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit GUI │    │  Codebase        │    │  Multi-Embedding│
│   (gui_app.py)  │────│  Manager         │────│  Store          │
│                 │    │  (codebase_      │    │  (multi_        │
└─────────────────┘    │   manager.py)    │    │   embedding_    │
                       └──────────────────┘    │   store.py)     │
                                ↓              └─────────────────┘
                       ┌──────────────────┐              ↓
                       │  Repository      │    ┌─────────────────┐
                       │  Loader          │    │  ChromaDB       │
                       │  (repo_loader.py)│    │  Vector Storage │
                       └──────────────────┘    └─────────────────┘
                                ↓
                       ┌──────────────────┐
                       │  SQLite Database │
                       │  (database.py)   │
                       └──────────────────┘
```

### Data Flow

1. **Repository Ingestion**: Clone Git repos and extract source files
2. **Content Processing**: Parse files (including Jupyter notebooks)
3. **Code Chunking**: Split content into manageable, overlapping chunks
4. **Vector Embedding**: Generate semantic embeddings for each chunk
5. **Storage**: Store in ChromaDB with metadata in SQLite
6. **Query Processing**: Semantic search + AI response generation
7. **Response Delivery**: Formatted answers with source context

## 🗂️ Project Structure

```
codebase-assistant/
├── 📱 Frontend & UI
│   ├── gui_app.py              # Main Streamlit application
│   └── run_gui.py              # Launcher script with setup
│
├── 🧠 Core Logic
│   ├── codebase_manager.py     # Main orchestration logic
│   ├── database.py             # SQLite operations
│   └── multi_embedding_store.py # Vector embedding management
│
├── 🔧 Processing Pipeline
│   ├── repo_loader.py          # Git repository handling
│   ├── chunking.py             # Code chunking logic
│   └── config.py               # Configuration settings
│
├── 📄 Documentation & Config
│   ├── README.md               # This comprehensive guide
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables (you create)
│
└── 💾 Generated Data (auto-created)
    ├── repos/                  # Cloned repositories
    ├── vector_db/              # ChromaDB storage
    └── codebases.db           # SQLite database
```

## 🐛 Troubleshooting

### Common Issues & Solutions

**❌ "No auth credentials found"**
```bash
# Solution: Check your .env file
cat .env  # Should show: OPENROUTER_API_KEY=sk-or-v1-...
```

**❌ "Repository not found"**
- ✅ Verify the Git URL is correct and publicly accessible
- ✅ For private repos, ensure you have proper access credentials
- ✅ Try cloning manually: `git clone <url>` to test access

**❌ "No source files found"**
- ✅ Repository might contain only binary/image files
- ✅ Use the "🔄 Refresh" button in the GUI
- ✅ Check supported file types in the configuration section

**❌ GUI won't start**
```bash
# Solution: Manual dependency installation
pip install streamlit pandas requests chromadb gitpython python-dotenv

# Then try starting again
streamlit run gui_app.py
```

**❌ Python not found**
- ✅ Ensure Python 3.8+ is installed and in PATH
- ✅ Try using full Python path: `C:/Users/.../python.exe`
- ✅ On Windows, disable app execution aliases for Python

### Performance Optimization

**Large Repositories** (1000+ files):
- Initial processing may take 2-5 minutes
- Consider using `.gitignore` patterns to exclude unnecessary files
- Monitor memory usage during processing

**Slow Responses**:
- First query per session initializes the embedding store
- Subsequent queries should be much faster
- Large context queries may take longer to process

**Memory Usage**:
- Each codebase uses separate vector storage (~10-50MB per project)
- Consider cleaning up unused codebases periodically
- ChromaDB automatically optimizes storage

## 🔒 Privacy & Security

- **Local Processing**: All code analysis happens on your machine
- **API Usage**: Only processed chunks (not full code) sent to OpenRouter
- **Data Storage**: All data stored locally in SQLite + ChromaDB
- **No Telemetry**: No usage data collected or transmitted

## 📈 Roadmap & Future Features

### Planned Enhancements
- 🔄 **Better Embeddings**: Integration with local embedding models
- 🌐 **Multi-language Support**: Enhanced support for more programming languages
- 📊 **Analytics Dashboard**: Code complexity analysis and insights
- 🔗 **IDE Integration**: VS Code and other editor plugins
- 🤝 **Team Features**: Shared codebases and collaborative analysis
- 🚀 **Performance**: Faster processing and reduced memory usage

### Contributing

We welcome contributions! Areas where you can help:

- **File Type Support**: Add parsers for new programming languages
- **UI/UX**: Improve the interface and user experience  
- **Performance**: Optimize embedding generation and storage
- **Documentation**: Improve guides and add tutorials
- **Testing**: Add unit tests and integration tests

## 📝 License & Credits

This project is **open source** and available under the MIT License.

### Built With
- **[Streamlit](https://streamlit.io/)** - Web interface framework
- **[ChromaDB](https://www.trychroma.com/)** - Vector database
- **[OpenRouter](https://openrouter.ai/)** - AI model API
- **[GitPython](https://gitpython.readthedocs.io/)** - Git repository handling

### Acknowledgments
- Inspired by the need for better code understanding tools
- Thanks to the open-source community for the amazing libraries
- Special thanks to early users and contributors

---

## 🚀 Get Started Now!

Ready to chat with your code? Let's get started:

```bash
# 1. Get your OpenRouter API key (free): https://openrouter.ai
# 2. Clone this repo and navigate to it
# 3. Create .env file with your API key
# 4. Run the launcher:
python run_gui.py
```

**Questions? Issues? Feedback?** 

- 📧 Open an issue on GitHub
- 💬 Join our community discussions
- 🌟 Star the repo if you find it useful!

---

**Happy coding! 🎉 Transform how you understand and work with code today!**
