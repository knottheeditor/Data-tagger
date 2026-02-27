#!/bin/bash
# ============================================================
# Data Forager: Full Remote Pod Setup Script
# Run this ONCE on your remote pod instance after starting the pod.
# This script is idempotent — safe to re-run.
#
# Usage:
#   bash /workspace/setup_pod.sh
#
# What it does:
#   1. Installs system dependencies (zstd, ffmpeg, rclone)
#   2. Installs Ollama
#   3. Pulls the official gemma3:12b model (with built-in vision)
#   4. Starts Ollama server on 0.0.0.0:11434
#
# IMPORTANT REQUIREMENT FOR CLOUD SCANNING:
# Ensure you have added your DigitalOcean Spaces keys to `config.json`:
#   "do_endpoint": "nyc3.digitaloceanspaces.com",
#   "do_access_key": "YOUR_ACCESS_KEY",
#   "do_secret_key": "YOUR_SECRET_KEY"
# The dashboard worker will automatically inject these into the pod on scan.
# ============================================================

set -e

echo "============================================"
echo "  DATA FORAGER // Remote Pod Auto-Setup"
echo "============================================"

# --- Config ---
OLLAMA_MODEL_NAME="gemma3:12b"

# --- Step 1: System & Python Dependencies ---
echo ""
echo "[1/4] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq zstd ffmpeg 2>/dev/null || true

# Install rclone if missing
if ! command -v rclone &> /dev/null; then
    echo "  -> Installing rclone..."
    curl -fsSL https://rclone.org/install.sh | bash
fi

echo "  -> Installing Python dependencies..."
pip install -q peewee moviepy opencv-python-headless requests python-dotenv tqdm pydantic fastapi uvicorn

echo "  -> Environment: OK"

# --- Step 2: Install Ollama ---
echo ""
echo "[2/4] Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "  -> Ollama installed."
else
    echo "  -> Ollama already installed: $(ollama --version)"
fi

# --- Step 3: Start Ollama on 0.0.0.0 ---
echo ""
echo "[3/4] Starting Ollama server..."
# Kill any existing instance
pkill ollama 2>/dev/null || true
sleep 1

# Start on 0.0.0.0 so RunPod proxy can reach it
mkdir -p /workspace/ollama_models
OLLAMA_HOST=0.0.0.0 OLLAMA_MODELS=/workspace/ollama_models nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

# Verify it's running
if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "  -> Ollama server running."
else
    echo "  -> ERROR: Ollama failed to start. Check /tmp/ollama.log"
    exit 1
fi

# --- Step 4: Pull Model ---
echo ""
echo "[4/4] Pulling model: ${OLLAMA_MODEL_NAME}..."

# Check if model already exists
if ollama list 2>/dev/null | grep -q "${OLLAMA_MODEL_NAME}"; then
    echo "  -> Model already available."
else
    echo "  -> Downloading from Ollama registry (this may take a few minutes)..."
    OLLAMA_MODELS=/workspace/ollama_models ollama pull "${OLLAMA_MODEL_NAME}"
    echo "  -> Model pulled successfully."
fi

# --- Create workspace structure ---
echo ""
echo "[BONUS] Ensuring workspace structure..."
mkdir -p /workspace/src/.thumbnails

# --- Verify ---
echo ""
echo "============================================"
echo "  SETUP COMPLETE!"
echo "============================================"
echo ""
echo "Model:    ${OLLAMA_MODEL_NAME}"
echo "Endpoint: http://0.0.0.0:11434/v1"
echo "Proxy:    Use remote proxy URL for external access"
echo ""
ollama list
echo ""
