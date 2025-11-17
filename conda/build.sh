#!/bin/bash

set -e

# Initialize and update git submodules
git submodule update --init --recursive

# Collect environment variables with specific prefixes to forward to cmake
CMAKE_EXTRA_ARGS=()
for var in $(compgen -e); do
    if [[ "$var" =~ ^(WRP_CORE_ENABLE_|WRP_CTE_ENABLE_|WRP_CAE_ENABLE_|WRP_CEE_ENABLE_|HSHM_ENABLE_|WRP_CTP_ENABLE_|WRP_RUNTIME_ENABLE_|CHIMAERA_ENABLE_) ]]; then
        CMAKE_EXTRA_ARGS+=("-D${var}=${!var}")
    fi
done

echo "Forwarding environment variables to cmake:"
for arg in "${CMAKE_EXTRA_ARGS[@]}"; do
    echo "  $arg"
done
echo ""

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake .. \
    --preset minimal \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=$PREFIX \
    "${CMAKE_EXTRA_ARGS[@]}"

# Build and install
make -j${CPU_COUNT} VERBOSE=1
make install
