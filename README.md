<p align="center">
  <a href="https://www.iowarp.ai">
    <img src="https://www.iowarp.ai/img/iowarp_logo.png" alt="IOWarp logo" width="25%">
  </a>
</p>

<h1 align="center">IOWarp</h1>

<p align="center"><strong>Context Management Platform</strong></p>

<p align="center">Enabling AI agents to orchestrate large-scale data, complex multi-step workflows, and autonomous agentic orchestration.</p>

<p align="center">
  <a href="https://opensource.org/licenses/BSD-3-Clause"><img alt="License: BSD-3-Clause" src="https://img.shields.io/badge/License-BSD%203--Clause-blue.svg" /></a>
  <a href="http://github.com/iowarp"><img alt="IoWarp" src="https://img.shields.io/badge/IoWarp-GitHub-blue.svg" /></a>
  <a href="https://grc.iit.edu/"><img alt="GRC" src="https://img.shields.io/badge/GRC-Website-blue.svg" /></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.7+-yellow.svg" /></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-Compatible-blue.svg" /></a>
</p>

## Overview

**IOWarp** is a context management platform designed to accelerate scientific workflows by solving data bottlenecks using AI. It enables AI agents to orchestrate large-scale data, complex multi-step workflows, and autonomous agentic orchestration in high-performance computing environments.

This repository provides unified installation methods and tools for the entire IOWarp ecosystem. It simplifies the deployment of IOWarp's platform components - including the Content Assimilation Engine (CAE), Content Transfer Engine (CTE), Runtime, Agent Toolkit, and MCP servers - across multiple platforms and package managers.

### Key Capabilities

- **Context Engineering**: 15 specialized MCP servers for scientific computing workflows, ClaudIO agent framework, and intelligent context orchestration
- **High Performance**: Demonstrated 7.5x speedup in real-world workflows with HPC integration and efficient resource management
- **Open Source**: BSD 3-Clause licensed, $5M NSF funded, with active community support
- **Three-Tier Architecture**: Intelligence Layer (AI agents), Tool Layer (data processing), and Storage Layer (hierarchical storage management)

## Installation

### 📦 PyPI (Recommended for Python Users)

Install IOWarp and all its components via pip or uv:

```bash
# Using pip
pip install iowarp

# Using uv (faster)
uv pip install iowarp

# As a CLI tool with uvx (no installation needed)
uvx iowarp

# Install as a persistent tool
uv tool install iowarp
```

This installs:
- **iowarp-core**: High-performance I/O runtime and data processing engine (automatic fallback to GitHub releases)
- **iowarp-agent-toolkit**: AI agent tools and 15+ MCP servers for scientific computing
- **Unified CLI**: Single `iowarp` command to access all functionality

**Automatic Installation Fallback:**

The `iowarp` package includes intelligent automatic installation for `iowarp-core`:

1. **First attempt**: Checks if iowarp-core is already installed (e.g., from PyPI wheels when available)
2. **Automatic fallback**: If not found, automatically downloads and installs compatible wheels from GitHub releases
3. **Seamless experience**: Works transparently on first `import iowarp` - no manual intervention needed

This ensures:
- ✅ Installation always succeeds with `pip install iowarp`
- ✅ Works on all platforms (Linux x86_64, ARM64) even when PyPI wheels are unavailable
- ✅ Automatic updates when PyPI wheels become available (future)
- ✅ No build tools required for most users

**Platform Compatibility:**
- Linux x86_64 (manylinux_2_17)
- Linux ARM64/aarch64 (manylinux_2_17)
- Python 3.10, 3.11, 3.12, 3.13

**If automatic installation fails**, you can manually install iowarp-core from GitHub releases:
```bash
# Find your Python version
python --version  # e.g., Python 3.10.x

# Install matching wheel from GitHub releases
# Replace cp310 with your Python version (cp310, cp311, cp312, cp313)
# Replace x86_64 with aarch64 for ARM systems
pip install https://github.com/iowarp/core/releases/download/v0.6.2/iowarp_core-0.6.2-cp310-cp310-manylinux_2_17_x86_64.whl
```

**Quick Start:**

```bash
# Start IOWarp runtime (default behavior)
iowarp

# Or explicitly
iowarp core start

# Stop runtime
iowarp core stop

# List available MCP servers
iowarp agent mcp-servers

# Run an MCP server
iowarp agent mcp-server hdf5

# List prompt templates
iowarp agent prompts
```

**Note:** iowarp-core is currently under active development. Some features may not be fully functional yet.

**All individual commands remain available:**
- `iowarp-core`, `wrp_start`, `wrp_stop`, etc. (core runtime commands)
- `iowarp-agent-toolkit` (agent toolkit launcher)

### ⚡ Native Install

One way to install IOWarp is using our standalone installer script:

```bash
# Basic install (uses pip and expects a venv to be active)
curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | bash

# Custom install location
curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | INSTALL_PREFIX=$HOME/iowarp bash

# Install with build options
curl -fsSL https://raw.githubusercontent.com/iowarp/iowarp-install/main/install.sh | WRP_CORE_ENABLE_MPI=ON WRP_CORE_ENABLE_TESTS=ON WRP_CORE_ENABLE_BENCHMARKS=ON bash
```

