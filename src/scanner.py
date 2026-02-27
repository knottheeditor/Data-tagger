
import os
import hashlib
import time
from src.database import Content, db
from src.utils import parse_filename, get_rclone_url, RemotePaths
import subprocess
import json
import collections
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.wmv', '.webm'}

# Module-level: set by scan_rclone before parallel probing
_RCLONE_SERVE_BASE = None  # e.g. "http://localhost:9876"
_RCLONE_SERVE_REMOTE = None  # e.g. "do:chloe-storage/content-for-sale/STREAMVOD"

def get_file_hash(filepath, block_size=1024*1024):
    """Generates a hash for the first megabyte of a file (fast discovery)"""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(block_size)
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}", flush=True)
        return None

def _get_serve_url(filepath):
    """Convert a do: filepath to a localhost URL via the running rclone serve proxy."""
    global _RCLONE_SERVE_BASE, _RCLONE_SERVE_REMOTE
    if _RCLONE_SERVE_BASE and _RCLONE_SERVE_REMOTE and filepath.startswith(_RCLONE_SERVE_REMOTE):
        # Strip the remote prefix to get the relative path
        relative = filepath[len(_RCLONE_SERVE_REMOTE):].lstrip("/")
        # URL-encode path components (preserve /)
        parts = relative.split("/")
        encoded = "/".join(quote(p) for p in parts)
        return f"{_RCLONE_SERVE_BASE}/{encoded}"
    return None

def extract_metadata_remote(filepath):
    """Extracts duration and a thumbnail on the pod. Has timeouts to avoid hanging."""
    duration = 0
    thumb_path = None
    
    # 1. Get Duration
    try:
        # For cloud paths, prefer the rclone serve http proxy (fast, proper Range requests)
        # Fallback to rclone link if serve isn't running (e.g. GUI lazy-load)
        if filepath.startswith("do:"):
            url = _get_serve_url(filepath)
            if not url:
                url = get_rclone_url(filepath)
        else:
            url = filepath
        
        if url:
            cmd = [
                'ffprobe', '-v', 'error', 
                '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                url
            ]
            output = subprocess.check_output(cmd, timeout=30).decode('utf-8').strip()
            duration = int(float(output))
        else:
            print(f"  > Skipping metadata (no URL): {filepath}", flush=True)
            return 0, None
    except subprocess.TimeoutExpired:
        print(f"  > Duration probe timed out for {filepath}", flush=True)
    except Exception as e:
        print(f"  > Duration extraction failed for {filepath}: {e}", flush=True)
        
    # 2. Extract Thumbnail
    try:
        thumb_dir = RemotePaths.THUMBNAILS
        os.makedirs(thumb_dir, exist_ok=True)
        fname = os.path.basename(filepath)
        fhash = hashlib.md5(fname.encode()).hexdigest()[:8]
        target = os.path.join(thumb_dir, f"THUMB_{fhash}.png")
        
        ss = min(5, duration * 0.1) if duration > 0 else 2
        
        if filepath.startswith("do:"):
            url = _get_serve_url(filepath)
            if not url:
                url = get_rclone_url(filepath)
            if url:
                cmd = [
                    'ffmpeg', '-ss', str(ss), '-i', url, '-frames:v', '1', '-q:v', '2', '-y', target
                ]
            else:
                return duration, None
        else:
            cmd = [
                'ffmpeg', '-probesize', '10M', '-analyzeduration', '10M',
                '-ss', str(ss), '-i', filepath, 
                '-frames:v', '1', '-q:v', '2', '-y', target
            ]
            
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        if os.path.exists(target):
            thumb_path = target
    except subprocess.TimeoutExpired:
        print(f"  > Thumbnail extraction timed out for {filepath}", flush=True)
    except Exception as e:
        print(f"  > Thumbnail extraction failed for {filepath}: {e}", flush=True)
        
    return duration, thumb_path

