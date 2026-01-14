FROM iowarp/iowarp-base:latest
LABEL maintainer="llogan@hawk.iit.edu"
LABEL version="0.0"
LABEL description="IOWarp dependencies Docker image"

# Disable prompt during packages installation.
ARG DEBIAN_FRONTEND=noninteractive

# Update iowarp-install repo
RUN cd ${HOME}/iowarp-install && \
    git fetch origin && \
    git pull origin main

# Update grc-repo repo
RUN cd ${HOME}/grc-repo && \
    git pull origin main

#------------------------------------------------------------
# Conda Dependencies
#------------------------------------------------------------

# Install all development dependencies via conda
# This avoids library conflicts between system packages and conda packages
# Dependencies installed:
#   - Build tools: cmake, ninja, conda-build
#   - Core libraries: boost, hdf5, yaml-cpp, zeromq, cppzmq, cereal
#   - Testing: catch2
#   - Network: libcurl, openssl
#   - Compression: zlib
#   - Optional: poco (for Globus support), nlohmann_json
RUN /home/iowarp/miniconda3/bin/conda install -y \
    conda-build \
    cmake \
    ninja \
    boost \
    hdf5 \
    yaml-cpp \
    zeromq \
    cppzmq \
    cereal \
    catch2 \
    libcurl \
    openssl \
    zlib \
    poco \
    nlohmann_json \
    && /home/iowarp/miniconda3/bin/conda clean -ya

# Set conda environment variables for CMake to find packages
# These allow pkg-config and CMake to locate conda-installed libraries
ENV CONDA_PREFIX=/home/iowarp/miniconda3
ENV PKG_CONFIG_PATH=/home/iowarp/miniconda3/lib/pkgconfig:${PKG_CONFIG_PATH}
ENV CMAKE_PREFIX_PATH=/home/iowarp/miniconda3:${CMAKE_PREFIX_PATH}

#------------------------------------------------------------
# System Dependencies (not available via conda)
#------------------------------------------------------------

# Install system packages not provided by conda
USER root
RUN apt-get update && apt-get install -y \
    libelf-dev \
    && rm -rf /var/lib/apt/lists/*
# NOTE: The following apt packages are now provided by conda and commented out:
#   cmake, g++, doxygen, git (build tools - cmake from conda, others in base)
#   libboost-all-dev (conda boost)
#   libzmq3-dev (conda zeromq)
#   libssl-dev (conda openssl)
#   libhdf5-dev hdf5-tools (conda hdf5)
#   pkg-config (in base image)
#   python3 python3-pip (in base image)

# Install MPI (openmpi) - not available via conda in our setup
RUN apt-get update && apt-get install -y \
    openmpi-bin \
    libopenmpi-dev \
    mpi-default-dev \
    && rm -rf /var/lib/apt/lists/*

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# Switch back to iowarp user
USER iowarp
WORKDIR /home/iowarp

# Configure Spack to use conda packages
# Note: conda packages are in /home/iowarp/miniconda3
RUN mkdir -p ~/.spack && \
    echo "packages:" > ~/.spack/packages.yaml && \
    echo "  cmake:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: cmake" >> ~/.spack/packages.yaml && \
    echo "      prefix: /home/iowarp/miniconda3" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml && \
    echo "  boost:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: boost" >> ~/.spack/packages.yaml && \
    echo "      prefix: /home/iowarp/miniconda3" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml && \
    echo "  openmpi:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: openmpi" >> ~/.spack/packages.yaml && \
    echo "      prefix: /usr" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml && \
    echo "  hdf5:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: hdf5" >> ~/.spack/packages.yaml && \
    echo "      prefix: /home/iowarp/miniconda3" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml && \
    echo "  python:" >> ~/.spack/packages.yaml && \
    echo "    externals:" >> ~/.spack/packages.yaml && \
    echo "    - spec: python" >> ~/.spack/packages.yaml && \
    echo "      prefix: /usr" >> ~/.spack/packages.yaml && \
    echo "    buildable: false" >> ~/.spack/packages.yaml
