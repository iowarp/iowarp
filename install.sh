#!/bin/bash
#
# IOWarp Standalone Installer
#
# Download and run with:
#   curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | bash
# Or with custom install prefix:
#   curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | INSTALL_PREFIX=$HOME/iowarp bash
# Or with build configuration options:
#   curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | WRP_CORE_ENABLE_MPI=ON WRP_CORE_ENABLE_TESTS=ON WRP_CORE_ENABLE_BENCHMARKS=ON bash
#

set -e  # Exit on error

# Default install prefix
: ${INSTALL_PREFIX:=/usr/local}

# Build configuration variables (can be set via environment or command line)
: ${WRP_CORE_ENABLE_MPI:=}
: ${WRP_CORE_ENABLE_TESTS:=}
: ${WRP_CORE_ENABLE_BENCHMARKS:=}

# Export INSTALL_PREFIX
export INSTALL_PREFIX

# Export all environment variables with specific prefixes
for var in $(compgen -e); do
    if [[ "$var" =~ ^(WRP_CORE_ENABLE_|WRP_CTE_ENABLE_|WRP_CAE_ENABLE_|WRP_CEE_ENABLE_|HSHM_ENABLE_|WRP_CTP_ENABLE_|WRP_RUNTIME_ENABLE_|CHIMAERA_ENABLE_) ]]; then
        export "$var"
        echo "Forwarding $var"
    fi
done

# Create temporary working directory
WORK_DIR=$(mktemp -d)
trap "echo 'Cleaning up temporary directory...'; rm -rf '$WORK_DIR'" EXIT

cd "$WORK_DIR"

echo "=== IOWarp Installation Script ==="
echo "Install prefix: $INSTALL_PREFIX"
echo "Temporary directory: $WORK_DIR"

# Check for pip installation
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "Error: pip is not installed. Please install pip first:"
    echo "  - Debian/Ubuntu: sudo apt-get install python3-pip"
    echo "  - RHEL/CentOS: sudo yum install python3-pip"
    echo "  - macOS: python3 -m ensurepip --upgrade"
    exit 1
fi

# Determine pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# Check for uvx installation, install if not present
if ! command -v uvx &> /dev/null; then
    echo "uvx not found, installing uv..."
    $PIP_CMD install uv
fi

# Clone iowarp-core repository with submodules
if [ ! -d "core" ]; then
    echo "Cloning iowarp-core with submodules..."
    git clone --recurse-submodules https://github.com/iowarp/core.git
else
    echo "iowarp-core already exists, skipping clone..."
fi

# Check if we're in a virtual environment before installing Python packages
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Error: Not running in a Python virtual environment."
    echo "Please activate a virtual environment first:"
    echo "  - Create venv: python3 -m venv .venv"
    echo "  - Activate venv: source .venv/bin/activate"
    echo "  - Or use conda: conda activate <env-name>"
    exit 1
fi

# Run iowarp-core install.sh with INSTALL_PREFIX
echo "Running iowarp-core install.sh with INSTALL_PREFIX=$INSTALL_PREFIX..."
cd core
if [ -f "install.sh" ]; then
    # chmod +x install.sh
    # INSTALL_PREFIX="$INSTALL_PREFIX" ./install.sh
    pip install -v .
else
    echo "Error: install.sh not found in iowarp-core"
    exit 1
fi
cd ..

# Install iowarp-agent-toolkit using uvx
echo "Installing iowarp-agent-toolkit..."
pip install iowarp-agent-toolkit

echo ""
echo "=== IOWarp installation complete ==="
echo "Installed to: $INSTALL_PREFIX"
