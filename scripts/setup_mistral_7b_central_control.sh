#!/bin/bash
"""
Mistral 7B Central Control Setup Script
Downloads and configures Mistral 7B model for central orchestration.
"""

set -euo pipefail

# Configuration
BASE_DIR="/home/cgbowen/AIWorkspace"
MODELS_DIR="$BASE_DIR/models/central_control"
MISTRAL_DIR="$MODELS_DIR/mistral_7b"
CONFIG_DIR="$BASE_DIR/infrastructure/configs/central_control"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git is required but not installed"
        exit 1
    fi
    
    # Check available disk space (need ~15GB for Mistral 7B)
    available_space=$(df "$BASE_DIR" | awk 'NR==2 {print $4}')
    required_space=$((15 * 1024 * 1024)) # 15GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space. Need at least 15GB, have $(( available_space / 1024 / 1024 ))GB"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install required Python packages
install_dependencies() {
    log_info "Installing required dependencies..."
    
    # Activate virtual environment if it exists
    if [ -f "$BASE_DIR/.venv/bin/activate" ]; then
        source "$BASE_DIR/.venv/bin/activate"
        log_info "Activated virtual environment"
    fi
    
    # Install required packages
    pip3 install --upgrade pip
    pip3 install huggingface-hub torch transformers accelerate sentencepiece
    
    log_success "Dependencies installed successfully"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p "$MISTRAL_DIR"
    mkdir -p "$MODELS_DIR/router_controller"
    mkdir -p "$MODELS_DIR/data_analyzer"
    mkdir -p "$MODELS_DIR/tool_director"
    mkdir -p "$BASE_DIR/app/central_control"
    mkdir -p "$BASE_DIR/fine_tuning/datasets/central_control"
    mkdir -p "$BASE_DIR/scripts/central_control"
    
    log_success "Directory structure created"
}

