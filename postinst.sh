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

# Install required Python dependencies using pip and requirements.txt
cd /opt/mega

# Check if .env already exists in /etc/mega/.env
ENV_FILE="/etc/mega/.env"
if [ -f "$ENV_FILE" ]; then
    echo "[+] .env already exists. Skipping environment variable prompts."
else
    # Prompt for environment variables if .env doesn't exist
    echo "[*] Please enter the required configuration values:"
    read -p "🔐 PROVIDER_SERVER_TOKEN_INIT: " TOKEN
    read -p "🐦 NGROK_URL (optional): " NGROK_URL
    read -p "🖥️  Libvirt system URI [default: qemu:///system]: " PRV_VIRT_SYSTEM

    # Set default if empty
    PRV_VIRT_SYSTEM=${PRV_VIRT_SYSTEM:-qemu:///system}

    # Write to /etc/mega/.env
    mkdir -p /etc/mega
    cat <<EOF > "$ENV_FILE"
PROVIDER_SERVER_TOKEN_INIT=$TOKEN
MNGMT_URL="https://backend.computekart.com"
NGROK_URL=$NGROK_URL
PRV_VIRT_SYSTEM=$PRV_VIRT_SYSTEM
EOF

    echo "[+] .env written to /etc/mega."
fi

python3 -m venv /opt/mega/venv
. /opt/mega/venv/bin/activate
pip install -r requirements.txt

# Reload systemd, enable and start the mega service
echo "[+] Enabling and starting the mega service..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable mega
systemctl restart mega

echo "✅ Mega server setup complete and running!"