def extract_random_thumbnail(filepath):
    """Picks a random timestamp and extracts a frame on the pod."""
    import random
    
    thumb_dir = RemotePaths.THUMBNAILS
    os.makedirs(thumb_dir, exist_ok=True)
    fname = os.path.basename(filepath)
    fhash = hashlib.md5(fname.encode()).hexdigest()[:8]
    target = os.path.join(thumb_dir, f"THUMB_{fhash}.png")
    if filepath.startswith("do:"):
        # FUSE MOUNT STRATEGY: rclone mount provides kernel-level byte-range seeking,
        # allowing ffmpeg to treat DO Spaces files as local files.
        # ffmpeg's HTTP demuxer hangs on DO Spaces pre-signed URLs for large files.
        MOUNT_POINT = "/mnt/spaces"
        
        # 1. Parse do:bucket/path → /mnt/spaces/path
        do_path = filepath[3:]  # strip "do:"
        bucket = do_path.split("/")[0]  # e.g. "chloe-storage"
        rel_path = "/".join(do_path.split("/")[1:])  # e.g. "content-for-sale/STREAMVOD/file.mp4"
        local_path = os.path.join(MOUNT_POINT, rel_path)
        
        # 2. Ensure rclone mount is running
        try:
            mount_check = subprocess.run(["mountpoint", "-q", MOUNT_POINT])
            if mount_check.returncode != 0:
                os.makedirs(MOUNT_POINT, exist_ok=True)
                subprocess.run([
                    "rclone", "mount", f"do:{bucket}", MOUNT_POINT,
                    "--vfs-cache-mode", "minimal",
                    "--vfs-read-chunk-size", "10M",
                    "--allow-non-empty",
                    "--daemon"
                ], timeout=10)
                import time as _t
                _t.sleep(3)  # Wait for mount to stabilize
        except Exception as e:
            print(f"  > FUSE mount check/start failed: {e}", flush=True)
            return None
        
        if not os.path.exists(local_path):
            print(f"  > FUSE path not found: {local_path}", flush=True)
            return None
        
        # 3. Get duration via ffprobe on FUSE path
        duration = 600
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1', local_path]
            output = subprocess.check_output(cmd, timeout=30).decode('utf-8').strip()
            duration = int(float(output))
        except Exception:
            pass
        
        # 4. Extract random frame
        ts = random.uniform(duration * 0.1, duration * 0.9)
        cmd = ['ffmpeg', '-ss', str(ts), '-i', local_path,
               '-frames:v', '1', '-q:v', '2', '-y', target]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        
        return target if os.path.exists(target) else None
    else:
        # Local file fallback
        duration = 600
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
            output = subprocess.check_output(cmd, timeout=10).decode('utf-8').strip()
            duration = int(float(output))
        except: pass
        
        ts = random.uniform(duration * 0.1, duration * 0.9)
        cmd = ['ffmpeg', '-ss', str(ts), '-i', filepath, '-frames:v', '1', '-q:v', '2', '-y', target]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        
        return target if os.path.exists(target) else None

