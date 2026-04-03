#!/bin/bash
#mcp@name:          systemlogs
#mcp@description:   Display recent system logs using journalctl (requires sudo)
#mcp@return:        string

# System Logs Script for Ubuntu
# Returns recent journal entries (last 50 lines)

echo "=== Recent System Logs (last 50 entries) ==="
echo ""

# Try to get recent logs - attempt without sudo first, then with sudo if needed
if journalctl -n 50 --no-pager 2>/dev/null; then
    : # Success without sudo
elif [ -n "$TEST_SUDO_PASSWORD" ]; then
    # Headless test mode: use sudo -S with password from env var
    echo "$TEST_SUDO_PASSWORD" | sudo -S --preserve-env=TEST_SUDO_PASSWORD journalctl -n 50 --no-pager 2>&1
else
    # Production mode: use sudo with askpass
    sudo -A journalctl -n 50 --no-pager 2>&1
fi

if [ $? -ne 0 ]; then
    echo "Warning: Could not retrieve journalctl logs"
fi

echo ""
echo "=== End of System Logs ==="
exit 0
