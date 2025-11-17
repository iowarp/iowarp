"""
IOWarp - A wrapper package for IOWarp components

This package installs both iowarp-agent-toolkit and iowarp-core.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("iowarp")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0.dev0"

# Try to import the underlying packages to verify they're installed
try:
    import iowarp_agent_toolkit
except ImportError:
    pass

#Try to import iowarp_core with automatic fallback installation
_core_import_attempted = False
_core_available = False

try:
    import iowarp_core
    _core_available = True
except ImportError:
    if not _core_import_attempted:
        # Attempt automatic installation from GitHub releases
        _core_import_attempted = True
        import sys
        print("\nIOWarp Core not found. Attempting automatic installation from GitHub releases...", file=sys.stderr)

        try:
            from ._installer import install_iowarp_core_with_fallback

            if install_iowarp_core_with_fallback():
                # Installation succeeded, try importing again
                try:
                    import iowarp_core
                    _core_available = True
                    print("IOWarp Core successfully installed and imported!", file=sys.stderr)
                except ImportError:
                    print("Warning: IOWarp Core installation reported success but import still failed.", file=sys.stderr)
                    print("You may need to restart your Python session.", file=sys.stderr)
        except Exception as e:
            print(f"Error during automatic installation: {e}", file=sys.stderr)

def is_core_available() -> bool:
    """Check if iowarp-core is available."""
    return _core_available
