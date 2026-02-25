import requests
import json
import os
import sys
from src.database import db, Content, Asset

def check_system():
    print("--- DATA FORAGER SYSTEM CHECK ---")
    
    # 1. Database Check
    try:
        db.connect(reuse_if_open=True)
        print(f"✅ Database Connection: SUCCESS")
        print(f"   - Content Records: {Content.select().count()}")
        print(f"   - Asset Records: {Asset.select().count()}")
        print(f"   - sensor_log_raw column: {'EXISTS' if hasattr(Content, 'sensor_log_raw') else 'MISSING'}")
        
        last = Content.select().order_by(Content.id.desc()).first()
        if last:
            print(f"   - Last Scene: {last.scene_name} (ID: {last.id})")
    except Exception as e:
        print(f"❌ Database Connection: FAILED ({e})")

    # 2. Config Check
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Config File: FOUND")
        
        # 3. VLM Endpoint Check
        vlm_url = config.get("vlm_endpoint")
        if vlm_url:
            print(f"📡 Testing VLM Endpoint: {vlm_url}")
            try:
                # Test Ollama tags endpoint
                # If using /v1 proxy, Ollama's native /api/tags is usually at base level
                base_url = vlm_url.replace("/v1", "")
                test_url = base_url.rstrip("/") + "/api/tags"
                r = requests.get(test_url, timeout=10)
                if r.status_code == 200:
                    models = r.json().get("models", [])
                    model_names = [m["name"] for m in models]
                    print(f"✅ VLM API: REACHABLE (HTTP {r.status_code})")
                    print(f"   - Available Models: {', '.join(model_names)}")
                    
                    target_model = config.get("vlm_model")
                    audit_model = config.get("vlm_audit_model")
                    
                    if target_model in model_names or any(target_model in m for m in model_names):
                        print(f"   - Primary Model ({target_model}): READY")
                    else:
                        print(f"   - Primary Model ({target_model}): NOT FOUND (Warning)")
                        
                    if audit_model in model_names or any(audit_model in m for m in model_names):
                        print(f"   - Audit Model ({audit_model}): READY")
                    else:
                        print(f"   - Audit Model ({audit_model}): NOT FOUND (Warning)")
                else:
                    print(f"❌ VLM API: FAILED (HTTP {r.status_code})")
            except Exception as e:
                print(f"❌ VLM API: UNREACHABLE ({e})")
    else:
        print(f"❌ Config File: NOT FOUND")

    print("--- CHECK COMPLETE ---")

if __name__ == "__main__":
    check_system()