def scan_directory(directory_path):
    """
    Scans a directory recursively, groups related files, and designates a Master.
    """
    print(f"Scanning: {directory_path}...", flush=True)
    files_added = 0
    files_updated = 0
    groups = collections.defaultdict(list) # {(date, name): [files]}
    new_masters_to_probe = []

    # Recursive scan using os.walk
    try:
        count = 0
        for root, dirs, files in os.walk(directory_path, followlinks=False):
            print(f"  > Scanning Subdir: {root} ({len(files)} files)", flush=True)
            for name in files:
                count += 1
                if count % 1000 == 0:
                    print(f"  > Processed {count} discovery items...", flush=True)
                full_path = os.path.join(root, name)
                
                ext = os.path.splitext(name)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    # Pass the immediate parent folder as context, not the root scan folder
                    meta = parse_filename(name, parent_path=root)
                    key = (meta["date"], meta["name"].lower())
                    if key not in groups:
                        groups[key] = []
                    groups[key].append({
                        "path": full_path,
                        "meta": meta,
                        "size": os.stat(full_path).st_size,
                        "name": name
                    })
    except Exception as e:
        print(f"Directory scan error: {e}", flush=True)

    # Process Groups to identify Master
    print(f"Directory scan complete. Grouped {len(groups)} items. Processing groups...", flush=True)
    for key, file_list in groups.items():
        scene_date, scene_name = key
        
        # 1. Identify Master (Largest file by default, preferring PPV type, deprioritizing FULL VODs)
        file_list.sort(key=lambda x: x["size"], reverse=True)
        master_candidate = file_list[0]
        
        # Look for the best candidate: Not a full VOD, preferably PPV.
        for f in file_list:
            is_vod = "full vod" in f["name"].lower()
            if f["meta"]["type"] == "PPV" and not is_vod:
                master_candidate = f
                break
            # If the current master is a full VOD but we found a smaller highlight clip, prefer the highlight
            if "full vod" in master_candidate["name"].lower() and not is_vod:
                master_candidate = f
        
        # 2. CHECK PERSISTENCE: Is there already a Master in DB for this (date, name)?
        existing_master = Content.select().where(
            (Content.content_date == scene_date) & 
            (Content.scene_name ** scene_name) # Case-insensitive match
        ).first()

        master_record = None
        
        if existing_master:
            # Refresh metadata if changed
            updated = False
            if existing_master.content_type != master_candidate["meta"]["type"]:
                existing_master.content_type = master_candidate["meta"]["type"]
                updated = True
            if existing_master.scene_number != master_candidate["meta"]["number"]:
                existing_master.scene_number = master_candidate["meta"]["number"]
                updated = True
            if existing_master.scene_name != master_candidate["meta"]["name"]:
                existing_master.scene_name = master_candidate["meta"]["name"]
                # Also reset status if it was stuck
                if existing_master.status == "processing": existing_master.status = "pending"
                updated = True
            
            if updated:
                existing_master.save()
                files_updated += 1
                
            master_record = existing_master
            
            # Asset Linking for existing master done outside the future block
            _link_assets(master_record, file_list)
        else:
            # 3. Create New Master Record if candidate not already in DB by path
            if Content.select().where(Content.source_path == master_candidate["path"]).exists():
                continue
                
            # Add to queue for parallel processing
            new_masters_to_probe.append((key, master_candidate, file_list))

    print(f"Group processing complete. {len(new_masters_to_probe)} new masters require probing.", flush=True)

    # Phase 2: Parallel Probing for New Masters
    print(f"  > Probing {len(new_masters_to_probe)} new masters in parallel...", flush=True)
    probed_results = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Map future to (key, master_candidate, file_list)
        future_to_master = {
            executor.submit(extract_metadata_remote, item[1]["path"]): item 
            for item in new_masters_to_probe
        }
        
        for future in as_completed(future_to_master):
            key, master_candidate, file_list = future_to_master[future]
            try:
                duration, thumb = future.result()
                status_val = "pending"
            except Exception as e:
                # Timeout or failure: Create fail-safe record
                print(f"  > Probe failed/timed out for {key}: {e}. Creating fail-safe record.", flush=True)
                duration, thumb = 0, None
                status_val = "pending_meta"
                
            probed_results.append((key, master_candidate, file_list, duration, thumb, status_val))
                
        # Phase 3: Sequential DB Write (SQLite Thread Safety)
        for key, master_candidate, file_list, duration, thumb, status_val in probed_results:
            try:
                master_record = Content.create(
                    source_path=master_candidate["path"],
                    file_hash=get_file_hash(master_candidate["path"]),
                    file_size=master_candidate["size"],
                    scene_name=master_candidate["meta"]["name"],
                    scene_number=master_candidate["meta"]["number"],
                    content_date=master_candidate["meta"]["date"],
                    content_type=master_candidate["meta"]["type"],
                    duration_seconds=duration,
                    thumbnail_path=thumb,
                    status=status_val
                )
                files_added += 1
                
                # 4. Link Assets (All other files in group)
                _link_assets(master_record, file_list)
                
            except Exception as db_e:
                print(f"  > DB Creation failed for {key}: {db_e}", flush=True)

    print(f"Scan complete. Added {files_added}, Updated {files_updated} master scenes.", flush=True)
    return files_added + files_updated

