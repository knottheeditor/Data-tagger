import pytest
import os
import json
import shutil
import tempfile

@pytest.fixture
def temp_workspace():
    """Creates a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config(temp_workspace):
    """Creates a mock config.json in the temporary workspace."""
    config_path = os.path.join(temp_workspace, "config.json")
    config_data = {
        "ssh_host": "1.2.3.4",
        "ssh_port": 2222,
        "ssh_key": "~/test_key",
        "do_access_key": "test_access",
        "do_secret_key": "test_secret",
        "rclone_path": "mock_rclone"
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path

@pytest.fixture
def media_file(temp_workspace):
    """Creates a dummy media file."""
    file_path = os.path.join(temp_workspace, "2025-01-01 Scene 1.mp4")
    with open(file_path, "wb") as f:
        f.write(b"dummy data")
    return file_path
