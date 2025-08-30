#!/bin/bash
# Multi-GPU Setup Script for GTX 1660 Super Integration
# Run this after installing the GTX 1660 Super

set -e

echo "🚀 Setting up Multi-GPU AI Architecture..."

# Check GPU detection
echo "📡 Detecting GPUs..."
nvidia-smi --list-gpus

# Pull required models
echo "📥 Pulling AI models..."

# Leonardo (Mistral 7B Q5_K_M) for RTX 3060 Ti (primary reasoning)
echo "  • Pulling Leonardo (Mistral 7B Q5_K_M)..."
docker exec ollama ollama pull mistral:7b-instruct-q5_k_m

# Jarvis (Phi3 Q4_0) for GTX 1660 Super (chat + TTS)
echo "  • Pulling Jarvis (Phi3 Q4_0)..."
docker exec ollama ollama pull phi3:3.8b-mini-4k-instruct-q4_0

# Verify models are available
echo "✅ Verifying model installation..."
docker exec ollama ollama list

# Test GPU assignments
echo "🧪 Testing GPU assignments..."

# Test Leonardo (Mistral) on primary GPU
echo "  • Testing Leonardo (Mistral 7B) reasoning capabilities..."
docker exec ollama ollama run mistral:7b-instruct-q5_k_m "Leonardo, what is the difference between machine learning and deep learning?" --verbose

# Test Jarvis (Phi3) on secondary GPU  
echo "  • Testing Jarvis (Phi3) chat interface..."
docker exec ollama ollama run phi3:3.8b-mini-4k-instruct-q4_0 "Jarvis, introduce yourself and explain your role." --verbose

# Check GPU memory usage
echo "📊 GPU Memory Status:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits

echo "🎉 Multi-GPU setup complete!"
echo ""
echo "🎭 AI Personalities:"
echo "  🧠 Leonardo (RTX 3060 Ti)  → Mistral 7B Q5_K_M (analytical reasoning)"
echo "  🤖 Jarvis (GTX 1660 Super) → Phi3 Q4_0 (conversational chat + TTS)"
echo ""
echo "Next steps:"
echo "  1. Update backend routing to use 'leonardo' and 'jarvis' endpoints"
echo "  2. Configure TTS pipeline on Jarvis"
echo "  3. Test frontend with new named backend options"
