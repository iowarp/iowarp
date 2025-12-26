# Kubernetes Deployment with Hostfile

This guide covers deploying applications on Kubernetes using the `deploy_from_hostfile.sh` script, which automatically generates a hostfile from cluster nodes and deploys on all worker nodes.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Creating a Kubernetes Cluster](#kubernetes-cluster-setup)
3. [Deployment using deploy_from_hostfile.sh](#using-deploy_from_hostfilesh)
4. [Testing the Deployment](#testing-the-deployment)
5. [IoWarp Deployment](#iowarp-deployment)


## Prerequisites

- Ubuntu 22.04 LTS on all nodes
- Root or sudo kubernetes access on all nodes
- Network connectivity between nodes
- Install Docker and Kubernetes on All Nodes

## Creating a Kubernetes Cluster

### 1. Initialize the Master Node

On the master node (control plane):

```bash
# Initialize the cluster
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=<MASTER_IP>

# Set up kubectl for your user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install a CNI (Container Network Interface) - Flannel
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

### 2. Generate Join Token

On the master node, generate the join command for worker nodes:

```bash
# Generate join command with token
sudo kubeadm token create --print-join-command
```

This will output something like:
```bash
sudo kubeadm join 172.20.1.1:6443 --token abcdef.1234567890abcdef --discovery-token-ca-cert-hash sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### 3. Join Worker Nodes

On each worker node, run the join command from the previous step:

```bash
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> --discovery-token-ca-cert-hash sha256:<HASH>
```

### 4. Verify Cluster Status

```bash
# Check node status
kubectl get nodes

# Check all pods in kube-system namespace
kubectl get pods -n kube-system
```

## Deployment Using deploy_from_hostfile.sh

The `deploy_from_hostfile.sh` script automatically:
1. Generates a hostfile from your Kubernetes cluster nodes
2. Deploys applications on all worker nodes
3. Ensures exactly 1 pod per worker node
4. Uses nodeAffinity to prevent pod migration

### Script Features

- **Automatic hostfile generation** from cluster nodes
- **Excludes master node** automatically (by hostname pattern)
- **One pod per worker node** to avoid IP conflicts
- **Strict node placement** via nodeAffinity
- **No user input required** - uses default values
- **ClusterIP service** for load balancing

### Default Configuration

- **Deployment Name**: `all-nodes-app`
- **Docker Image**: `nginx:alpine`
- **Container Port**: `80`
- **Replicas per node**: `1`
- **Service Type**: `ClusterIP`

### Usage

1. **Make the script executable:**
```bash
chmod +x deploy_from_hostfile.sh
```

2. **Run the script:**
```bash
source deploy_from_hostfile.sh
```

### Verify Hostfile Contents


### Example Output

```
==========================================
Kubernetes Hostfile Generation & Deployment
==========================================

Step 1: Generating hostfile from cluster nodes...

Hostfile generated successfully!
Contents of hostfile:
====================
172.20.101.27
172.20.101.28

Step 2: Reading nodes for deployment...
  1) 172.20.101.27 (ares-comp-27)
  2) 172.20.101.28 (ares-comp-28)

Found 2 nodes in hostfile:
  - 172.20.101.27 (ares-comp-27)
  - 172.20.101.28 (ares-comp-28)

Step 3: Creating deployment on ALL nodes with following details:
======================================================
Deployment Name: all-nodes-app
Docker Image: nginx:alpine
Container Port: 80
Replicas per node: 1
Total replicas: 2
Target nodes: 172.20.101.27 172.20.101.28

Step 4: Creating deployment.yaml...
Step 5: Applying deployment to ALL nodes...
deployment.apps/all-nodes-app created
service/all-nodes-app-service created

Deployment Complete!
==========================================
Summary:
- Hostfile generated with 2 worker nodes
- Deployment created with 2 replicas
- Exactly 1 pod per worker node
- NodeAffinity ensures strict node placement
```

## Testing the Deployment

### 1. Check Deployment Status

```bash
# Check deployment status
kubectl get deployments

# Check pod status and placement
kubectl get pods -l app=all-nodes-app -o wide

# Check service status
kubectl get services -l app=all-nodes-app
```

### 2. Test Connectivity from Worker Nodes

```bash
# Get current pod IPs
kubectl get pods -l app=all-nodes-app -o wide

# Get service IP
kubectl get services -l app=all-nodes-app

# Test Pod 1 (ares-comp-27)
ssh 172.20.101.27 "curl -v http://10.88.3.34:80"

# Test Pod 2 (ares-comp-28)  
ssh 172.20.101.28 "curl -v http://10.88.3.0:80"

# Test Service Load Balancing
ssh 172.20.101.27 "curl -s http://10.110.191.202:80 | head -5"
```

### 3. Expected Results

- **Pod Status**: All pods should be in `Running` state
- **Node Placement**: Each pod should be on a different worker node
- **HTTP Response**: Should return nginx welcome page with HTTP 200 OK
- **Service Load Balancing**: Service should route traffic to both pods

## Troubleshooting

### Common Issues

#### 1. Pods in CrashLoopBackOff

```bash
# Check pod logs
kubectl logs <POD_NAME>

# Restart deployment
kubectl rollout restart deployment <DEPLOYMENT_NAME>
```

#### 2. Pods in Pending State

```bash
# Check pod events
kubectl describe pod <POD_NAME>

# Check node resources
kubectl describe node <NODE_NAME>
```

#### 3. Network Connectivity Issues

```bash
# Check if kube-proxy is running
kubectl get pods -n kube-system | grep kube-proxy

# Check service endpoints
kubectl get endpoints <SERVICE_NAME>
```

#### 4. NodeAffinity Issues

```bash
# Verify node labels
kubectl get nodes --show-labels

# Check deployment configuration
kubectl get deployment <DEPLOYMENT_NAME> -o yaml
```

### Useful Commands

```bash
# Get all resources
kubectl get all

# Describe specific resource
kubectl describe <RESOURCE_TYPE> <RESOURCE_NAME>

# Check cluster events
kubectl get events --sort-by='.lastTimestamp'

# Check node status
kubectl get nodes -o wide

# Check service endpoints
kubectl get endpointslices
```

## Summary

This guide provides a complete workflow for:

1. **Setting up a Kubernetes cluster** with master and worker nodes
2. **Automatically generating a hostfile** with worker node IPs
3. **Deploying applications on all nodes** using nodeAffinity
4. **Testing connectivity** to ensure proper deployment
5. **Troubleshooting common issues**

The deployment ensures exactly one pod per worker node and strictly follows the nodeAffinity rules for placement.

**Perfect for IoWarp distributed deployments!** 🎯
