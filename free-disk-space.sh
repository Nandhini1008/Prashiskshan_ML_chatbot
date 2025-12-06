#!/bin/bash
# Script to free up disk space on EC2

echo "=========================================="
echo "Freeing Disk Space on EC2"
echo "=========================================="

echo "Current disk usage:"
df -h

echo ""
echo "Cleaning up Docker..."

# Remove unused Docker images
echo "Removing unused Docker images..."
docker image prune -a -f

# Remove unused containers
echo "Removing stopped containers..."
docker container prune -f

# Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# Remove build cache
echo "Removing Docker build cache..."
docker builder prune -a -f

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f

echo ""
echo "Cleaning up system packages..."
sudo apt-get autoremove -y
sudo apt-get autoclean -y

echo ""
echo "Cleaning up logs..."
sudo journalctl --vacuum-time=3d

echo ""
echo "Final disk usage:"
df -h

echo ""
echo "Done! Try building again."

