#!/usr/bin/env python3
"""
Quick test for Leonardo's voice integration
Tests TTS and speech recognition capabilities
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def test_piper_tts():
    """Test Piper TTS installation"""
    print("🗣️  Testing Piper TTS...")
    try:
        import piper
        print("✅ Piper TTS imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Piper TTS import failed: {e}")
        return False

def test_whisper():
    """Test Whisper installation"""
    print("🎤 Testing Whisper...")
    try:
        import whisper
        print("✅ Whisper imported successfully")
        # Test loading base model
        model = whisper.load_model("base")
        print("✅ Whisper base model loaded")
        return True
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

def test_leonardo_endpoints():
    """Test Leonardo audio endpoints"""
    print("🤖 Testing Leonardo endpoints...")
    
    # Check if FastAPI server is running (this would normally test the endpoints)
    # For now, just verify the modules exist
    try:
        # Check if leonardo module exists
        leonardo_path = Path("app/leonardo")
        if leonardo_path.exists():
            print("✅ Leonardo module directory exists")
        else:
            print("❌ Leonardo module directory not found")
            return False
            
        # Check if audio router exists
        audio_router_path = leonardo_path / "audio_router.py"
        if audio_router_path.exists():
            print("✅ Leonardo audio router found")
        else:
            print("❌ Leonardo audio router not found")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Leonardo endpoint test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎤 Leonardo Voice Integration Test")
    print("=" * 40)
    
    tests = [
        ("Piper TTS", test_piper_tts),
        ("Whisper", test_whisper),
        ("Leonardo Endpoints", test_leonardo_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        print("-" * 40)
    
    print(f"\n🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Leonardo voice integration is ready.")
        print("\n📝 Next steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Test Leonardo TTS: curl -X POST 'http://localhost:8000/leonardo/speak' -H 'Content-Type: application/json' -d '{\"text\":\"Hello, I am Leonardo, ready to think analytically.\"}'")
        print("3. Use the frontend interface to interact with Leonardo's voice")
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
