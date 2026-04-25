"""Tests for updater module."""

import json
import time
import unittest
from unittest.mock import patch, MagicMock

from vvrite import updater


class TestRepositoryConfig(unittest.TestCase):
    def test_update_checker_uses_fork_repository(self):
        self.assertEqual(updater.REPOSITORY_URL, "https://github.com/shinshow/vvrite")
        self.assertEqual(
            updater.GITHUB_API_URL,
            "https://api.github.com/repos/shinshow/vvrite/releases/latest",
        )


class TestParseVersion(unittest.TestCase):
    def test_with_v_prefix(self):
        self.assertEqual(updater.parse_version("v1.2.3"), (1, 2, 3))

    def test_without_v_prefix(self):
        self.assertEqual(updater.parse_version("1.2.3"), (1, 2, 3))

    def test_zero_version(self):
        self.assertEqual(updater.parse_version("v0.0.1"), (0, 0, 1))

    def test_large_numbers(self):
        self.assertEqual(updater.parse_version("v10.20.30"), (10, 20, 30))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            updater.parse_version("not-a-version")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            updater.parse_version("")

    def test_whitespace_stripped(self):
        self.assertEqual(updater.parse_version("  v1.0.0  "), (1, 0, 0))


class TestIsNewer(unittest.TestCase):
    def test_newer_patch(self):
        self.assertTrue(updater.is_newer("v1.0.1", "1.0.0"))

    def test_newer_minor(self):
        self.assertTrue(updater.is_newer("v1.1.0", "1.0.0"))

    def test_newer_major(self):
        self.assertTrue(updater.is_newer("v2.0.0", "1.0.0"))

    def test_same_version(self):
        self.assertFalse(updater.is_newer("v1.0.0", "1.0.0"))

    def test_older_version(self):
        self.assertFalse(updater.is_newer("v0.9.0", "1.0.0"))

    def test_invalid_remote_returns_false(self):
        self.assertFalse(updater.is_newer("invalid", "1.0.0"))

    def test_invalid_local_returns_false(self):
        self.assertFalse(updater.is_newer("v1.0.0", "invalid"))


class TestShouldCheck(unittest.TestCase):
    def test_never_checked(self):
        self.assertTrue(updater.should_check(0.0))

    def test_recently_checked(self):
        self.assertFalse(updater.should_check(time.time() - 3600))  # 1 hour ago

    def test_old_check(self):
        self.assertTrue(updater.should_check(time.time() - 90000))  # 25 hours ago


class TestFindDmgAsset(unittest.TestCase):
    def test_finds_dmg(self):
        release = {
            "assets": [
                {"name": "vvrite-1.1.0.zip", "browser_download_url": "https://example.com/a.zip"},
                {"name": "vvrite-1.1.0.dmg", "browser_download_url": "https://example.com/a.dmg"},
            ]
        }
        asset = updater.find_dmg_asset(release)
        self.assertEqual(asset["name"], "vvrite-1.1.0.dmg")

    def test_falls_back_to_zip(self):
        release = {
            "assets": [
                {"name": "vvrite-1.1.0.zip", "browser_download_url": "https://example.com/a.zip"},
            ]
        }
        asset = updater.find_dmg_asset(release)
        self.assertEqual(asset["name"], "vvrite-1.1.0.zip")

    def test_no_matching_asset(self):
        release = {
            "assets": [
                {"name": "source.tar.gz", "browser_download_url": "https://example.com/a.tar.gz"},
            ]
        }
        self.assertIsNone(updater.find_dmg_asset(release))

    def test_empty_assets(self):
        self.assertIsNone(updater.find_dmg_asset({"assets": []}))

    def test_no_assets_key(self):
        self.assertIsNone(updater.find_dmg_asset({}))


class TestReleasePageUrl(unittest.TestCase):
    def test_uses_release_html_url(self):
        release = {"html_url": "https://github.com/shinshow/vvrite/releases/tag/v1.2.3"}
        self.assertEqual(
            updater.release_page_url(release),
            "https://github.com/shinshow/vvrite/releases/tag/v1.2.3",
        )

    def test_falls_back_to_repo_when_missing(self):
        self.assertEqual(updater.release_page_url({}), updater.REPOSITORY_URL)

    def test_falls_back_to_repo_for_invalid_release(self):
        self.assertEqual(updater.release_page_url(None), updater.REPOSITORY_URL)


class TestFetchLatestRelease(unittest.TestCase):
    @patch("vvrite.updater.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        data = {"tag_name": "v1.1.0", "assets": []}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = updater.fetch_latest_release()
        self.assertEqual(result["tag_name"], "v1.1.0")

    @patch("vvrite.updater.urllib.request.urlopen")
    def test_network_error_returns_none(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("network error")
        self.assertIsNone(updater.fetch_latest_release())


if __name__ == "__main__":
    unittest.main()
