#!/bin/bash
# Leonardo TTS & Whisper Integration Setup
# Connects Mistral 7B with voice capabilities

set -e

echo "🎤 Leonardo Voice Integration Setup"
echo "=================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$WORKSPACE_ROOT/.venv"

# Activate virtual environment
echo "🐍 Activating Python environment..."
source "$VENV_PATH/bin/activate"

# Install TTS dependencies
echo "📦 Installing Piper TTS for Leonardo..."
pip install --quiet piper-tts

# Install Whisper for speech recognition
echo "🎙️  Installing Whisper for speech recognition..."
pip install --quiet openai-whisper

# Download Piper voice models for Leonardo
echo "🗣️  Setting up Leonardo voice models..."
PIPER_MODELS_DIR="$HOME/.local/share/piper"
mkdir -p "$PIPER_MODELS_DIR"

# Download analytical voice models
echo "   Downloading analytical voice models..."
cd "$PIPER_MODELS_DIR"

# British English (analytical tone)
if [ ! -f "en_GB-northern_english_male-medium.onnx" ]; then
    echo "   📥 Downloading British analytical voice..."
    wget -q "https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-gb-northern_english_male-medium.tar.gz"
    tar -xzf "voice-en-gb-northern_english_male-medium.tar.gz"
    rm "voice-en-gb-northern_english_male-medium.tar.gz"
fi

# US English (clear analytical)
if [ ! -f "en_US-lessac-medium.onnx" ]; then
    echo "   📥 Downloading US analytical voice..."
    wget -q "https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-lessac-medium.tar.gz"
    tar -xzf "voice-en-us-lessac-medium.tar.gz"
    rm "voice-en-us-lessac-medium.tar.gz"
fi

cd "$WORKSPACE_ROOT"

# Test Piper installation
echo "🧪 Testing Piper TTS..."
echo "Leonardo analytical test" | piper --model en_GB-northern_english_male-medium --output_file test_leonardo.wav
if [ -f "test_leonardo.wav" ]; then
    echo "✅ Piper TTS working correctly"
    rm test_leonardo.wav
else
    echo "❌ Piper TTS test failed"
    exit 1
fi

# Test Whisper installation
echo "🧪 Testing Whisper..."
if command -v whisper &> /dev/null; then
    echo "✅ Whisper CLI available"
else
    echo "❌ Whisper CLI not found"
    exit 1
fi

# Download Whisper base model
echo "📥 Downloading Whisper base model..."
python -c "import whisper; whisper.load_model('base')"

# Create Leonardo TTS configuration
echo "⚙️  Creating Leonardo TTS configuration..."
cat > "$WORKSPACE_ROOT/leonardo_tts_config.json" << EOF
{
  "leonardo_voices": {
    "analytical": {
      "model": "en_GB-northern_english_male-medium",
      "description": "Clear, thoughtful British accent for analytical responses"
    },
    "teaching": {
      "model": "en_US-amy-medium", 
      "description": "Warm, encouraging voice for educational content"
    },
    "explaining": {
      "model": "en_US-lessac-medium",
      "description": "Clear, precise voice for explanations"
    },
    "encouraging": {
      "model": "en_GB-alba-medium",
      "description": "Supportive British voice for motivation"
    }
  },
  "whisper_config": {
    "model": "base",
    "language": "en",
    "temperature": 0.0
  },
  "leonardo_personality": {
    "default_voice": "analytical",
    "speaking_pace": "measured",
    "tone": "thoughtful",
    "characteristics": [
      "Analytical thinking",
      "Educational focus", 
      "Patient explanations",
      "Encouraging guidance"
    ]
  }
}
EOF

# Test Leonardo backend connectivity
echo "🔗 Testing Leonardo backend connectivity..."
cd "$WORKSPACE_ROOT"
python -c "
import requests
import json

try:
    # Test Leonardo status
    response = requests.get('http://localhost:8000/leonardo/status', timeout=10)
    if response.status_code == 200:
        status = response.json()
        print('✅ Leonardo backend connected')
        print(f'   Model available: {status.get(\"leonardo_model\", False)}')
        print(f'   TTS available: {status.get(\"tts_available\", False)}')
        print(f'   Speech recognition: {status.get(\"speech_recognition\", False)}')
    else:
        print('⚠️  Leonardo backend not responding')
except Exception as e:
    print(f'⚠️  Could not connect to Leonardo backend: {e}')
    print('   Make sure the FastAPI server is running')
"

# Create Leonardo voice test script
echo "🎯 Creating Leonardo voice test script..."
cat > "$WORKSPACE_ROOT/test_leonardo_voice.py" << 'EOF'
#!/usr/bin/env python3
"""
Leonardo Voice Integration Test Script
Tests TTS and speech recognition capabilities
"""