# Download Mistral 7B model
download_mistral_7b() {
    log_info "Downloading Mistral 7B model..."
    log_warning "This will download ~13GB of data. Please be patient..."
    
    cd "$MISTRAL_DIR"
    
    # Create download script
    cat > download_mistral.py << 'EOF'
import os
from huggingface_hub import snapshot_download
import torch

def download_mistral_7b():
    model_name = "mistralai/Mistral-7B-Instruct-v0.3"
    local_dir = "."
    
    print(f"Downloading {model_name} to {local_dir}")
    
    try:
        snapshot_download(
            repo_id=model_name,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print("✅ Model downloaded successfully")
        
        # Verify download
        required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ Missing required file: {file}")
                return False
        
        print("✅ Model verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

if __name__ == "__main__":
    success = download_mistral_7b()
    exit(0 if success else 1)
EOF
    
    # Run download
    python3 download_mistral.py
    download_status=$?
    
    # Clean up download script
    rm download_mistral.py
    
    if [ $download_status -eq 0 ]; then
        log_success "Mistral 7B model downloaded successfully"
    else
        log_error "Failed to download Mistral 7B model"
        exit 1
    fi
}

# Create central orchestrator
create_central_orchestrator() {
    log_info "Creating central orchestrator..."
    
    cat > "$BASE_DIR/app/central_control/mistral_orchestrator.py" << 'EOF'
#!/usr/bin/env python3
"""
Mistral 7B Central Orchestrator
Coordinates between tiny tool controller, domain specialists, and tools.
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class OrchestratorRequest:
    user_input: str
    context: Dict[str, Any]
    routing_hint: Optional[str] = None
    priority: str = "normal"
    
@dataclass 
class OrchestratorResponse:
    response: str
    specialist_used: str
    tools_activated: List[str]
    processing_time_ms: int
    confidence: float

class MistralOrchestrator:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/home/cgbowen/AIWorkspace/infrastructure/configs/central_control/mistral_7b_config.json"
        self.config = self._load_config()
        self.specialists = {}
        self.tools = {}
        self.router = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "model_config": {"model_name": "mistral-7b-instruct"},
            "orchestration_config": {"max_concurrent_requests": 10},
            "performance_targets": {"orchestration_latency_ms": 200}
        }
    
    async def initialize(self):
        """Initialize the orchestrator and load models."""
        print("🚀 Initializing Mistral 7B Central Orchestrator...")
        
        # Load configuration
        print(f"📋 Loaded configuration: {self.config['model_config']['model_name']}")
        
        # Initialize router (placeholder)
        print("🔀 Initializing router controller...")
        
        # Initialize specialists (placeholder)
        print("🎓 Initializing domain specialists...")
        
        # Initialize tools (placeholder)
        print("🔧 Initializing tool director...")
        
        print("✅ Mistral 7B Central Orchestrator initialized successfully")
    
    async def process_request(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process an incoming request through the orchestration pipeline."""
        start_time = time.time()
        
        # Step 1: Route the request
        routing_decision = await self._route_request(request)
        
        # Step 2: Activate appropriate specialist
        specialist_response = await self._activate_specialist(routing_decision, request)
        
        # Step 3: Coordinate tool usage
        tools_used = await self._coordinate_tools(routing_decision, specialist_response)
        
        # Step 4: Generate final response
        final_response = await self._generate_response(specialist_response, tools_used)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return OrchestratorResponse(
            response=final_response,
            specialist_used=routing_decision.get("specialist", "unknown"),
            tools_activated=tools_used,
            processing_time_ms=processing_time,
            confidence=routing_decision.get("confidence", 0.5)
        )
    
    async def _route_request(self, request: OrchestratorRequest) -> Dict[str, Any]:
        """Route request to appropriate specialist."""
        # Placeholder routing logic
        return {
            "specialist": "phi3_mathematics_tutor",
            "domain": "mathematics", 
            "confidence": 0.85,
            "tools_suggested": ["calculator", "graphing"]
        }
    
    async def _activate_specialist(self, routing: Dict[str, Any], request: OrchestratorRequest) -> str:
        """Activate the appropriate domain specialist."""
        # Placeholder specialist activation
        return f"Response from {routing['specialist']} for: {request.user_input}"
    
    async def _coordinate_tools(self, routing: Dict[str, Any], response: str) -> List[str]:
        """Coordinate tool usage based on routing and response."""
        # Placeholder tool coordination
        return routing.get("tools_suggested", [])
    
    async def _generate_response(self, specialist_response: str, tools_used: List[str]) -> str:
        """Generate final orchestrated response."""
        tools_info = f" (used tools: {', '.join(tools_used)})" if tools_used else ""
        return f"{specialist_response}{tools_info}"

# Demo usage
async def demo_orchestrator():
    orchestrator = MistralOrchestrator()
    await orchestrator.initialize()
    
    # Test request
    test_request = OrchestratorRequest(
        user_input="Help me solve 2x + 5 = 15",
        context={"session_id": "demo_001"}
    )
    
    response = await orchestrator.process_request(test_request)
    
    print(f"\n🎯 Orchestrator Demo Results:")
    print(f"   Response: {response.response}")
    print(f"   Specialist: {response.specialist_used}")
    print(f"   Tools: {response.tools_activated}")
    print(f"   Time: {response.processing_time_ms}ms")
    print(f"   Confidence: {response.confidence:.2f}")

if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
EOF
    
    log_success "Central orchestrator created"
}

# Create setup verification script
create_verification_script() {
    log_info "Creating verification script..."
    
    cat > "$BASE_DIR/scripts/central_control/verify_setup.py" << 'EOF'
#!/usr/bin/env python3
"""
Mistral 7B Central Control Setup Verification
Verifies that all components are properly installed and configured.
"""

import json
import os
from pathlib import Path

def verify_setup():
    print("🔍 Verifying Mistral 7B Central Control Setup")
    print("=" * 50)
    
    base_path = Path("/home/cgbowen/AIWorkspace")
    success_count = 0
    total_checks = 0
    
    # Check model directory
    total_checks += 1
    mistral_dir = base_path / "models" / "central_control" / "mistral_7b"
    if mistral_dir.exists() and any(mistral_dir.iterdir()):
        print("✅ Mistral 7B model directory exists and contains files")
        success_count += 1
    else:
        print("❌ Mistral 7B model directory missing or empty")
    
    # Check configuration files
    config_files = [
        "mistral_7b_config.json",
        "central_router_config.json", 
        "tool_director_config.json",
        "data_analyzer_config.json"
    ]
    
    config_dir = base_path / "infrastructure" / "configs" / "central_control"
    for config_file in config_files:
        total_checks += 1
        config_path = config_dir / config_file
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    json.load(f)
                print(f"✅ {config_file} exists and is valid JSON")
                success_count += 1
            except Exception as e:
                print(f"❌ {config_file} exists but invalid JSON: {e}")
        else:
            print(f"❌ {config_file} missing")
    
    # Check orchestrator
    total_checks += 1
    orchestrator_path = base_path / "app" / "central_control" / "mistral_orchestrator.py"
    if orchestrator_path.exists():
        print("✅ Central orchestrator created")
        success_count += 1
    else:
        print("❌ Central orchestrator missing")
    
    # Check directory structure
    required_dirs = [
        "models/central_control/router_controller",
        "models/central_control/data_analyzer", 
        "models/central_control/tool_director",
        "app/central_control",
        "fine_tuning/datasets/central_control"
    ]
    
    for dir_path in required_dirs:
        total_checks += 1
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ Directory {dir_path} exists")
            success_count += 1
        else:
            print(f"❌ Directory {dir_path} missing")
    
    # Summary
    print(f"\n📊 Setup Verification Results:")
    print(f"✅ Passed: {success_count}/{total_checks}")
    
    if success_count == total_checks:
        print("🎉 Mistral 7B Central Control setup complete!")
        return True
    else:
        print("⚠️  Setup incomplete. Please address the issues above.")
        return False

if __name__ == "__main__":
    verify_setup()
EOF
    
    chmod +x "$BASE_DIR/scripts/central_control/verify_setup.py"
    log_success "Verification script created"
}

# Main setup function
main() {
    echo ""
    log_info "🧠 Mistral 7B Central Control Setup"
    echo "======================================"
    
    check_prerequisites
    install_dependencies
    create_directories
    download_mistral_7b
    create_central_orchestrator
    create_verification_script
    
    echo ""
    log_success "🎉 Mistral 7B Central Control Setup Complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Run verification: python scripts/central_control/verify_setup.py"
    echo "  2. Test orchestrator: python app/central_control/mistral_orchestrator.py"
    echo "  3. Integrate with existing academic domain system"
    echo ""
}

# Run main function
main "$@"
