from PySide6.QtCore import QThread, Signal
import os
import subprocess
import requests
import time
import json
import paramiko
from src.utils import resolve_ssh_details, RemotePaths

class RemoteScanWorker(QThread):
    finished = Signal(int)
    log = Signal(str)
    request_db_unlock = Signal()

    def __init__(self, remote_path, config):
        super().__init__()
        self.remote_path = remote_path
        self.config = config

    def _ssh_cmd_base(self, host, port, ssh_key):
        """Returns base SSH arguments for reuse."""
        return ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=30",
                "-i", ssh_key, "-p", str(port), f"root@{host}"]
    
    def _scp_cmd_base(self, port, ssh_key):
        """Returns base SCP arguments for reuse."""
        return ["scp", "-o", "StrictHostKeyChecking=no", "-P", str(port), "-i", ssh_key]

    def deploy_to_pod(self, host, port, ssh_key):
        """Push source code and setup script to the pod, run setup if needed."""
        project_root = os.path.dirname(os.path.dirname(__file__)).replace("\\", "/")
        
        # Files to always push (source code — small, fast)
        files_to_push = [
            (f"{project_root}/src/scanner.py", f"{RemotePaths.SRC}/scanner.py"),
            (f"{project_root}/src/utils.py", f"{RemotePaths.SRC}/utils.py"),
            (f"{project_root}/src/database.py", f"{RemotePaths.SRC}/database.py"),
            (f"{project_root}/setup_pod.sh", f"{RemotePaths.WORKSPACE}/setup_pod.sh"),
            (f"{project_root}/download_heretic.py", f"{RemotePaths.WORKSPACE}/download_heretic.py"),
        ]
        
        self.log.emit("📦 Deploying source code to pod...")
        # Also ensure rclone config is synced for 'do:' bucket access
        # Also ensure rclone config is synced for 'do:' bucket access
        do_access = self.config.get("do_access_key")
        do_secret = self.config.get("do_secret_key")
        do_endpoint = self.config.get("do_endpoint", "nyc3.digitaloceanspaces.com")
        
        # Ensure base directories exist on the Droplet (RunPod had them natively, DO does not)
        mkdir_cmd = self._ssh_cmd_base(host, port, ssh_key) + ["mkdir -p /root/.config/rclone /workspace/src /workspace/models"]
        try:
            res_mkdir = subprocess.run(mkdir_cmd, capture_output=True, text=True, timeout=15)
            if res_mkdir.returncode != 0:
                self.log.emit(f"  ⚠ Failed to create remote directories: {res_mkdir.stderr[:100]}")
        except Exception as e:
            self.log.emit(f"  ⚠ SSH mkdir timed out or failed: {e}")

        if do_access and do_secret:
            rclone_conf = f"[do]\ntype = s3\nprovider = DigitalOcean\nenv_auth = false\naccess_key_id = {do_access}\nsecret_access_key = {do_secret}\nendpoint = {do_endpoint}\nacl = private\n"
            
            tmp_conf = os.path.join(project_root, ".rclone.conf.tmp")
            try:
                with open(tmp_conf, "w") as f:
                    f.write(rclone_conf)
                scp_rclone = self._scp_cmd_base(port, ssh_key) + [tmp_conf, f"root@{host}:/root/.config/rclone/rclone.conf"]
                res = subprocess.run(scp_rclone, capture_output=True, text=True, timeout=15)
                if res.returncode != 0:
                    self.log.emit(f"  ⚠ Failed to push dynamic rclone.conf: {res.stderr[:100]}")
            except Exception as e:
                self.log.emit(f"  ⚠ Error generating rclone.conf: {e}")
            finally:
                if os.path.exists(tmp_conf):
                    os.remove(tmp_conf)
        else:
            self.log.emit("  ⚠ DigitalOcean credentials missing from config.json. Remote bucket scans will fail.")

        for local_path, remote_path in files_to_push:
            local_path_native = local_path.replace("/", os.sep)
            if not os.path.exists(local_path_native):
                self.log.emit(f"  ⚠ Skipping (not found): {os.path.basename(local_path)}")
                continue
            scp = self._scp_cmd_base(port, ssh_key) + [local_path_native, f"root@{host}:{remote_path}"]
            res = subprocess.run(scp, capture_output=True, text=True, timeout=15)
            if res.returncode != 0:
                self.log.emit(f"  ⚠ Failed to push {os.path.basename(local_path)}: {res.stderr[:100]}")
        
        # Check if Ollama is running — if not, run full setup
        self.log.emit("🔍 Checking pod health...")
        check_cmd = self._ssh_cmd_base(host, port, ssh_key) + [
            "curl -s http://localhost:11434/api/version 2>/dev/null || echo OLLAMA_DOWN"
        ]
        check_res = subprocess.run(check_cmd, capture_output=True, text=True, timeout=15)
        
        if "OLLAMA_DOWN" in check_res.stdout or not check_res.stdout.strip():
            self.log.emit("🔧 Pod needs setup — running setup_pod.sh (this may take a few minutes on first run)...")
            setup_cmd = self._ssh_cmd_base(host, port, ssh_key) + [
                f"export OLLAMA_MODELS=/workspace/ollama_models && chmod +x {RemotePaths.WORKSPACE}/setup_pod.sh && bash {RemotePaths.WORKSPACE}/setup_pod.sh"
            ]
            process = subprocess.Popen(setup_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                stripped = line.strip()
                if stripped:
                    self.log.emit(f"SETUP: {stripped}")
            process.wait()
            if process.returncode != 0:
                self.log.emit("⚠ Setup may have had issues — continuing with scan anyway.")
        else:
            self.log.emit("✅ Pod is healthy (Ollama running).")
        
        return True

    def run(self):
        host, port = resolve_ssh_details(self.config, logger=self.log.emit)
        if not host or not port:
            self.log.emit("Error: Missing SSH details.")
            self.finished.emit(0); return

        ssh_key = self.config.get("ssh_key", "~/.ssh/id_ed25519").replace("\\", "/")
        ssh_key = os.path.expanduser(ssh_key)
        
        if not os.path.exists(ssh_key):
            self.log.emit(f"FATAL: SSH Key not found at {ssh_key}")
            self.finished.emit(0); return

        # 0. Deploy code and ensure pod is set up
        try:
            self.deploy_to_pod(host, port, ssh_key)
        except Exception as e:
            self.log.emit(f"⚠ Deploy warning: {e}")

        self.log.emit(f"🚀 Initiating Remote Scan for: {self.remote_path}")
        
        # Pre-Scan Sync: Push the current local database to the pod so schemas match
        local_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src/content_factory.db").replace("\\", "/")
        remote_db = f"root@{host}:{RemotePaths.DB}"
        if os.path.exists(local_db):
            self.log.emit("Syncing local database to pod...")
            # Request UI unlock so DB is free to copy
            self.request_db_unlock.emit()
            from src.database import db
            try:
                db.stop()
                time.sleep(0.5)
            except Exception as e:
                self.log.emit(f"DB Stop Warning: {e}")
            
            # Wipe any orphaned WAL/SHM db files from previous failed remote runs
            ssh_wipe_cmd = self._ssh_cmd_base(host, port, ssh_key) + ["sh", "-c", f"rm -f {RemotePaths.DB}*"]
            try:
                subprocess.run(ssh_wipe_cmd, capture_output=True, timeout=10)
            except Exception as e:
                self.log.emit(f"DB Wipe Warning: {e}")
            
            # Sync main DB, WAL, and SHM files to ensure DB integrity
            db_exts = ["", "-wal", "-shm"]
            for ext in db_exts:
                l_file = f"{local_db}{ext}"
                r_file = f"{remote_db}{ext}"
                if os.path.exists(l_file):
                    scp_push_cmd = self._scp_cmd_base(port, ssh_key) + [l_file, r_file]
                    try:
                        scp_res = subprocess.run(scp_push_cmd, capture_output=True, text=True, timeout=60)
                        if scp_res.returncode != 0:
                            self.log.emit(f"DB Push Failed for {ext}: {scp_res.stderr}")
                    except Exception as e:
                        self.log.emit(f"DB Push Exception for {ext}: {e}")
            
            try:
                db.start()
                db.connect(reuse_if_open=True)
            except Exception as e:
                self.log.emit(f"DB Start Warning: {e}")
        
        try:
            # 1. Pre-scan Cleanup
            pkill_cmd = self._ssh_cmd_base(host, port, ssh_key) + ["pkill", "-f", "rclone serve"]
            subprocess.run(pkill_cmd, capture_output=True, text=True, timeout=10)
            
            # 2. Execute Scan
            scan_cmd = self._ssh_cmd_base(host, port, ssh_key) + [
                f"export PYTHONPATH={RemotePaths.WORKSPACE} && python3 {RemotePaths.SCANNER} '{self.remote_path}'"
            ]
            process = subprocess.Popen(scan_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            for line in process.stdout:
                self.log.emit(f"POD: {line.strip()}")
            
            process.wait()
            if process.returncode != 0:
                self.log.emit(f"Scan failed with code {process.returncode}")
                self.finished.emit(0); return
            
            # 2. Sync DB
            self.log.emit("Pulling results to hub...")
            self.request_db_unlock.emit()
            
            # Robust Unlock Wait
            from src.database import db
            for _ in range(5):
                try:
                    db.close()
                    break
                except:
                    time.sleep(0.5)
            
            local_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src/content_factory.db").replace("\\", "/")
            remote_db = f"root@{host}:{RemotePaths.DB}"
            
            self.log.emit(f"Syncing Database and WAL: {remote_db}* -> {local_db}*")
            
            # Sync main DB, WAL, and SHM files to prevent "database disk image is malformed"
            db_exts = ["", "-wal", "-shm"]
            
            for ext in db_exts:
                r_file = f"{remote_db}{ext}"
                l_file = f"{local_db}{ext}"
                l_tmp = f"{l_file}.cloud"
                
                scp_cmd = self._scp_cmd_base(port, ssh_key) + [r_file, l_tmp]
                try:
                    scp_res = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
                    if scp_res.returncode == 0:
                        # Windows file-locking workaround: Atomic replace
                        for _ in range(5):
                            try:
                                if os.path.exists(l_tmp):
                                    os.replace(l_tmp, l_file)
                                break
                            except Exception as rename_err:
                                time.sleep(1)
                except Exception as e:
                    self.log.emit(f"DB Sync Exception for {ext}: {e}")
            
            # Skip bulk thumbnail download (400MB+ on pod)
            # Users extract thumbnails on-demand via the GUI's Randomize button
            thumb_local = os.path.join(os.path.dirname(__file__), ".thumbnails").replace("\\", "/")
            os.makedirs(thumb_local, exist_ok=True)
            self.log.emit("Thumbnail sync skipped (use Randomize button to extract locally).")
            
            # 3. Path Re-mapping (Local display)
            try:
                from src.database import Content, db
                # Forcefully tear down the QueueDatabase before querying the hot-swapped file
                db.stop()
                time.sleep(0.5)
                db.start()
                db.connect(reuse_if_open=True)
                
                for item in Content.select().where(Content.thumbnail_path.contains(RemotePaths.WORKSPACE)):
                    fname = os.path.basename(item.thumbnail_path)
                    local_p = os.path.join(thumb_local, fname).replace("\\", "/")
                    if os.path.exists(local_p):
                        item.thumbnail_path = local_p
                        item.save()
            except Exception as e:
                self.log.emit(f"Local Re-mapping Warning: {e}")

            self.finished.emit(1)
        except Exception as e:
            self.log.emit(f"Error: {e}")
            self.finished.emit(0)

class ScanWorker(QThread):
    finished = Signal(int)
    log = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        from src.scanner import scan_directory
        self.log.emit(f"Starting scan of {self.path}...")
        count = scan_directory(self.path)
        self.finished.emit(count)
