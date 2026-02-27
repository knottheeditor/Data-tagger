from datetime import datetime
import json
import hashlib

# ==================== CONSTANTS & PATHS ====================
class RemotePaths:
    """Centralized truth for remote pod paths."""
    WORKSPACE = "/workspace"
    SRC = "/workspace/src"
    THUMBNAILS = "/workspace/src/.thumbnails"
    DB = "/workspace/src/content_factory.db"
    SCANNER = "/workspace/src/scanner.py"

def get_rclone_url(rclone_path, timeout=15):
    """Gets a public/temporary URL for an rclone path via 'rclone link'."""
    try:
        # Get rclone executable path from config
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        rclone_exe = "rclone"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                rclone_exe = config.get("rclone_path", "rclone")

        # DigitalOcean Spaces requires linking with an expiration otherwise it fails if private.
        cmd = [rclone_exe, "link", "--expire", "15m", rclone_path]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout).decode('utf-8').strip()
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        return lines[-1] if lines else None
    except FileNotFoundError:
        print(f"  > Skipping rclone link (rclone not installed locally)", flush=True)
        return None
    except subprocess.TimeoutExpired:
        print(f"  > rclone link timed out for {rclone_path}", flush=True)
        return None
    except Exception as e:
        print(f"  > rclone link failed: {e}", flush=True)
        return None

# ==================== DATE & TYPE PARSING ====================
DATE_PATTERN = r"(\d{4}[\-\.\s]\d{2}[\-\.\s]\d{2})"
NL_DATE_PATTERN = r"(?i)(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{2,4})"

def standardize_nl_date(match):
    """Converts (Month, Day, Year) match to YYYY-MM-DD"""
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }
    m_name, d, y = match.groups()
    m = months.get(m_name.lower(), 1)
    y = int(y)
    if y < 100: y += 2000
    try:
        dt = datetime(year=y, month=m, day=int(d))
        return dt.strftime("%Y-%m-%d")
    except:
        return None

TYPE_KEYWORDS = {
    "TRAILER": ["trailer", "preview", "teaser", "trl", "tlr", "pre"],
    "THUMB": ["thumb", "thumbnail", "jpg", "png", "poster", "pic", "image"],
    "META": ["meta", "json", "data"],
    "STREAMVOD": ["stream", "vod", "fullvod", "recording"],
    "PPV": ["ppv", "full", "scene", "main", "complete"],
}

# ==================== CORE UTILITIES = [NEW] ====================
class ConfigManager:
    """Consolidated configuration and tool discovery."""
    _config = None
    
    @classmethod
    def get_config(cls):
        if cls._config is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if not os.path.exists(config_path):
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json.template")
            try:
                with open(config_path, 'r') as f:
                    cls._config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                cls._config = {}
        return cls._config

    @classmethod
    def get_rclone_exe(cls):
        config = cls.get_config()
        path = config.get("rclone_path")
        if path and os.path.exists(path): return path
        import shutil
        return shutil.which("rclone") or os.path.join(os.getcwd(), "rclone.exe")

class MetadataCache:
    """Memoizes file metadata (size, mtime) to avoid redundant hashing."""
    _cache = {}
    
    @classmethod
    def get_file_info(cls, filepath):
        """Returns (size, mtime) for a local file, or None if error."""
        try:
            stat = os.stat(filepath)
            return stat.st_size, stat.st_mtime
        except:
            return None

    @classmethod
    def needs_rehash(cls, filepath, saved_hash):
        """Checks if a file's metadata matches the cached version."""
        if not saved_hash: return True
        current_info = cls.get_file_info(filepath)
        if not current_info: return True
        
        cache_key = hashlib.md5(filepath.encode()).hexdigest()
        cached = cls._cache.get(cache_key)
        
        if cached == current_info:
            return False
            
        cls._cache[cache_key] = current_info
        return True

def resolve_ssh_details(config, logger=None):
    """Resolves IP/Port from static config (RunPod API fallback removed)."""
    # 1. Check for DigitalOcean static IP override
    if config.get("do_droplet_ip"):
        if logger: logger(f"Resolved: DigitalOcean Droplet at {config['do_droplet_ip']}:22")
        return config["do_droplet_ip"], 22
        
    # 2. Return static config
    host = config.get("ssh_host")
    port = config.get("ssh_port", 22)
    
    if logger: logger(f"Resolved static host: {host}:{port}")
    return host, port

def parse_filename(filename, parent_path=None):
    """Extracts structural metadata from a file string."""
    data = {"type": None, "date": None, "name": "Unknown Scene", "number": 1}
    name_only, ext = os.path.splitext(filename)
    
    # 1. Date
    date_match = re.search(DATE_PATTERN, name_only)
    if date_match:
        raw_date = date_match.group(1)
        data["date"] = re.sub(r"[\.\s]", "-", raw_date)
        name_only = name_only.replace(raw_date, "")
    else:
        nl_match = re.search(NL_DATE_PATTERN, name_only)
        if nl_match:
            std_date = standardize_nl_date(nl_match)
            if std_date:
                data["date"] = std_date
                name_only = name_only.replace(nl_match.group(0), "")

    if not data["date"] and parent_path:
        parent_name = os.path.basename(parent_path)
        p_match = re.search(DATE_PATTERN, parent_name)
        if p_match: data["date"] = re.sub(r"[\.\s]", "-", p_match.group(1))

    # 2. Number
    num_match = re.search(r"(?i)(?:scene|no|#|s)\s*(\d+)", name_only)
    if num_match: data["number"] = int(num_match.group(1))
    
    # 3. Type
    norm_name = re.sub(r"[^a-zA-Z0-9\s]", " ", name_only).lower()
    detected_type = None
    for t_key, keywords in TYPE_KEYWORDS.items():
        if t_key == "PPV": continue 
        for kw in keywords:
            if re.search(rf"\b{kw}\b", norm_name):
                detected_type = t_key
                break
        if detected_type: break
    data["type"] = detected_type if detected_type else "PPV"

    # 4. Name Cleanup
    clean_name = name_only
    if num_match: clean_name = clean_name.replace(num_match.group(0), "")
    for t_key, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            clean_name = re.sub(rf"(?i)(?<![a-z]){kw}(?![a-z])", "", clean_name)
    clean_name = re.sub(r"[\-_\.\(\)]+", " ", clean_name).strip()
    clean_name = re.sub(r"\s+", " ", clean_name)
    data["name"] = clean_name if len(clean_name) > 1 else (name_only.strip() or "Unknown Scene")
        
    return data

class StandardNaming:
    """Single source of truth for standard file naming."""
    @staticmethod
    def get_file_name(content_id, date, title, content_type="PPV", ext=".mp4"):
        """Generates: TYPE_ID_YYYY_MM_DD.ext or TYPE_ID.ext if date exists in title."""
        if not date or date == "None":
            # If no date, check if title has one
            if re.search(r"\d{4}[-_]\d{2}[-_]\d{2}", title):
                return f"{content_type}_{content_id}{ext}"
            return f"{content_type}_{content_id}_NO_DATE{ext}"
            
        safe_date = str(date).replace("_", "-").replace(" ", "-")
        return f"{content_type}_{content_id}_{safe_date}{ext}"

    @staticmethod
    def get_meta_name(content_id, date):
        """Generates: METADATA_ID_YYYY-MM-DD.txt"""
        safe_date = (date or datetime.now().strftime("%Y-%m-%d")).replace("_", "-")
        return f"METADATA_{content_id}_{safe_date}.txt"
