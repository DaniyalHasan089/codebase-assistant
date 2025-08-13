# config.py

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "vector_db")

# Chunk settings
CHUNK_SIZE = 40  # lines
CHUNK_OVERLAP = 10

# OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("Please set the OPENROUTER_API_KEY environment variable.")

# Available AI Models (Free on OpenRouter)
AVAILABLE_MODELS = {
    "deepseek/deepseek-chat": {
        "name": "DeepSeek Chat",
        "description": "Fast and capable model, good for code analysis (Free)",
        "provider": "DeepSeek",
        "free": True
    },
    "mistralai/mistral-7b-instruct": {
        "name": "Mistral 7B Instruct",
        "description": "Efficient open-source model (Free)",
        "provider": "Mistral AI",
        "free": True
    },
    "mistralai/mixtral-8x7b-instruct": {
        "name": "Mixtral 8x7B Instruct", 
        "description": "More powerful Mistral model (Free)",
        "provider": "Mistral AI",
        "free": True
    },
    "meta-llama/llama-3-8b-instruct": {
        "name": "Llama 3 8B Instruct",
        "description": "Meta's efficient instruction-following model (Free)",
        "provider": "Meta",
        "free": True
    },
    "openchat/openchat-3.5-0106": {
        "name": "OpenChat 3.5",
        "description": "Open-source conversational AI model (Free)",
        "provider": "OpenChat",
        "free": True
    },
    "nousresearch/nous-capybara-7b": {
        "name": "Nous Capybara 7B",
        "description": "Fine-tuned model for conversations (Free)",
        "provider": "Nous Research",
        "free": True
    },
    "gryphe/mythomax-l2-13b": {
        "name": "MythoMax L2 13B",
        "description": "Creative and versatile model (Free)",
        "provider": "Gryphe",
        "free": True
    },
    "openrouter/auto": {
        "name": "Auto (Best Free)",
        "description": "Automatically selects the best available free model",
        "provider": "OpenRouter",
        "free": True
    }
}

# Default model
DEFAULT_MODEL = "deepseek/deepseek-chat"

# Storage modes
STORAGE_MODE_LOCAL = "local"        # Keep repositories on disk (current behavior)
STORAGE_MODE_TEMP = "temporary"     # Process and delete repositories immediately
DEFAULT_STORAGE_MODE = STORAGE_MODE_LOCAL
