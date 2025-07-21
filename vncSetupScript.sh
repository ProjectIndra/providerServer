#!/bin/bash
set -e

# Assume this variable is passed/set before running the script
# Example usage: vm_password="yourpassword" ./this_script.sh

if [ -z "$vm_password" ]; then
  echo "❌ Error: vm_password variable not set. Please export it before running the script."
  exit 1
fi

echo "[*] Configuring VNC and starting noVNC..."

# Step 1: Set VNC password non-interactively
echo "[*] Setting VNC password..."
mkdir -p ~/.vnc
echo "$vm_password" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

# Step 2: Create xstartup for XFCE
cat <<EOF > ~/.vnc/xstartup
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF
chmod +x ~/.vnc/xstartup

# Step 3: Start/restart VNC server on :1
vncserver -kill :1 2>/dev/null || true
vncserver :1

# Step 4: Clone noVNC if not present
NOVNC_DIR="/opt/noVNC"
if [ ! -d "$NOVNC_DIR" ]; then
    echo "[*] Cloning noVNC into $NOVNC_DIR..."
    sudo git clone https://github.com/novnc/noVNC.git "$NOVNC_DIR"
    cd "$NOVNC_DIR"
    sudo git submodule update --init --recursive
else
    echo "[*] noVNC already exists at $NOVNC_DIR"
fi

# Step 5: Free up port 9090 if in use
echo "[*] Ensuring port 9090 is free..."
sudo fuser -k 9090/tcp || true

# Step 6: Start noVNC proxy on all interfaces
echo "[*] Starting noVNC server on http://<your-ip>:9090/vnc.html"
cd "$NOVNC_DIR"
./utils/novnc_proxy --vnc localhost:5901 --listen 0.0.0.0:9090
