#!/bin/bash
# Mira Avatar Setup Script
# Prepares 3D avatar integration for Jarvis

set -e

echo "🤖 Mira Avatar Setup"
echo "===================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
AVATAR_DIR="$WORKSPACE_ROOT/app/static/avatars/mira"
FRONTEND_DIR="$WORKSPACE_ROOT/frontend/dashboard"

# Create avatar directory structure
echo "📁 Creating avatar directory structure..."
mkdir -p "$AVATAR_DIR"
mkdir -p "$FRONTEND_DIR/src/components/avatar"
mkdir -p "$FRONTEND_DIR/public/avatars/mira"

# Check if Mira assets are available
echo "🔍 Checking for Mira 3D assets..."
MIRA_SOURCE=""

# Common locations to check for Mira assets
POTENTIAL_SOURCES=(
    "/home/cgbowen/Downloads/meet-mira"
    "/tmp/meet-mira"
    "$WORKSPACE_ROOT/assets/mira"
    "./meet-mira"
)

for source in "${POTENTIAL_SOURCES[@]}"; do
    if [ -d "$source" ] && [ -f "$source/sharable-bot.glb" ]; then
        MIRA_SOURCE="$source"
        echo "✅ Found Mira assets at: $MIRA_SOURCE"
        break
    fi
done

if [ -z "$MIRA_SOURCE" ]; then
    echo "⚠️  Mira assets not found in common locations"
    echo "📋 Please ensure the following files are available:"
    echo "   - sharable-bot.glb (main 3D model)"
    echo "   - Ucupaint baked Color_1.png (color texture)"
    echo "   - Ucupaint baked Normal_0.png (normal map)"
    echo "   - Ucupaint baked Metallic-Roughness texture"
    echo "   - internal_ground_ao_texture.jpeg (ambient occlusion)"
    echo ""
    echo "🎯 Manual setup required:"
    echo "   1. Copy Mira assets to: $AVATAR_DIR"
    echo "   2. Run this script again after assets are in place"
