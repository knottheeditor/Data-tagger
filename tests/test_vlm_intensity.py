import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.vlm import VLMClient

class TestVLMIntensity(unittest.TestCase):
    def setUp(self):
        # Mock the API URL and other init params since we won't make network calls
        self.vlm = VLMClient(api_url="http://fake:11434")

    def test_calculate_intensity_all_high(self):
        burst_logs = [
            "ACTION_VERB: Pumping\nINTENSITY: High",
            "ACTION_VERB: Thrusting\nINTENSITY: High"
        ]
        score = self.vlm._calculate_intensity_score(burst_logs)
        self.assertEqual(score, 10, "Should be 10 for all High")

    def test_calculate_intensity_mixed(self):
        burst_logs = [
            "INTENSITY: High",   # 10
            "INTENSITY: Medium", # 7
            "INTENSITY: Low",    # 4
            "INTENSITY: None"    # 1
        ]
        # Avg: (10+7+4+1)/4 = 5.5 -> Round to 6
        score = self.vlm._calculate_intensity_score(burst_logs)
        self.assertEqual(score, 6, "Should average mixed scores correctly")

    def test_calculate_intensity_missing(self):
        burst_logs = [
            "ACTION_VERB: Posing",
            "No intensity here"
        ]
        # Default fallback is 5
        score = self.vlm._calculate_intensity_score(burst_logs)
        self.assertEqual(score, 5, "Should fall back to 5 if no intensity found")

    def test_calculate_intensity_case_insensitive(self):
        burst_logs = [
            "INTENSITY: higH",
            "intensity: LOW"
        ]
        # (10 + 4) / 2 = 7
        score = self.vlm._calculate_intensity_score(burst_logs)
        self.assertEqual(score, 7, "Should handle case insensitivity")

    def test_calculate_intensity_garbage(self):
        burst_logs = [
            "INTENSITY: SuperExtreme", # Unknown -> 1
            "INTENSITY: Medium"        # 7
        ]
        # (1 + 7) / 2 = 4
        score = self.vlm._calculate_intensity_score(burst_logs)
        self.assertEqual(score, 4, "Should handle unknown intensity as 1")

if __name__ == '__main__':
    unittest.main()
