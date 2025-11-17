"""
Automatic installation fallback system for iowarp-core.

This module implements a multi-tier fallback strategy to install iowarp-core:
1. PyPI wheel (pip's default, handled automatically)
2. GitHub release wheel (fallback if PyPI fails or wheel unavailable)
3. PyPI source (pip's default fallback, handled automatically)
4. GitHub source (last resort, not yet implemented)

The fallback logic is triggered on first import if iowarp_core is not available.
"""

import sys
import os
import platform
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


# GitHub repository information
GITHUB_OWNER = "iowarp"
GITHUB_REPO = "core"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

# Cache file to avoid repeated installation attempts
# Use per-environment cache for virtual environments
def _get_cache_dir() -> Path:
    """
    Get cache directory for installation state.

    For virtual environments, uses the venv directory to allow
    independent retry attempts per environment.
    For system Python, uses user cache directory.
    """
    # Check if running in a virtual environment
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        # Virtual environment - use venv-specific cache
        return Path(sys.prefix) / ".iowarp_cache"
    # System Python - use user cache directory
    return Path.home() / ".cache" / "iowarp"

CACHE_DIR = _get_cache_dir()
INSTALL_CACHE_FILE = CACHE_DIR / "core_install_state.json"


def get_platform_info() -> Tuple[str, str, str]:
    """
    Get current platform information for wheel compatibility.

    Returns:
        Tuple of (python_tag, abi_tag, platform_tag)
        Example: ('cp310', 'cp310', 'manylinux_2_17_x86_64')
    """
    py_version = sys.version_info
    python_tag = f"cp{py_version.major}{py_version.minor}"
    abi_tag = python_tag  # For CPython, ABI tag matches python tag

    # Determine platform tag
    system = platform.system()
    machine = platform.machine()

    if system == "Linux":
        # Map machine architecture
        arch_map = {
            "x86_64": "x86_64",
            "aarch64": "aarch64",
            "arm64": "aarch64",  # macOS ARM reports as arm64
        }
        arch = arch_map.get(machine, machine)
        platform_tag = f"manylinux_2_17_{arch}"
    elif system == "Darwin":
        # macOS
        platform_tag = f"macosx_10_9_{machine}"
    elif system == "Windows":
        arch = "amd64" if machine == "AMD64" else "win32"
        platform_tag = f"win_{arch}"
    else:
        platform_tag = f"{system.lower()}_{machine}"

    return python_tag, abi_tag, platform_tag


def find_compatible_wheel(release_assets: list, python_tag: str, platform_tag: str) -> Optional[str]:
    """
    Find a compatible wheel from GitHub release assets.

    Args:
        release_assets: List of asset dictionaries from GitHub API
        python_tag: Python version tag (e.g., 'cp310')
        platform_tag: Platform tag (e.g., 'manylinux_2_17_x86_64')

    Returns:
        Download URL of compatible wheel, or None if not found
    """
    for asset in release_assets:
        name = asset.get("name", "")
        if not name.endswith(".whl"):
            continue

        # Wheel filename format: iowarp_core-{version}-{python}-{abi}-{platform}.whl
        # Check if wheel matches our platform
        if python_tag in name and platform_tag in name:
            return asset.get("browser_download_url")

    return None


def get_latest_release_with_wheels() -> Optional[dict]:
    """
    Get the latest GitHub release that has wheel assets.

    Returns:
        Release information dict, or None if no suitable release found
    """
    try:
        # Use GitHub API to get releases
        req = Request(GITHUB_RELEASES_API)
        req.add_header("Accept", "application/vnd.github.v3+json")

        with urlopen(req, timeout=10) as response:
            releases = json.loads(response.read().decode())

        # Find the latest release with wheel assets
        for release in releases:
            if release.get("draft") or release.get("prerelease"):
                continue

            assets = release.get("assets", [])
            # Check if this release has any wheel files
            has_wheels = any(asset.get("name", "").endswith(".whl") for asset in assets)

            if has_wheels:
                return release

        return None

    except (HTTPError, URLError, json.JSONDecodeError) as e:
        print(f"Warning: Could not fetch GitHub releases: {e}", file=sys.stderr)
        return None


def install_from_github_wheel(wheel_url: str) -> bool:
    """
    Install iowarp-core from a GitHub release wheel URL.

    Args:
        wheel_url: Direct download URL for the wheel file

    Returns:
        True if installation succeeded, False otherwise
    """
    print(f"Installing iowarp-core from GitHub release wheel...", file=sys.stderr)
    print(f"  URL: {wheel_url}", file=sys.stderr)

    # Try multiple installation methods to support different package managers
    install_methods = [
        # Method 1: Try uv pip (for uv virtual environments)
        (["uv", "pip", "install", "--no-deps", wheel_url], "uv pip"),
        # Method 2: Try standard pip module
        ([sys.executable, "-m", "pip", "install", "--no-deps", wheel_url], "python -m pip"),
        # Method 3: Try direct pip command
        (["pip", "install", "--no-deps", wheel_url], "pip"),
    ]

    for cmd, method_name in install_methods:
        try:
            print(f"  Trying {method_name}...", file=sys.stderr)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                print(f"Successfully installed iowarp-core from GitHub release using {method_name}", file=sys.stderr)
                return True
            else:
                # Don't print error for methods that simply aren't available
                if "No module named pip" not in result.stderr and "command not found" not in result.stderr:
                    print(f"  {method_name} failed: {result.stderr.strip()[:100]}", file=sys.stderr)

        except FileNotFoundError:
            # Command not found, try next method
            continue
        except subprocess.TimeoutExpired:
            print(f"  {method_name} timed out", file=sys.stderr)
            continue
        except Exception as e:
            print(f"  {method_name} error: {e}", file=sys.stderr)
            continue

    # All methods failed
    print(f"Failed to install wheel using any available method", file=sys.stderr)
    return False


