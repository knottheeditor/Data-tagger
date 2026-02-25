#!/bin/bash
# ============================================================
# Gemma-3-12B-IT-Heretic: Full Setup Script for RunPod
# Run this ONCE on your RunPod instance after starting the pod.
# ============================================================

set -e

echo "============================================"
echo "  Gemma-3-12B-IT-Heretic Setup for RunPod"
echo "============================================"

# --- Config ---
MODEL_DIR="/workspace/models"
MODELFILE_PATH="/workspace/Modelfile.heretic"
OLLAMA_MODEL_NAME="gemma3-heretic:12b"

HERETIC_REPO="DreamFast/gemma-3-12b-it-heretic"
HERETIC_FILE="gguf/gemma-3-12b-it-heretic-Q4_K_M.gguf"
HERETIC_LOCAL="${MODEL_DIR}/gemma-3-12b-it-heretic-Q4_K_M.gguf"

MMPROJ_REPO="bartowski/google_gemma-3-12b-it-GGUF"
MMPROJ_FILE="mmproj-google_gemma-3-12b-it-f16.gguf"
MMPROJ_LOCAL="${MODEL_DIR}/${MMPROJ_FILE}"

# --- Step 0: Install huggingface-cli if missing ---
echo ""
echo "[0/4] Checking for huggingface-cli..."
if ! command -v huggingface-cli &> /dev/null; then
    echo "  -> Installing huggingface_hub..."
    pip install -q -U "huggingface_hub[cli]"
fi
echo "  -> OK"

# --- Step 1: Create model directory ---
echo ""
echo "[1/4] Creating model directory: ${MODEL_DIR}"
mkdir -p "${MODEL_DIR}"

# --- Step 2 & 3: Download via Python helper ---
echo ""
echo "[2/3] Downloading models via Python helper..."
python3 /workspace/download_heretic.py

# --- Step 4: Create Modelfile and register with Ollama ---
echo ""
echo "[3/3] Creating Ollama model: ${OLLAMA_MODEL_NAME}"

cat > "${MODELFILE_PATH}" <<'MODELFILE_EOF'
FROM /workspace/models/gguf/gemma-3-12b-it-heretic-Q4_K_M.gguf
ADAPTER /workspace/models/mmproj-google_gemma-3-12b-it-f16.gguf

TEMPLATE """{{- range .Messages }}
{{- if eq .Role "user" }}<start_of_turn>user
{{ .Content }}<end_of_turn>
{{ else if eq .Role "model" }}<start_of_turn>model
{{ .Content }}<end_of_turn>
{{ end }}
{{- end }}<start_of_turn>model
"""

PARAMETER stop <end_of_turn>
PARAMETER temperature 0.4
PARAMETER num_ctx 8192
MODELFILE_EOF

# Ensure Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "  -> Starting Ollama server..."
    ollama serve &
    sleep 3
fi

ollama create "${OLLAMA_MODEL_NAME}" -f "${MODELFILE_PATH}"
echo ""
echo "============================================"
echo "  DONE! Model registered as: ${OLLAMA_MODEL_NAME}"
echo "============================================"
echo ""
echo "Quick test:"
echo "  ollama run ${OLLAMA_MODEL_NAME} 'Hello, describe yourself.'"
echo ""
echo "To verify vision:"
echo "  curl http://localhost:11434/v1/chat/completions -d '{"
echo "    \"model\": \"${OLLAMA_MODEL_NAME}\","
echo "    \"messages\": [{\"role\": \"user\", \"content\": \"hello\"}]"
echo "  }'"
echo ""
