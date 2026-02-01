#!/bin/bash

set -e  # Exit on error

echo "============================"
echo "🚀 Mega Server Post-Install"
echo "============================"

# Ensure the script is running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "[!] This script must be run as root (use sudo)."
    exit 1
fi

cd /opt/mega

CONFIG_FILE="/etc/mega/config.conf"
mkdir -p /etc/mega
touch "$CONFIG_FILE"

# Load existing config if available
if [ -f "$CONFIG_FILE" ]; then
    echo "[+] Found existing config. Loading..."
    . "$CONFIG_FILE"
else
    echo "[+] No existing config found. Proceeding to collect configuration..."
fi

# Check for install token file (passed from install_mega.sh)
# This takes precedence over existing config to allow re-keying
TOKEN_FILE="/etc/mega/.install_token"
if [ -f "$TOKEN_FILE" ]; then
    echo "[+] Found install token file. Using new token."
    PROVIDER_SERVER_TOKEN_INIT=$(cat "$TOKEN_FILE")
    rm -f "$TOKEN_FILE"
fi

# If the config file does not exist or is missing variables, ask for all values
# Use provided env var or empty (logic handled by caller)
# PROVIDER_SERVER_TOKEN_INIT passed from install_mega.sh satisfies this.

# helper for PRV_VIRT_SYSTEM
if [ -z "$PRV_VIRT_SYSTEM" ]; then
     PRV_VIRT_SYSTEM="qemu:///system"
fi

IMAGES_DIR="/opt/mega/images"

# Ensure the directory exists
mkdir -p "$IMAGES_DIR"

# Write all variables back to config file
# We quote the values to ensure safe sourcing later
cat <<EOF > "$CONFIG_FILE"
PROVIDER_SERVER_TOKEN_INIT="${PROVIDER_SERVER_TOKEN_INIT}"
PRV_VIRT_SYSTEM="${PRV_VIRT_SYSTEM}"
MNGMT_URL="https://backend.computekart.com"
IMAGES_DIR="${IMAGES_DIR}"
BASE_QVM_PATH="base.qcow2"
JAVA_HOME="/opt/mega/java-1.11.0-openjdk-amd64"
EOF

echo "[+] Configuration written to $CONFIG_FILE"

# Set up virtual environment
python3 -m venv /opt/mega/venv
. /opt/mega/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Reload systemd and enable service
echo "[+] Enabling and starting the mega service..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable mega
systemctl restart mega

if systemctl list-unit-files | grep -q mega-scrapper.service; then
    echo "[+] Enabling and starting the mega-scrapper service..."
    systemctl enable mega-scrapper
    systemctl restart mega-scrapper
else
    echo "[!] mega-scrapper service not found, skipping."
fi

echo "✅ Mega server setup complete and running!"