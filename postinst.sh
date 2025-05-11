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
if [ ! -f "$CONFIG_FILE" ] || [ -z "$PROVIDER_SERVER_TOKEN_INIT" ] || [ -z "$NGROK_AUTH_TOKEN" ] || [ -z "$NGROK_URL" ] || [ -z "$PRV_VIRT_SYSTEM" ]; then
    echo "[*] Please enter the required configuration values:"

    # Prompt for all variables if not set
    if [ -z "$PROVIDER_SERVER_TOKEN_INIT" ]; then
        read -p "🔐 PROVIDER_SERVER_TOKEN_INIT: " PROVIDER_SERVER_TOKEN_INIT
    fi

    if [ -z "$NGROK_AUTH_TOKEN" ]; then
        read -p "🔑 NGROK_AUTH_TOKEN (optional): " NGROK_AUTH_TOKEN
    fi

    if [ -z "$NGROK_URL" ]; then
        read -p "🌐 NGROK_URL (optional): " NGROK_URL
    fi

    if [ -z "$PRV_VIRT_SYSTEM" ]; then
        read -p "🖥️ Libvirt system URI [default: qemu:///system]: " PRV_VIRT_SYSTEM
        PRV_VIRT_SYSTEM=${PRV_VIRT_SYSTEM:-qemu:///system}
    fi

    # Write all variables back to config file
    cat <<EOF > "$CONFIG_FILE"
PROVIDER_SERVER_TOKEN_INIT=$PROVIDER_SERVER_TOKEN_INIT
NGROK_AUTH_TOKEN=$NGROK_AUTH_TOKEN
NGROK_URL=$NGROK_URL
PRV_VIRT_SYSTEM=$PRV_VIRT_SYSTEM
MNGMT_URL="https://backend.computekart.com"
EOF

    echo "[+] Configuration written to $CONFIG_FILE"
fi

# Install ngrok (if token is provided)
if [ -n "$NGROK_AUTH_TOKEN" ]; then
    echo "[+] Installing and configuring ngrok..."
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
        | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
        | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update
else
    echo "[!] Skipping ngrok installation: No auth token provided."
fi

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