def _link_assets(master_record, file_list):
    """Helper function to link non-master files as assets."""
    from src.database import Asset
    for asset_file in file_list:
        # Skip if this IS the record we just used for master (by path)
        if asset_file["path"] == master_record.source_path:
            continue
        
        # Also skip if already linked as asset
        if Asset.select().where(Asset.local_path == asset_file["path"]).exists():
            continue

        Asset.create(
            content=master_record,
            asset_type=asset_file["meta"]["type"].lower(),
            local_path=asset_file["path"],
            status="pending"
        )

        # The existing loop logic from line 214...
        # ... was replaced by the _link_assets call in the new implementation.

def get_rclone_hash(remote_path, block_size=1024*1024):
    """Gets a hash for the first megabyte using rclone cat."""
    import json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    rclone_exe = "rclone"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            rclone_exe = config.get("rclone_path", "rclone")

    cmd = [rclone_exe, "cat", remote_path, "--offset", "0", "--count", str(block_size)]
    try:
        output = subprocess.check_output(cmd)
        return hashlib.md5(output).hexdigest()
    except Exception as e:
        print(f"Error hashing {remote_path}: {e}", flush=True)
        return None

def scan_rclone(remote_name):
    """
    Scans an rclone remote recursively, groups files, and designates a Master.
    """
    import json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    rclone_exe = "rclone"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            rclone_exe = config.get("rclone_path", "rclone")

    print(f"Scanning rclone remote: {remote_name}...", flush=True)
    cmd = [rclone_exe, "lsjson", "-R", remote_name]
    files_added = 0
    files_updated = 0
    groups = collections.defaultdict(list)
    new_masters_to_probe = []

    try:
        output = subprocess.check_output(cmd, timeout=120)
        items = json.loads(output)
        
        for item in items:
            if item["IsDir"]: continue
            
            ext = os.path.splitext(item["Name"])[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                full_remote_path = f"{remote_name}/{item['Path']}"
                meta = parse_filename(item["Name"])
                key = (meta["date"], meta["name"].lower())
                
                groups[key].append({
                    "path": full_remote_path,
                    "meta": meta,
                    "size": item["Size"],
                    "name": item["Name"]
                })
        
        # Process Groups (OUTSIDE the discovery loop)
        total_groups = len(groups)
        for i, (key, file_list) in enumerate(groups.items()):
            scene_date, scene_name = key
            print(f"[{i+1}/{total_groups}] Processing: {scene_name}...", flush=True)
            
            file_list.sort(key=lambda x: x["size"], reverse=True)
            master_candidate = file_list[0]
            
            # Look for the best candidate: Not a full VOD, preferably PPV.
            for f in file_list:
                is_vod = "full vod" in f["name"].lower()
                if f["meta"]["type"] == "PPV" and not is_vod:
                    master_candidate = f
                    break
                # If current master is a FULL VOD and we find a highlight, prefer the highlight
                if "full vod" in master_candidate["name"].lower() and not is_vod:
                    master_candidate = f
            
            # CHECK PERSISTENCE (handle NULL dates properly)
            if scene_date is None:
                date_filter = Content.content_date.is_null()
            else:
                date_filter = (Content.content_date == scene_date)
            
            existing_master = Content.select().where(
                date_filter & 
                (Content.scene_name ** scene_name)
            ).first()

            master_record = None
            
            if existing_master:
                # Refresh metadata if changed
                updated = False
                if existing_master.content_type != master_candidate["meta"]["type"]:
                    existing_master.content_type = master_candidate["meta"]["type"]
                    updated = True
                if existing_master.scene_number != master_candidate["meta"]["number"]:
                    existing_master.scene_number = master_candidate["meta"]["number"]
                    updated = True
                if existing_master.scene_name != master_candidate["meta"]["name"]:
                    existing_master.scene_name = master_candidate["meta"]["name"]
                    updated = True
                
                # If it has no duration/thumb, let the Lazy Enrichment system handle it later
                # to prevent blocking the initial index scan.
                
                if updated:
                    existing_master.save()
                    files_updated += 1
                    
                master_record = existing_master
                _link_assets(master_record, file_list)
            else:
                # Add to queue for parallel processing
                new_masters_to_probe.append((key, master_candidate, file_list))

        # Phase 2: Parallel Probing for New Masters
        if new_masters_to_probe:
            print(f"  > Probing {len(new_masters_to_probe)} new masters in parallel...", flush=True)
            probed_results = []
            
            # Start rclone serve http proxy for cloud paths
            global _RCLONE_SERVE_BASE, _RCLONE_SERVE_REMOTE
            serve_proc = None
            is_cloud = any(item[1]["path"].startswith("do:") for item in new_masters_to_probe)
            if is_cloud:
                _RCLONE_SERVE_REMOTE = remote_name
                _RCLONE_SERVE_BASE = "http://localhost:9876"
                print(f"  > Starting rclone HTTP proxy for {remote_name}...", flush=True)
                serve_proc = subprocess.Popen(
                    [rclone_exe, "serve", "http", remote_name, "--addr", ":9876", "--read-only",
                     "--vfs-cache-mode", "off"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                time.sleep(3)  # Wait for server to start
            
            try:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_to_master = {}
                    for item in new_masters_to_probe:
                        size = item[1].get("size", 0)
                        # Massive files (>500MB) consistently timeout via HTTP proxy. 
                        # Skip probe to save 90 seconds per file and assign pending_meta immediately.
                        if item[1]["path"].startswith("do:") and size > 500 * 1024 * 1024:
                            print(f"  > Fast-tracking enormous cloud file: {item[1]['name']} ({size/1024/1024:.1f}MB)", flush=True)
                            probed_results.append((item[0], item[1], item[2], 0, None, "pending_meta"))
                        else:
                            future_to_master[executor.submit(extract_metadata_remote, item[1]["path"])] = item
                    
                    
                    for future in as_completed(future_to_master):
                        key, master_candidate, file_list = future_to_master[future]
                        try:
                            duration, thumb = future.result()
                            status_val = "pending" if duration > 0 else "pending_meta"
                        except Exception as e:
                            print(f"  > Probe failed for {key}: {e}. Creating fail-safe record.", flush=True)
                            duration, thumb = 0, None
                            status_val = "pending_meta"
                            
                        probed_results.append((key, master_candidate, file_list, duration, thumb, status_val))
            finally:
                if serve_proc:
                    serve_proc.terminate()
                    serve_proc.wait()
                    _RCLONE_SERVE_BASE = None
                    _RCLONE_SERVE_REMOTE = None
                    print(f"  > rclone HTTP proxy stopped.", flush=True)
                    
            # Phase 3: Sequential DB Write (SQLite Thread Safety)
            for key, master_candidate, file_list, duration, thumb, status_val in probed_results:
                try:
                    file_hash = None
                    if not master_candidate["path"].startswith("do:"):
                        file_hash = get_file_hash(master_candidate["path"])
                    
                    master_record = Content.create(
                        source_path=master_candidate["path"],
                        file_hash=file_hash,
                        file_size=master_candidate["size"],
                        scene_name=master_candidate["meta"]["name"],
                        scene_number=master_candidate["meta"]["number"],
                        content_date=master_candidate["meta"]["date"],
                        content_type=master_candidate["meta"]["type"],
                        duration_seconds=duration,
                        thumbnail_path=thumb,
                        status=status_val
                    )
                    files_added += 1
                    _link_assets(master_record, file_list)
                    
                except Exception as db_e:
                    print(f"  > DB Creation failed for cloud group {key}: {db_e}", flush=True)
                    
    except Exception as e:
        print(f"Rclone scan failed: {e}", flush=True)
        
    print(f"Scan complete. Indexed {files_added} master scenes from cloud.", flush=True)
    return files_added

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    try:
        if ":" in path: # Looks like a remote
            if path == "random-thumb" and len(sys.argv) > 2:
                target = extract_random_thumbnail(sys.argv[2])
                if target: print(f"SUCCESS:{target}", flush=True)
                else: print("FAILED", flush=True)
            else:
                scan_rclone(path)
        else:
            scan_directory(path)
    finally:
        if hasattr(db, "stop"):
            # Ensure the SQLite background worker thread cleanly terminates so Python can exit
            db.stop()
