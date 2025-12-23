# Install Ubuntu.
FROM ubuntu:24.04
LABEL maintainer="llogan@hawk.iit.edu"
LABEL version="0.0"
LABEL description="IoWarp spack docker image"

# Disable prompt during packages installation.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y

# Install basic packages.
# NOTE: The following packages have been moved to conda and are commented out:
#   cmake, openssl, libssl-dev, zlib1g-dev, hdf5-tools
# They are still listed here in case we need to restore apt versions in the future.
RUN apt install -y \
    openssh-server \
    sudo git \
    gcc g++ gfortran make binutils gpg \
    tar zip xz-utils bzip2 \
    perl m4 libncurses5-dev libxml2-dev diffutils \
    pkg-config \
    python3 python3-pip python3-venv doxygen \
    lcov \
    build-essential ca-certificates \
    coreutils curl wget \
    lsb-release unzip liblz4-dev \
    bash jq gdbserver gdb gh nano vim dos2unix \
    clangd clang-format clang-tidy npm \
    redis-server redis-tools \
    gnupg \
    net-tools lsof iproute2 \
    && rm -rf /var/lib/apt/lists/*
# Commented apt packages now provided by conda:
#   cmake \
#   openssl libssl-dev \
#   zlib1g-dev \
#   hdf5-tools \

#------------------------------------------------------------
# User Configuration
#------------------------------------------------------------

# Create non-root user with sudo privileges
RUN useradd -m -s /bin/bash -G sudo iowarp && \
    echo "iowarp ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    passwd -d iowarp

# Switch to non-root user
USER iowarp
ENV USER="iowarp"
ENV HOME="/home/iowarp"
WORKDIR /home/iowarp

#------------------------------------------------------------
# Conda Installation
#------------------------------------------------------------

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /home/iowarp/miniconda3 \
    && rm /tmp/miniconda.sh

# Initialize conda for bash
RUN /home/iowarp/miniconda3/bin/conda init bash \
    && /home/iowarp/miniconda3/bin/conda config --add channels conda-forge \
    && /home/iowarp/miniconda3/bin/conda config --set channel_priority strict

# Accept Anaconda Terms of Service and install all development dependencies via conda
# This avoids library conflicts between system packages and conda packages
# Dependencies installed:
#   - Build tools: cmake, ninja, conda-build
#   - Core libraries: boost, hdf5, yaml-cpp, zeromq, cppzmq, cereal
#   - Testing: catch2
#   - Network: libcurl, openssl
#   - Compression: zlib
#   - Optional: poco (for Globus support), nlohmann_json
RUN /home/iowarp/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && /home/iowarp/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r \
    && /home/iowarp/miniconda3/bin/conda install -y \
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

#------------------------------------------------------------
# Python Virtual Environment
#------------------------------------------------------------

# Create Python virtual environment in user's home directory
# Note: Users can choose between conda environments or venv
RUN python3 -m venv /home/iowarp/venv \
    && /home/iowarp/venv/bin/pip install --upgrade pip setuptools wheel \
    && /home/iowarp/venv/bin/pip install pyyaml nanobind

#------------------------------------------------------------
# Spack Configuration
#------------------------------------------------------------

# Setup basic environment.
ENV SPACK_DIR="${HOME}/spack"
ENV SPACK_VERSION="v0.23.0"

# Install Spack.
RUN git clone -b ${SPACK_VERSION} https://github.com/spack/spack ${SPACK_DIR} && \
    . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack external find

# Add GRC Spack repo.
RUN git clone https://github.com/grc-iit/grc-repo.git ${HOME}/grc-repo && \
    . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack repo add ${HOME}/grc-repo

# Add IOWarp Spack repo.
RUN git clone https://github.com/iowarp/iowarp-install.git ${HOME}/iowarp-install && \
    . "${SPACK_DIR}/share/spack/setup-env.sh" && \
    spack repo add ${HOME}/iowarp-install/iowarp-spack

#------------------------------------------------------------
# SSH Configuration
#------------------------------------------------------------

# Configure SSH for iowarp user
RUN mkdir -p ~/.ssh && \
    echo "Host *" >> ~/.ssh/config && \
    echo "    StrictHostKeyChecking no" >> ~/.ssh/config && \
    chmod 600 ~/.ssh/config

# Enable passwordless SSH (requires root)
USER root
RUN sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords yes/' /etc/ssh/sshd_config && \
    mkdir -p /run/sshd

#------------------------------------------------------------
# Claude Code Installation
#------------------------------------------------------------

# Install Claude Code globally using npm
RUN npm install -g @anthropic-ai/claude-code

#------------------------------------------------------------
# uvx Package Manager Installation
#------------------------------------------------------------

# Install uvx (standalone tool runner for Python)
RUN pip3 install --break-system-packages uv

# Switch back to iowarp user
USER iowarp

#------------------------------------------------------------
# Environment Configuration
#------------------------------------------------------------

# Add conda activation and spack to bashrc
# Conda base environment is auto-activated to ensure all conda dependencies are available
RUN echo '' >> /home/iowarp/.bashrc \
    && echo '# >>> conda initialize >>>' >> /home/iowarp/.bashrc \
    && echo '# Conda base environment is auto-activated with all dev dependencies' >> /home/iowarp/.bashrc \
    && echo '# This includes: boost, hdf5, yaml-cpp, zeromq, cereal, catch2, etc.' >> /home/iowarp/.bashrc \
    && echo '# Create custom environments if needed: conda create -n myenv' >> /home/iowarp/.bashrc \
    && echo 'eval "$(/home/iowarp/miniconda3/bin/conda shell.bash hook)"' >> /home/iowarp/.bashrc \
    && echo '# <<< conda initialize <<<' >> /home/iowarp/.bashrc \
    && echo '' >> /home/iowarp/.bashrc \
    && echo '# Spack environment' >> /home/iowarp/.bashrc \
    && echo 'source ${SPACK_DIR}/share/spack/setup-env.sh' >> /home/iowarp/.bashrc \
    && echo '' >> /home/iowarp/.bashrc \
    && echo '# Python virtual environment (alternative to conda)' >> /home/iowarp/.bashrc \
    && echo '# Note: venv is NOT recommended when using conda dependencies' >> /home/iowarp/.bashrc \
    && echo '# Uncomment to auto-activate venv instead of conda (use at your own risk):' >> /home/iowarp/.bashrc \
    && echo '# if [ -f /home/iowarp/venv/bin/activate ]; then' >> /home/iowarp/.bashrc \
    && echo '#     source /home/iowarp/venv/bin/activate' >> /home/iowarp/.bashrc \
    && echo '# fi' >> /home/iowarp/.bashrc

WORKDIR /workspace

# Start SSH on container startup (using sudo since iowarp user has NOPASSWD)
CMD sudo service ssh start && /bin/bash
