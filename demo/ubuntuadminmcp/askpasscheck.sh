#!/bin/bash
#mcp@name:          askpasscheck
#mcp@description:   Force sudo askpass authentication and confirm root elevation
#mcp@return:        string

# Askpass Authentication Check for Ubuntu
# Forces the sudo askpass path even when some read-only tools work without sudo.

echo "=== Askpass Authentication Check ==="
echo ""
echo "This tool forces sudo authentication with askpass."
echo ""

if [ -n "$TEST_SUDO_PASSWORD" ]; then
    if root_uid=$(
        echo "$TEST_SUDO_PASSWORD" | \
            sudo -S -k --preserve-env=TEST_SUDO_PASSWORD id -u 2>/dev/null
    ); then
        :
    else
        echo "Authentication failed."
        exit 1
    fi
else
    if root_uid=$(sudo -A -k id -u 2>/dev/null); then
        :
    else
        echo "Authentication failed."
        exit 1
    fi
fi

if [ "$root_uid" != "0" ]; then
    echo "Unexpected sudo result: $root_uid"
    exit 1
fi

echo "Authentication succeeded. Root UID: $root_uid"
echo ""
echo "=== End of Askpass Authentication Check ==="
exit 0
