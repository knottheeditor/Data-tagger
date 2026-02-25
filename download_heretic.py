import os
import sys
from huggingface_hub import hf_hub_download, list_repo_files

MODEL_DIR = "/workspace/models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("--- Listing files for bartowski/google_gemma-3-12b-it-GGUF ---")
try:
    files = list_repo_files("bartowski/google_gemma-3-12b-it-GGUF")
    print("Files found:")
    for f in files:
        print(f"  - {f}")
except Exception as e:
    print(f"Error listing files: {e}")

print("\n--- Downloading Heretic Text Model (Q4_K_M) ---")
try:
    heretic_path = hf_hub_download(
        repo_id="DreamFast/gemma-3-12b-it-heretic",
        filename="gguf/gemma-3-12b-it-heretic-Q4_K_M.gguf",
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False
    )
    print(f"Downloaded text model to: {heretic_path}")
except Exception as e:
    print(f"Text model download error: {e}")

print("\n--- Downloading Vision Projector ---")
# I will use a best guess based on the list if I could see it, but here I'll try to find any mmproj file if f16 fails
# The correct projector filename found in the repo list
mmproj_file = "mmproj-google_gemma-3-12b-it-f16.gguf"
# If I have the list, I would check it here. Since I am writing the script to run on the pod:
try:
    projector_path = hf_hub_download(
        repo_id="bartowski/google_gemma-3-12b-it-GGUF",
        filename=mmproj_file,
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False
    )
    print(f"Downloaded projector to: {projector_path}")
except Exception as e:
    print(f"Projector download error: {e}")
    print("Trying alternative: mmproj-google_gemma-3-12b-it-f16.gguf")
    try:
        projector_path = hf_hub_download(
            repo_id="bartowski/google_gemma-3-12b-it-GGUF",
            filename="mmproj-google_gemma-3-12b-it-f16.gguf",
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
        print(f"Downloaded projector to: {projector_path}")
    except Exception as e2:
        print(f"Alternative projector download error: {e2}")
