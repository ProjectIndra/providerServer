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

# If the config file does not exist or is missing variables, ask for all values
if [ ! -f "$CONFIG_FILE" ] || [ -z "$PROVIDER_SERVER_TOKEN_INIT" ] || [ -z "$PRV_VIRT_SYSTEM" ]; then
    echo "[*] Please enter the required configuration values:"

    # Prompt for all variables if not set
    if [ -z "$PROVIDER_SERVER_TOKEN_INIT" ]; then
        read -p "🔐 PROVIDER_SERVER_TOKEN_INIT: " PROVIDER_SERVER_TOKEN_INIT
    fi

    if [ -z "$PRV_VIRT_SYSTEM" ]; then
        read -p "🖥️ Libvirt system URI [default: qemu:///system]: " PRV_VIRT_SYSTEM
        PRV_VIRT_SYSTEM=${PRV_VIRT_SYSTEM:-qemu:///system}
    fi

    # Write all variables back to config file
    cat <<EOF > "$CONFIG_FILE"
PROVIDER_SERVER_TOKEN_INIT=$PROVIDER_SERVER_TOKEN_INIT
PRV_VIRT_SYSTEM=$PRV_VIRT_SYSTEM
MNGMT_URL="http://100.81.95.72:30001"
IMAGES_DIR="/home/avinash/cloud_project/images"
BASE_QVM_PATH="base.qcow2"
EOF

    echo "[+] Configuration written to $CONFIG_FILE"
fi

# install the tunnel client
sudo chmod +x /opt/mega/downloadTunnelClient.sh
/opt/mega/downloadTunnelClient.sh

# call downloadImage.sh to download the base image of the VM i.e. base.qcow2
# sudo chmod +x /opt/mega/downloadImage.sh
# /opt/mega/downloadImage.sh

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

echo "✅ Mega server setup complete and running!"
