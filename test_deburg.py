import unittest
from unittest.mock import patch

import deburg


class DeburgTests(unittest.TestCase):
    @patch("deburg.subprocess.check_output", side_effect=FileNotFoundError)
    def test_run_cmd_returns_empty_when_adb_missing(self, _mock_check_output):
        self.assertEqual(deburg.run_cmd("adb devices"), "")

    @patch("deburg.check_device", return_value=False)
    @patch("deburg.log")
    def test_monitor_once_handles_missing_device(self, mock_log, _mock_check_device):
        deburg.monitor_once()
        mock_log.assert_any_call("[!] No device connected")

    @patch("deburg.check_device", return_value=True)
    @patch("deburg.get_screen_state", return_value="SCREEN_ON")
    @patch("deburg.get_lock_state", return_value="LOCKED")
    def test_collect_status_returns_snapshot(self, _mock_lock, _mock_screen, _mock_device):
        snapshot = deburg.collect_status()
        self.assertTrue(snapshot["connected"])
        self.assertEqual(snapshot["screen"], "SCREEN_ON")
        self.assertEqual(snapshot["lock"], "LOCKED")
        self.assertEqual(snapshot["status"], "SCREEN_ON | LOCKED")


if __name__ == "__main__":
    unittest.main()