import requests
import json
import base64
import tempfile
import os
import subprocess

def test_leonardo_tts():
    """Test Leonardo TTS generation"""
    print("🗣️  Testing Leonardo TTS...")
    
    test_text = "Hello, I am Leonardo. I am here to provide analytical thinking and educational guidance for your family."
    
    try:
        response = requests.post('http://localhost:8000/leonardo/speak', 
            json={
                "text": test_text,
                "voice": "leonardo",
                "emotion": "analytical"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('audio_base64'):
                # Save audio for testing
                audio_data = base64.b64decode(data['audio_base64'])
                with open('leonardo_test.wav', 'wb') as f:
                    f.write(audio_data)
                print("✅ Leonardo TTS working - audio saved as leonardo_test.wav")
                return True
            else:
                print("❌ No audio data received")
                return False
        else:
            print(f"❌ TTS request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ TTS test error: {e}")
        return False

def test_leonardo_analysis():
    """Test Leonardo analytical thinking"""
    print("🧠 Testing Leonardo analytical thinking...")
    
    try:
        response = requests.post('http://localhost:8000/leonardo/think',
            json={
                "query": "Explain the concept of photosynthesis to a curious child",
                "temperature": 0.3,
                "speak_response": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('text'):
                print("✅ Leonardo analytical thinking working")
                print(f"   Response length: {len(data['text'])} characters")
                print(f"   Backend: {data['metadata'].get('backend')}")
                return True
            else:
                print("❌ No text response received")
                return False
        else:
            print(f"❌ Analysis request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis test error: {e}")
        return False

def test_leonardo_combined():
    """Test Leonardo analysis with TTS"""
    print("🎤 Testing Leonardo analysis + TTS...")
    
    try:
        response = requests.post('http://localhost:8000/leonardo/analyze-and-speak',
            json={
                "query": "What makes a good teacher?",
                "temperature": 0.3,
                "speak_response": True
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('text') and data.get('audio_base64'):
                # Save combined test
                audio_data = base64.b64decode(data['audio_base64'])
                with open('leonardo_analysis.wav', 'wb') as f:
                    f.write(audio_data)
                print("✅ Leonardo combined analysis + TTS working")
                print("   Audio saved as leonardo_analysis.wav")
                return True
            else:
                print("❌ Incomplete response (missing text or audio)")
                return False
        else:
            print(f"❌ Combined request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Combined test error: {e}")
        return False

if __name__ == "__main__":
    print("🎭 Leonardo Voice Integration Test")
    print("================================")
    
    tests = [
        test_leonardo_tts,
        test_leonardo_analysis, 
        test_leonardo_combined
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All Leonardo voice tests passed!")
        print("🎯 Leonardo is ready for voice interaction")
    else:
        print("⚠️  Some tests failed - check configuration")
EOF

chmod +x "$WORKSPACE_ROOT/test_leonardo_voice.py"

# Update environment variables for Leonardo
echo "🔧 Setting up Leonardo environment variables..."
cat >> "$WORKSPACE_ROOT/.env" << EOF

# Leonardo (Mistral 7B) Configuration
LEONARDO_URL=http://localhost:11434
LEONARDO_MODEL=mistral:7b-instruct-q5_k_m

# Leonardo TTS Configuration  
LEONARDO_TTS_VOICE=en_GB-northern_english_male-medium
LEONARDO_TTS_EMOTION=analytical

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_LANGUAGE=en
EOF

echo ""
echo "✅ Leonardo Voice Integration Setup Complete!"
echo ""
echo "🎤 TTS Capabilities:"
echo "   - Analytical British voice for thoughtful responses"
echo "   - Educational tone for teaching interactions"
echo "   - Emotion-aware speech generation"
echo ""
echo "🎙️  Speech Recognition:"
echo "   - Whisper base model for speech-to-text"
echo "   - English language optimization"
echo "   - Leonardo-specific audio processing"
echo ""
echo "🧠 Integration Features:"
echo "   - /leonardo/speak - Generate TTS for any text"
echo "   - /leonardo/think - Analytical thinking with optional TTS"
echo "   - /leonardo/listen - Speech recognition for input"
echo "   - /leonardo/analyze-and-speak - Complete voice interaction"
echo ""
echo "🎯 Next steps:"
echo "   1. Start the FastAPI server: python -m app.main"
echo "   2. Test Leonardo voice: python test_leonardo_voice.py"
echo "   3. Use frontend with 'leonardo' backend and voice"
echo ""
echo "🤖 Leonardo is ready to think and speak with your family!"