else
    # Copy Mira assets
    echo "📦 Copying Mira assets..."
    cp -r "$MIRA_SOURCE"/* "$AVATAR_DIR/"
    cp -r "$MIRA_SOURCE"/* "$FRONTEND_DIR/public/avatars/mira/"
    echo "✅ Mira assets copied successfully"
fi

# Install Three.js dependencies for avatar rendering
echo "📦 Installing Three.js dependencies..."
cd "$FRONTEND_DIR"
npm install three @types/three --save

# Create Mira Avatar React component
echo "⚛️  Creating Mira Avatar component..."
cat > "$FRONTEND_DIR/src/components/avatar/MiraAvatar.tsx" << 'EOF'
import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

interface MiraAvatarProps {
  isVisible?: boolean;
  isSpeaking?: boolean;
  emotion?: 'neutral' | 'happy' | 'thinking' | 'helpful' | 'explaining';
  size?: 'small' | 'medium' | 'large';
}

const MiraAvatar: React.FC<MiraAvatarProps> = ({
  isVisible = true,
  isSpeaking = false,
  emotion = 'neutral',
  size = 'medium'
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const modelRef = useRef<THREE.Object3D>();
  const mixerRef = useRef<THREE.AnimationMixer>();
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sizeMap = {
    small: { width: 200, height: 200 },
    medium: { width: 300, height: 300 },
    large: { width: 400, height: 400 }
  };

  useEffect(() => {
    if (!mountRef.current) return;

    const { width, height } = sizeMap[size];

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = null; // Transparent background
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 0, 2);

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Lighting setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Load Mira model
    const loader = new GLTFLoader();
    loader.load(
      '/avatars/mira/sharable-bot.glb',
      (gltf) => {
        const model = gltf.scene;
        
        // Scale and position the model
        model.scale.setScalar(1);
        model.position.set(0, -0.5, 0);
        
        // Enable shadows
        model.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });

        scene.add(model);
        modelRef.current = model;

        // Setup animation mixer if animations exist
        if (gltf.animations && gltf.animations.length > 0) {
          const mixer = new THREE.AnimationMixer(model);
          mixerRef.current = mixer;
          
          // Play idle animation if available
          const idleAnimation = gltf.animations.find(clip => 
            clip.name.toLowerCase().includes('idle')
          );
          if (idleAnimation) {
            const action = mixer.clipAction(idleAnimation);
            action.play();
          }
        }

        setIsLoaded(true);
      },
      (progress) => {
        console.log('Mira loading progress:', progress);
      },
      (error) => {
        console.error('Error loading Mira:', error);
        setError('Failed to load Mira avatar');
      }
    );

    // Add renderer to DOM
    mountRef.current.appendChild(renderer.domElement);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      
      if (mixerRef.current) {
        mixerRef.current.update(0.016); // ~60fps
      }
      
      // Subtle rotation for idle state
      if (modelRef.current && !isSpeaking) {
        modelRef.current.rotation.y += 0.005;
      }
      
      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [size]);

  // Handle speaking animation
  useEffect(() => {
    if (!modelRef.current || !mixerRef.current) return;

    if (isSpeaking) {
      // Add speaking animation/lip sync here
      console.log('Mira is speaking');
    } else {
      // Return to idle state
      console.log('Mira stopped speaking');
    }
  }, [isSpeaking]);

  // Handle emotion changes
  useEffect(() => {
    if (!modelRef.current) return;

    // Implement emotion-based facial expressions
    switch (emotion) {
      case 'happy':
        // Trigger happy expression animation
        break;
      case 'thinking':
        // Trigger thinking expression
        break;
      case 'helpful':
        // Trigger helpful/encouraging expression
        break;
      case 'explaining':
        // Trigger teaching/explaining expression
        break;
      default:
        // Neutral expression
        break;
    }
  }, [emotion]);

  if (!isVisible) return null;

  return (
    <div className="mira-avatar-container" style={{ position: 'relative' }}>
      <div 
        ref={mountRef} 
        style={{ 
          borderRadius: '12px',
          overflow: 'hidden',
          backgroundColor: 'transparent'
        }} 
      />
      
      {!isLoaded && !error && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#ffffff',
          textAlign: 'center'
        }}>
          🤖 Loading Mira...
        </div>
      )}
      
      {error && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#ff6b6b',
          textAlign: 'center',
          fontSize: '14px'
        }}>
          ⚠️ {error}
        </div>
      )}
      
      {isLoaded && (
        <div style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          {isSpeaking ? '🎤 Speaking' : '💭 Listening'}
        </div>
      )}
    </div>
  );
};

export default MiraAvatar;
EOF

# Update the main GemmaPhi component to include Mira
echo "🔧 Creating Mira integration example..."
cat > "$FRONTEND_DIR/src/components/avatar/MiraIntegration.tsx" << 'EOF'
import React, { useState, useEffect } from 'react';
import MiraAvatar from './MiraAvatar';

interface MiraIntegrationProps {
  isJarvisMode?: boolean;
  currentMessage?: string;
  isSpeaking?: boolean;
}

const MiraIntegration: React.FC<MiraIntegrationProps> = ({
  isJarvisMode = false,
  currentMessage = '',
  isSpeaking = false
}) => {
  const [emotion, setEmotion] = useState<'neutral' | 'happy' | 'thinking' | 'helpful' | 'explaining'>('neutral');

  // Analyze message content to determine appropriate emotion
  useEffect(() => {
    if (!currentMessage) {
      setEmotion('neutral');
      return;
    }

    const message = currentMessage.toLowerCase();
    
    if (message.includes('help') || message.includes('assist')) {
      setEmotion('helpful');
    } else if (message.includes('explain') || message.includes('teach')) {
      setEmotion('explaining');
    } else if (message.includes('think') || message.includes('analyze')) {
      setEmotion('thinking');
    } else if (message.includes('great') || message.includes('excellent') || message.includes('wonderful')) {
      setEmotion('happy');
    } else {
      setEmotion('neutral');
    }
  }, [currentMessage]);

  if (!isJarvisMode) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      zIndex: 1000,
      background: 'rgba(0,0,0,0.1)',
      borderRadius: '16px',
      padding: '10px',
      backdropFilter: 'blur(10px)'
    }}>
      <MiraAvatar
        isVisible={true}
        isSpeaking={isSpeaking}
        emotion={emotion}
        size="medium"
      />
      <div style={{
        textAlign: 'center',
        marginTop: '8px',
        color: '#ffffff',
        fontSize: '14px',
        fontWeight: 'bold',
        textShadow: '0 1px 2px rgba(0,0,0,0.5)'
      }}>
        Jarvis (Mira)
      </div>
    </div>
  );
};

export default MiraIntegration;
EOF

# Create avatar management utilities
echo "🛠️  Creating avatar utilities..."
cat > "$FRONTEND_DIR/src/utils/avatarSync.ts" << 'EOF'
// Avatar synchronization utilities for Mira + Jarvis integration

export interface AvatarState {
  isVisible: boolean;
  isSpeaking: boolean;
  emotion: 'neutral' | 'happy' | 'thinking' | 'helpful' | 'explaining';
  currentText?: string;
}

export class MiraController {
  private avatarState: AvatarState = {
    isVisible: true,
    isSpeaking: false,
    emotion: 'neutral'
  };

  private listeners: Array<(state: AvatarState) => void> = [];

  // Subscribe to avatar state changes
  subscribe(callback: (state: AvatarState) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  // Update avatar state and notify listeners
  private updateState(newState: Partial<AvatarState>) {
    this.avatarState = { ...this.avatarState, ...newState };
    this.listeners.forEach(listener => listener(this.avatarState));
  }

  // Start speaking animation with TTS integration
  startSpeaking(text: string) {
    this.updateState({
      isSpeaking: true,
      currentText: text,
      emotion: this.determineEmotion(text)
    });
  }

  // Stop speaking animation
  stopSpeaking() {
    this.updateState({
      isSpeaking: false,
      currentText: undefined,
      emotion: 'neutral'
    });
  }

  // Manually set emotion
  setEmotion(emotion: AvatarState['emotion']) {
    this.updateState({ emotion });
  }

  // Show/hide avatar
  setVisible(isVisible: boolean) {
    this.updateState({ isVisible });
  }

  // Analyze text to determine appropriate emotion
  private determineEmotion(text: string): AvatarState['emotion'] {
    const lowerText = text.toLowerCase();
    
    if (lowerText.includes('help') || lowerText.includes('assist') || lowerText.includes('support')) {
      return 'helpful';
    }
    
    if (lowerText.includes('explain') || lowerText.includes('teach') || lowerText.includes('learn')) {
      return 'explaining';
    }
    
    if (lowerText.includes('think') || lowerText.includes('analyze') || lowerText.includes('consider')) {
      return 'thinking';
    }
    
    if (lowerText.includes('great') || lowerText.includes('excellent') || 
        lowerText.includes('wonderful') || lowerText.includes('amazing')) {
      return 'happy';
    }
    
    return 'neutral';
  }

  // Get current state
  getState(): AvatarState {
    return { ...this.avatarState };
  }
}

// Global Mira controller instance
export const miraController = new MiraController();

// TTS integration helper
export async function speakWithMira(text: string, voice: string = 'jarvis') {
  try {
    // Start avatar speaking animation
    miraController.startSpeaking(text);
    
    // Make TTS request
    const response = await fetch('/audio/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice, format: 'base64' })
    });
    
    const data = await response.json();
    const audioBase64 = data.audio_base64 || data.audio_b64;
    
    if (audioBase64) {
      const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
      
      // Stop avatar animation when audio ends
      audio.addEventListener('ended', () => {
        miraController.stopSpeaking();
      });
      
      // Play audio
      await audio.play();
    }
  } catch (error) {
    console.error('Error with Mira TTS:', error);
    miraController.stopSpeaking();
  }
}
EOF

echo ""
echo "✅ Mira Avatar Setup Complete!"
echo ""
echo "📁 Created components:"
echo "   - MiraAvatar.tsx (3D avatar component)"
echo "   - MiraIntegration.tsx (integration with chat)"
echo "   - avatarSync.ts (TTS synchronization utilities)"
echo ""
echo "📦 Installed dependencies:"
echo "   - three.js for 3D rendering"
echo "   - GLTFLoader for model loading"
echo ""
echo "🎯 Next steps:"
if [ -z "$MIRA_SOURCE" ]; then
    echo "   1. Copy Mira 3D assets to:"
    echo "      $AVATAR_DIR"
    echo "      $FRONTEND_DIR/public/avatars/mira/"
else
    echo "   1. ✅ Mira assets already copied"
fi
echo "   2. Import MiraIntegration into GemmaPhi.tsx"
echo "   3. Configure Jarvis backend routing"
echo "   4. Test avatar rendering and TTS integration"
echo ""
echo "🤖 Mira is ready to become the face of Jarvis!"
