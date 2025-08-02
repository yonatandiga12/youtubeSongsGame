#!/usr/bin/env python3
"""
YouTube Video Game - Launcher Script
This script checks dependencies and launches the Streamlit app.
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'openai',
        'youtube-search-python',
        'python-dotenv',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Installing missing packages...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run:")
            print("   pip install -r requirements.txt")
            return False
    
    return True

def main():
    """Main launcher function"""
    print("🎵 YouTube Video Game Launcher")
    print("=" * 40)
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ app.py not found in current directory!")
        print("Please run this script from the project root directory.")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    print("\n🚀 Starting YouTube Video Game...")
    print("📱 The app will open in your browser at http://localhost:8501")
    print("🔄 Press Ctrl+C to stop the app")
    print("=" * 40)
    
    try:
        # Run the Streamlit app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Thanks for playing! Goodbye!")
    except Exception as e:
        print(f"❌ Error running the app: {e}")

if __name__ == "__main__":
    main() 