**Environment Variables:**
- `INSTALL_PREFIX` - Installation directory (default: `/usr/local`)
- `WRP_CORE_ENABLE_MPI` - Enable MPI support (default: unset, set to `ON` to enable)
- `WRP_CORE_ENABLE_TESTS` - Build test suite (default: unset, set to `ON` to enable)
- `WRP_CORE_ENABLE_BENCHMARKS` - Build benchmarks (default: unset, set to `ON` to enable)

This will:
- Clone and build IOWarp core with all submodules
- Install the IOWarp agent toolkit
- Set up the complete IOWarp environment

### 🐳 Docker

Docker provides an alternative containerized approach. The `iowarp/iowarp:latest` image includes the complete runtime with buffering services.

1. Pull the Docker image:
```bash
docker pull iowarp/iowarp:latest
```

2. Download the `docker/user/docker-compose.yml` file. Check file [here](docker/user/docker-compose.yml):
```bash
wget https://raw.githubusercontent.com/iowarp/iowarp/main/docker/user/docker-compose.yml
```

3. Run the container:
```bash
docker-compose up -d
```

> [!NOTE] 
> The provided `docker-compose.yml` file already configures the required shared memory (`shm_size: 8g`) and shareable IPC namespace (`ipc: shareable`) settings. These are required for IOWarp to function properly.

**More on docker:**

<details>
<summary><strong>Configuration (optional)</strong></summary>

The default configuration provides up to 16GB buffer cache.
For more complexity, create a `wrp_conf.yaml` configuration file.
This is an example with some paramters, but not all:

```yaml
# IOWarp Runtime Configuration File
compose:
  # Context Transfer Engine (CTE) - handles data buffering and I/O
  - mod_name: wrp_cte_core
    pool_name: wrp_cte
    pool_query: local
    pool_id: 512.0

    # Storage block device configuration
    # This is the most important section - defines where data is buffered
    storage:
      # RAM-based storage tier (fastest)
      - path: "ram::cte_ram_tier1"
        bdev_type: "ram"
        capacity_limit: "16GB"
        score: 0.0           # Manual score override (range 0 to 1), put all data here

      # Example: Add NVMe tier (uncomment to use)
      # - path: "/dev/nvme0n1"
      #   bdev_type: "file"
      #   capacity_limit: "500GB"
      #   score: 0.5

      # Example: Add SSD tier (uncomment to use)
      # - path: "/dev/sda1"
      #   bdev_type: "file"
      #   capacity_limit: "1TB"
      #   score: 1.0

  # Context Assimilation Engine (CAE) - handles data processing and transformation
  - mod_name: wrp_cae_core
    pool_name: cae_main
    pool_query: local
    pool_id: "400.0"
```

**Storage Configuration:**
- `path` - Device path or RAM identifier (format: `ram::<name>` for RAM, `/dev/<device>` for block devices)
- `bdev_type` - Backend type: `"ram"` (memory), `"nvme"` (NVMe SSD), `"aio"` (async I/O for other block devices)
- `capacity_limit` - Maximum storage capacity (supports `KB`, `MB`, `GB`, `TB` suffixes)
- `score` - Tier priority (0.0 = lowest priority, 1.0 = highest). 0.0 means "anyone can put data here", 
while 1.0 means only put high priority data here.

Multiple storage tiers can be configured to create a hierarchical storage system. Data is automatically placed across tiers based on the data placement engine (DPE) strategy.

</details>

<details>
<summary><strong>Example: Running Benchmarks</strong></summary>

The `demos/benchmark/` directory contains a complete Docker Compose setup for running CTE benchmarks:

```bash
cd demos/benchmark

# Run default benchmark (Put test)
docker-compose up

# Run specific test with custom parameters
TEST_CASE=Get IO_SIZE=4m IO_COUNT=1000 docker-compose up
```

**Available benchmark parameters:**
- `TEST_CASE` - Benchmark test: `Put`, `Get`, `PutGet` (default: `Put`)
- `NUM_PROCS` - Number of parallel processes (default: `1`)
- `DEPTH` - Queue depth for concurrent operations (default: `4`)
- `IO_SIZE` - Size of each I/O operation with suffix `b`, `k`, `m`, `g` (default: `1m`)
- `IO_COUNT` - Number of operations to perform (default: `100`)

The benchmark compose file demonstrates:
- Separate runtime and benchmark services
- Shared memory configuration (`shm_size: 8g`)
- IPC namespace sharing for shared memory access
- Custom CTE configuration via volume mounts
- Health checks to ensure runtime readiness

</details>

### 📦 Spack

1. Install Spack package manager - [Installation guide](https://spack-tutorial.readthedocs.io/en/latest/tutorial_basics.html)
2. Add IOWarp repository:
```bash
spack repo add iowarp-spack
```
3. Install IOWarp:
```bash
spack install iowarp
```

## Resources
- **Gnosis Research Center**: [grc.iit.edu](https://grc.iit.edu/)
- **Website**: [iowarp.ai](https://www.iowarp.ai)
- **Platform Documentation**: [iowarp.ai/platform](https://www.iowarp.ai/platform)
- **Docs**: [iowarp.ai/docs/intro](https://www.iowarp.ai/docs/intro)
- **Contributing**: See [CONTRIBUTING](CONTRIBUTING.md) for guidelines
- **License**: [BSD 3-Clause License](LICENSE)
- **Support**: [GitHub Issues](https://github.com/iowarp/iowarp) | [Project Homepage](https://grc.iit.edu/research/projects/iowarp/)
