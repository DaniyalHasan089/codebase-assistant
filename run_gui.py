#!/usr/bin/env python3
# run_gui.py

import subprocess
import sys
import os

def install_requirements():
    """Install required packages."""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        sys.exit(1)

def run_streamlit():
    """Run the Streamlit GUI."""
    print("Starting Codebase Assistant GUI...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "gui_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error running GUI: {e}")

if __name__ == "__main__":
    print("🤖 Codebase Assistant Setup")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create a .env file with your OPENROUTER_API_KEY")
        sys.exit(1)
    
    # Install requirements
    install_requirements()
    
    print("\n🚀 Starting GUI...")
    print("The web interface will open in your browser.")
    print("If it doesn't open automatically, go to: http://localhost:8501")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 40)
    
    # Run the GUI
    run_streamlit()


