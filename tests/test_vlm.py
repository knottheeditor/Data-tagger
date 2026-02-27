import pytest
import json
import os
import base64
from unittest.mock import MagicMock, patch
from src.vlm import VLMClient

@pytest.fixture
def vlm_client():
    return VLMClient(api_url="http://localhost:11434/v1", model_name="test-model")

def test_vlm_caching(vlm_client):
    """Test that VLMClient caches results to avoid redundant calls."""
    # Mock requests.post to avoid actual network calls
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": {"content": "Test description"}}
    
    with patch("requests.post", return_value=mock_resp) as mock_post:
        # First call: should call requests.post
        res1 = vlm_client.analyze_frames([], "test prompt")
        assert res1 == "Test description"
        assert mock_post.call_count == 1
        
        # Second call: should hit cache
        res2 = vlm_client.analyze_frames([], "test prompt")
        assert res2 == "Test description"
        assert mock_post.call_count == 1 # Still 1

def test_image_pre_encoding(vlm_client, temp_workspace):
    """Test that image pre-encoding works and is passed to analysis."""
    img_path = os.path.join(temp_workspace, "test.png")
    with open(img_path, "wb") as f:
        f.write(b"dummy image")
        
    encoded = vlm_client._encode_image(img_path)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

def test_parallel_burst_logic(vlm_client, temp_workspace):
    """Test the parallel pipeline trigger (get_metadata_from_video)."""
    img_paths = [os.path.join(temp_workspace, f"f{i}.png") for i in range(4)]
    for p in img_paths:
        with open(p, "wb") as f: f.write(b"data")
        
    mock_desc = "INTENSITY: 5/10. Action description."
    mock_synth = "Synthesized description."
    mock_tags = "tag1, tag2"
    
    with patch.object(vlm_client, 'analyze_frames') as mock_analyze:
        # 1. Burst analysis, 2. Synthesis, 3. Tag audit
        mock_analyze.side_effect = [mock_desc, mock_synth, mock_tags]
        
        result = vlm_client.get_metadata_from_video(img_paths)
        
        # 4 images = 1 burst + 1 synth + 1 tag = 3 calls
        assert mock_analyze.call_count == 3
        assert "Synthesized" in result["description"]