def try_github_fallback() -> bool:
    """
    Attempt to install iowarp-core from GitHub releases.

    Returns:
        True if installation succeeded, False otherwise
    """
    # Get platform information
    python_tag, _, platform_tag = get_platform_info()

    print(f"Attempting GitHub fallback installation for {python_tag} on {platform_tag}...", file=sys.stderr)

    # Find latest release with wheels
    release = get_latest_release_with_wheels()
    if not release:
        print("No GitHub releases with wheels found", file=sys.stderr)
        return False

    version = release.get("tag_name", "unknown")
    print(f"Found release: {version}", file=sys.stderr)

    # Find compatible wheel
    assets = release.get("assets", [])
    wheel_url = find_compatible_wheel(assets, python_tag, platform_tag)

    if not wheel_url:
        print(f"No compatible wheel found for {python_tag} on {platform_tag}", file=sys.stderr)
        print("Available wheels:", file=sys.stderr)
        for asset in assets:
            if asset.get("name", "").endswith(".whl"):
                print(f"  - {asset['name']}", file=sys.stderr)
        return False

    # Install the wheel
    return install_from_github_wheel(wheel_url)


def mark_install_result(success: bool, error_msg: str = ""):
    """
    Mark installation result with smart retry logic.

    Args:
        success: Whether installation succeeded
        error_msg: Error message if failed (optional)
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if success:
        # Successful installation - cache permanently
        result = {
            "success": True,
            "timestamp": time.time(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "platform": platform.platform()
        }
    else:
        # Failed installation - track attempts for exponential backoff
        data = {}
        if INSTALL_CACHE_FILE.exists():
            try:
                data = json.loads(INSTALL_CACHE_FILE.read_text())
            except:
                pass

        result = {
            "success": False,
            "attempts": data.get("attempts", 0) + 1,
            "last_attempt": time.time(),
            "error": error_msg,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "platform": platform.platform()
        }

    INSTALL_CACHE_FILE.write_text(json.dumps(result, indent=2))


def should_retry_install() -> bool:
    """
    Check if installation should be retried.

    Uses exponential backoff for failed attempts:
    - 1st failure: retry after 1 minute
    - 2nd failure: retry after 5 minutes
    - 3rd failure: retry after 1 hour
    - 4th+ failures: retry after 24 hours

    Returns:
        True if installation should be attempted, False otherwise
    """
    # Allow force retry via environment variable
    if os.environ.get("IOWARP_FORCE_INSTALL", "").lower() in ("true", "1", "yes"):
        print("  Forcing installation attempt (IOWARP_FORCE_INSTALL set)", file=sys.stderr)
        return True

    if not INSTALL_CACHE_FILE.exists():
        return True

    try:
        data = json.loads(INSTALL_CACHE_FILE.read_text())

        # If installation succeeded, don't retry
        if data.get("success"):
            return False

        # Exponential backoff intervals (in seconds)
        # 1min, 5min, 1hour, 24hours
        backoff_intervals = [60, 300, 3600, 86400]
        attempts = data.get("attempts", 0)
        last_attempt = data.get("last_attempt", 0)

        # Calculate required wait time based on number of attempts
        required_wait = backoff_intervals[min(attempts - 1, len(backoff_intervals) - 1)]
        elapsed = time.time() - last_attempt

        if elapsed < required_wait:
            wait_remaining = int(required_wait - elapsed)
            if wait_remaining < 120:
                wait_str = f"{wait_remaining} seconds"
            elif wait_remaining < 7200:
                wait_str = f"{wait_remaining // 60} minutes"
            else:
                wait_str = f"{wait_remaining // 3600} hours"

            print(f"  Retry blocked by exponential backoff (attempt {attempts})", file=sys.stderr)
            print(f"  Wait {wait_str} before retry, or set IOWARP_FORCE_INSTALL=true", file=sys.stderr)
            print(f"  Cache location: {INSTALL_CACHE_FILE}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        # Corrupted cache - allow retry
        print(f"  Warning: Cache file corrupted ({e}), allowing retry", file=sys.stderr)
        return True


def install_iowarp_core_with_fallback() -> bool:
    """
    Main entry point for installing iowarp-core with fallback logic.

    This function is called when iowarp_core cannot be imported.
    It attempts to install from GitHub releases as a fallback.

    Returns:
        True if installation succeeded, False otherwise
    """
    # Check if we should retry installation
    if not should_retry_install():
        return False

    # Try GitHub fallback
    success = try_github_fallback()

    # Mark result for future retry logic
    if success:
        mark_install_result(success=True)
    else:
        mark_install_result(success=False, error_msg="GitHub fallback installation failed")

        print("\nFailed to install iowarp-core automatically.", file=sys.stderr)
        print("\nManual installation options:", file=sys.stderr)
        print("1. Install from GitHub release (recommended):", file=sys.stderr)

        python_tag, _, platform_tag = get_platform_info()
        print(f"   pip install https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v0.6.2/iowarp_core-0.6.2-{python_tag}-{python_tag}-{platform_tag}.whl", file=sys.stderr)

        print("\n2. Build from source (requires build tools):", file=sys.stderr)
        print("   pip install iowarp-core --no-binary iowarp-core", file=sys.stderr)

        print("\n3. See installation guide:", file=sys.stderr)
        print(f"   https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}#installation", file=sys.stderr)

    return success

























