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
import platform
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


# GitHub repository information
GITHUB_OWNER = "iowarp"
GITHUB_REPO = "core"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

# Cache file to avoid repeated installation attempts
CACHE_DIR = Path.home() / ".cache" / "iowarp"
INSTALL_CACHE_FILE = CACHE_DIR / "core_install_attempted"


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


def mark_install_attempted():
    """Mark that we've attempted installation to avoid repeated failures."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INSTALL_CACHE_FILE.write_text("attempted")


def has_install_been_attempted() -> bool:
    """Check if we've already attempted installation in this environment."""
    return INSTALL_CACHE_FILE.exists()


def install_iowarp_core_with_fallback() -> bool:
    """
    Main entry point for installing iowarp-core with fallback logic.

    This function is called when iowarp_core cannot be imported.
    It attempts to install from GitHub releases as a fallback.

    Returns:
        True if installation succeeded, False otherwise
    """
    # Check if we've already tried
    if has_install_been_attempted():
        return False

    # Mark that we're attempting installation
    mark_install_attempted()

    # Try GitHub fallback
    success = try_github_fallback()

    if not success:
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
