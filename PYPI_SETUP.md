# PyPI Publishing Setup for IOWarp

This document describes the PyPI publishing infrastructure for the `iowarp` meta-package.

## Overview

The `iowarp` package serves as a unified entry point for the IOWarp ecosystem, automatically installing both `iowarp-core` and `iowarp-agent-toolkit` along with a unified CLI interface.

## Package Structure

```
iowarp/
├── src/iowarp/
│   ├── __init__.py          # Package initialization
│   └── cli.py               # Unified CLI interface
├── pyproject.toml           # Package configuration
├── README.md                # Package documentation
└── .github/workflows/
    └── publish-pypi.yml     # Automated publishing workflow
```

## Prerequisites

### 1. PyPI Account Setup

1. Create accounts on both:
   - **PyPI**: https://pypi.org/account/register/
   - **TestPyPI** (for testing): https://test.pypi.org/account/register/

2. Enable Two-Factor Authentication (2FA) on both accounts (required for publishing)

### 2. GitHub Repository Setup

The repository must be configured with PyPI trusted publishing (recommended) or API tokens.

#### Option A: Trusted Publishing (Recommended)

1. Go to PyPI account settings → Publishing → Add new publisher
2. Configure the trusted publisher:
   - **PyPI Project Name**: `iowarp`
   - **Owner**: Your GitHub organization/username
   - **Repository**: `iowarp`
   - **Workflow**: `publish-pypi.yml`
   - **Environment**: `pypi`

3. Repeat for TestPyPI with environment name `testpypi`

#### Option B: API Tokens (Alternative)

1. Generate API tokens on PyPI and TestPyPI
2. Add secrets to GitHub repository:
   - `PYPI_API_TOKEN`
   - `TEST_PYPI_API_TOKEN`

3. Update `.github/workflows/publish-pypi.yml` to use token authentication

## Publishing Process

### Testing Before Release

1. **Test locally**:
   ```bash
   # Build the package
   python -m build

   # Check the distribution
   twine check dist/*

   # Install locally to test
   pip install -e .

   # Test the CLI
   iowarp --help
   ```

2. **Publish to TestPyPI** (via GitHub Actions):
   ```bash
   # Trigger workflow manually from GitHub Actions UI
   # Select "Run workflow" → check "Publish to Test PyPI"
   ```

   Or push a tag with `-test` suffix:
   ```bash
   git tag v0.1.0-test
   git push origin v0.1.0-test
   ```

3. **Test installation from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
               --extra-index-url https://pypi.org/simple/ \
               iowarp
   ```

### Publishing to PyPI

1. **Create and push a release tag**:
   ```bash
   # Ensure your working tree is clean
   git status

   # Create a version tag (must match format: vX.Y.Z)
   git tag v0.1.0

   # Push the tag
   git push origin v0.1.0
   ```

2. **Create a GitHub Release**:
   - Go to GitHub → Releases → "Draft a new release"
   - Select the tag you just pushed
   - Add release notes describing changes
   - Publish the release

3. **Automated Publishing**:
   - The GitHub Actions workflow will automatically trigger
   - It will build the package and publish to PyPI
   - Monitor the workflow run in the Actions tab

## Version Management

This package uses `setuptools-scm` for automatic version management from git tags:

- **Development versions**: `0.0.0.post<N>` (based on commits since last tag)
- **Release versions**: Taken from git tags (format: `vX.Y.Z`)

Example:
```bash
# Create a new release
git tag v1.0.0
git push origin v1.0.0

# The package version will be 1.0.0
```

## Workflow Files

### `.github/workflows/publish-pypi.yml`

This workflow handles building and publishing:

1. **Trigger events**:
   - On GitHub release publication (auto-publishes to PyPI)
   - Manual workflow dispatch (can choose PyPI or TestPyPI)

2. **Jobs**:
   - `build`: Builds the distribution packages
   - `publish-to-pypi`: Publishes to PyPI (on release or manual trigger)
   - `publish-to-testpypi`: Publishes to TestPyPI (on manual trigger with flag)

## Package Dependencies

The meta-package declares dependencies on:
- `iowarp-core`: Core runtime and I/O processing
- `iowarp-agent-toolkit`: AI agent tools and MCP servers
- `click>=8.1.0`: CLI framework

**Note**: `iowarp-core` is currently under development. The package will install successfully, but runtime features may not be fully functional until core is stable.

## CLI Structure

The unified `iowarp` CLI provides:

```bash
# Default behavior - start runtime
iowarp

# Core runtime commands
iowarp core start
iowarp core stop
iowarp core compose
iowarp core refresh

# Agent toolkit commands
iowarp agent mcp-servers
iowarp agent mcp-server <name>
iowarp agent prompts
iowarp agent prompt <name>

# Version information
iowarp --version
```

## Troubleshooting

### Build Failures

If the build fails due to `iowarp-core`:
- This is expected if core is not fully functional
- The meta-package structure and CLI are still valid
- Users can install agent-toolkit independently: `pip install iowarp-agent-toolkit`

### Publishing Failures

1. **Authentication errors**: Verify trusted publisher configuration or API tokens
2. **Version conflicts**: Ensure you're using a new version number
3. **Missing files**: Check that `MANIFEST.in` includes all necessary files

### Testing Issues

To test without installing dependencies:
```bash
# Install only click
pip install click

# Test CLI directly
PYTHONPATH=src python -m iowarp.cli --help
```

## Support

- **GitHub Issues**: https://github.com/iowarp/iowarp/issues
- **Documentation**: https://www.iowarp.ai/docs
- **Website**: https://www.iowarp.ai
