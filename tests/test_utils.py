import pytest
import os
import json
from src.utils import ConfigManager, MetadataCache, parse_filename, standardize_nl_date, resolve_ssh_details

def test_config_manager_loading(mock_config, monkeypatch):
    """Test that ConfigManager loads the correct config values."""
    # Reset internal cache for testing
    ConfigManager._config = None
    
    # Mock os.path.join to point to our mock_config
    orig_join = os.path.join
    def mock_join(*args):
        if "config.json" in args:
            return mock_config
        return orig_join(*args)
    
    monkeypatch.setattr(os.path, "join", mock_join)
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    config = ConfigManager.get_config()
    assert config["ssh_host"] == "1.2.3.4"
    assert config["ssh_port"] == 2222

def test_metadata_cache_needs_rehash(temp_workspace):
    """Test that MetadataCache correctly identifies when a file needs rehashing."""
    file_path = os.path.join(temp_workspace, "test.txt")
    with open(file_path, "w") as f:
        f.write("hello")
    
    # Needs rehash if no hash provided
    assert MetadataCache.needs_rehash(file_path, None) is True
    
    # Cache the current state
    fake_hash = "abc"
    # Populate cache manually for test
    MetadataCache._cache = {}
    MetadataCache.needs_rehash(file_path, fake_hash)
    
    # Should not need rehash now
    assert MetadataCache.needs_rehash(file_path, fake_hash) is False
    
    # Modify file -> should need rehash
    import time
    time.sleep(0.1) # Ensure mtime changes
    with open(file_path, "a") as f:
        f.write(" world")
    
    assert MetadataCache.needs_rehash(file_path, fake_hash) is True

def test_standardize_nl_date():
    """Test natural language date standardization."""
    import re
    from src.utils import NL_DATE_PATTERN
    
    text = "January 31st, 2025"
    match = re.search(NL_DATE_PATTERN, text)
    assert match is not None
    assert standardize_nl_date(match) == "2025-01-31"

def test_parse_filename():
    """Test filename metadata extraction."""
    # Standard date
    meta = parse_filename("2025-01-01 Scene 1.mp4")
    assert meta["date"] == "2025-01-01"
    assert meta["number"] == 1
    assert "Scene" in meta["name"]
    
    # NL date
    meta = parse_filename("Twitter & Trailer December 6th 2025 - Scene 2.mp4")
    assert meta["date"] == "2025-12-06"
    assert meta["type"] == "TRAILER"
    assert meta["number"] == 2

def test_resolve_ssh_details():
    """Test SSH detail resolution."""
    # Static config
    config = {"ssh_host": "landlord", "ssh_port": 1234}
    host, port = resolve_ssh_details(config)
    assert host == "landlord"
    assert port == 1234
    
    # DO Droplet override
    config = {"do_droplet_ip": "5.6.7.8"}
    host, port = resolve_ssh_details(config)
    assert host == "5.6.7.8"
    assert port == 22
