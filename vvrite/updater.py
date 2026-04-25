"""GitHub Releases based update checker."""

import json
import re
import urllib.request
import urllib.error

GITHUB_API_URL = "https://api.github.com/repos/shinshow/vvrite/releases/latest"
REPOSITORY_URL = "https://github.com/shinshow/vvrite"
REQUEST_TIMEOUT = 15
COOLDOWN_SECONDS = 86400  # 24 hours


def parse_version(tag: str) -> tuple[int, int, int]:
    """Parse version tag like 'v1.2.3' or '1.2.3' into (major, minor, patch)."""
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag.strip())
    if not m:
        raise ValueError(f"Invalid version tag: {tag}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def is_newer(remote_tag: str, local_version: str) -> bool:
    """Return True if remote_tag is newer than local_version."""
    try:
        return parse_version(remote_tag) > parse_version(local_version)
    except ValueError:
        return False


def fetch_latest_release() -> dict | None:
    """Fetch the latest release from GitHub API. Returns None on failure."""
    req = urllib.request.Request(
        GITHUB_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "vvrite-updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None


def find_dmg_asset(release: dict) -> dict | None:
    """Find .dmg asset (preferred) or .zip fallback from release assets."""
    assets = release.get("assets", [])
    dmg = None
    zip_asset = None
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".dmg"):
            dmg = asset
            break
        if name.endswith(".zip") and zip_asset is None:
            zip_asset = asset
    return dmg or zip_asset


def release_page_url(release: dict | None) -> str:
    """Return the best browser URL for a release, falling back to the repo."""
    if not isinstance(release, dict):
        return REPOSITORY_URL

    html_url = release.get("html_url", "")
    if isinstance(html_url, str) and html_url.strip():
        return html_url.strip()

    return REPOSITORY_URL


def download_asset(url: str, destination: str) -> str:
    """Download file from url to destination path. Returns destination."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "vvrite-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(destination, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
    return destination


def should_check(last_timestamp: float) -> bool:
    """Return True if enough time has passed since last check."""
    import time
    return (time.time() - last_timestamp) >= COOLDOWN_SECONDS
