#!/bin/bash

# Script to generate hostfile and deploy on all nodes
# Usage: ./deploy_from_hostfile.sh

echo "=========================================="
echo "Kubernetes Hostfile Generation & Deployment"
echo "=========================================="
echo ""

# Step 1: Generate hostfile
echo "Step 1: Generating hostfile from cluster nodes..."
echo ""

# Clear the file first
> hostfile

# Get node information directly and process it
kubectl get nodes -o wide | tail -n +2 | while read -r line; do
    ip=$(echo "$line" | awk '{print $6}')
    hostname=$(echo "$line" | awk '{print $1}')
    
    # Only add worker nodes (exclude master node by hostname pattern) that have valid IPs
    if [[ "$ip" != "<none>" && "$ip" != "EXTERNAL-IP" && -n "$ip" && ! "$hostname" =~ \.local$ ]]; then
        echo "$ip" >> hostfile
    fi
done

echo "Hostfile generated successfully!"
echo "Contents of hostfile:"
echo "===================="
cat hostfile
echo ""

# Step 2: Read all IPs from hostfile for deployment
echo "Step 2: Reading nodes for deployment..."
declare -a node_ips
declare -a node_hostnames
line_number=1

# Clear arrays first
node_ips=()
node_hostnames=()

while IFS= read -r line; do
    if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
        node_ips+=("$line")
        
        # Get hostname for the IP
        hostname=$(kubectl get nodes -o wide | grep "$line" | awk '{print $1}')
        node_hostnames+=("$hostname")
        
        echo "  $line_number) $line ($hostname)"
        ((line_number++))
    fi
done < hostfile

if [ ${#node_ips[@]} -eq 0 ]; then
    echo "Error: No valid IPs found in hostfile."
    exit 1
fi

echo ""
echo "Found ${#node_ips[@]} nodes in hostfile:"
for i in "${!node_ips[@]}"; do
    echo "  - ${node_ips[$i]} (${node_hostnames[$i]})"
done
echo ""

# Step 3: Set deployment details (no user input)
deployment_name="all-nodes-app"
docker_image="nginx:alpine"
container_port="80"
replicas_per_node="1"

total_replicas=$((${#node_ips[@]} * replicas_per_node))

echo "Step 3: Creating deployment on ALL nodes with following details:"
echo "======================================================"
echo "Deployment Name: $deployment_name"
echo "Docker Image: $docker_image"
echo "Container Port: $container_port"
echo "Replicas per node: $replicas_per_node"
echo "Total replicas: $total_replicas"
echo "Target nodes: ${node_ips[*]}"
echo ""

# Step 4: Create deployment with nodeAffinity for all nodes
echo "Step 4: Creating deployment.yaml..."
cat > deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $deployment_name
  labels:
    app: $deployment_name
spec:
  replicas: $total_replicas
  selector:
    matchLabels:
      app: $deployment_name
  template:
    metadata:
      labels:
        app: $deployment_name
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
EOF

# Add all hostnames to the nodeSelector
for hostname in "${node_hostnames[@]}"; do
    echo "                - $hostname" >> deployment.yaml
done

# Continue with the rest of the deployment
cat >> deployment.yaml << EOF
      containers:
      - name: $deployment_name
        image: $docker_image
        ports:
        - containerPort: $container_port
        command: ["nginx", "-g", "daemon off;"]
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: $deployment_name-service
  labels:
    app: $deployment_name
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: $container_port
    protocol: TCP
    name: http
  selector:
    app: $deployment_name
EOF

# Step 5: Apply the deployment
echo "Step 5: Applying deployment to ALL nodes..."
kubectl apply -f deployment.yaml --validate=false

echo ""
echo "Deployment applied successfully!"
echo ""

echo ""
echo "Deployment Complete!"
echo "=========================================="
echo "Summary:"
echo "- Hostfile generated with ${#node_ips[@]} worker nodes"
echo "- Deployment created with $total_replicas replicas"
echo "- Exactly 1 pod per worker node"
echo "- NodeAffinity ensures strict node placement"
echo ""
echo "To test connectivity:"
echo "1. SSH to worker nodes and test pod IPs"
echo "2. Use service IP for load-balanced access"
echo "3. Check README.md for detailed testing instructions"
echo ""
