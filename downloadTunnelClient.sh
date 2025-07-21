# Ensure /opt/mega exists
if [ ! -d "/opt/mega" ]; then
    echo "[+] Creating /opt/mega directory..."
    sudo mkdir -p /opt/mega
fi

# Download with resume support
JAR_PATH="/opt/mega/ComputeKart-tunnel-client-1.0.0.jar"
JAR_URL="https://fileshare.computekart.com/ComputeKart-tunnel-client-1.0.0.jar"

echo "[+] Downloading ComputeKart tunnel client with resume support..."
sudo curl -L -C - -o "$JAR_PATH" "$JAR_URL"