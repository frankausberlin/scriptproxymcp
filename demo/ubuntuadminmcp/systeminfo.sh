#!/bin/bash
#mcp@name:          systeminfo
#mcp@description:   Gather comprehensive system information including hostname, OS, kernel, CPU, memory, disk, uptime, and network
#mcp@return:        string

# System Information Gathering Script for Ubuntu
# Returns a formatted summary of key system metrics

echo "=== System Information ==="
echo ""

# Hostname
echo "Hostname: $(hostname)"
echo ""

# Operating System
echo "=== Operating System ==="
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
    echo "ID: $ID"
    echo "Version ID: $VERSION_ID"
else
    echo "OS: $(uname -s)"
fi
echo ""

# Kernel
echo "=== Kernel ==="
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo ""

# CPU
echo "=== CPU ==="
echo "Model: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
echo "Cores: $(nproc)"
echo "Architecture: $(uname -m)"
echo ""

# Memory
echo "=== Memory ==="
free -h | grep -E "^Mem:|^Swap:" | while read line; do
    echo "$line"
done
echo ""

# Disk Usage
echo "=== Disk Usage ==="
df -h / | tail -1 | awk '{print "Total: "$2", Used: "$3", Available: "$4", Usage: "$5}'
echo ""

# Uptime
echo "=== Uptime ==="
uptime -p
echo ""

# Network
echo "=== Network ==="
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}/\d+' | while read ip; do
    echo "IP: $ip"
done
echo ""

# Load Average
echo "=== Load Average ==="
cat /proc/loadavg | awk '{print "1 min: "$1", 5 min: "$2", 15 min: "$3}'
echo ""

echo "=== End of System Information ==="
exit 0
