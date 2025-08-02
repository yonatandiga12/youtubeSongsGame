#!/usr/bin/env python3
"""
Test script to verify all dependencies work correctly
"""

def test_imports():
    """Test that all required packages can be imported"""
    try:
        import streamlit
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ streamlit import failed: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ openai import failed: {e}")
        return False
    
    try:
        from youtubesearchpython import VideosSearch
        print("✅ youtube-search-python imported successfully")
    except ImportError as e:
        print(f"❌ youtube-search-python import failed: {e}")
        return False
    

    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without API calls"""
    try:
        from youtubesearchpython import VideosSearch
        search = VideosSearch("test", limit=1)
        print("✅ YouTube search functionality works")
        return True
    except Exception as e:
        print(f"❌ YouTube search test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing YouTube Video Game Dependencies")
    print("=" * 50)
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    print("=" * 50)
    if imports_ok and functionality_ok:
        print("🎉 All tests passed! Your app should work correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.") 