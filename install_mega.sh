#!/bin/bash

# install_mega.sh
# Automates the installation of the mega package with a clean, engaging user experience.

set -e

DEB_URL="https://fileshare.computekart.com/mega_1.0.0_amd64.deb"
DEB_FILE="mega"
INSTALL_DIR="/opt/mega"
# Handle token input
# We allow INSTALL_TOKEN (user facing) to override/set PROVIDER_SERVER_TOKEN_INIT (internal)
if [ -n "$INSTALL_TOKEN" ]; then
    PROVIDER_SERVER_TOKEN_INIT="$INSTALL_TOKEN"
fi

# Enforce mandatory token
if [ -z "$PROVIDER_SERVER_TOKEN_INIT" ]; then
    echo -e "${RED}[!] Error: INSTALL_TOKEN is required.${d}"
    echo -e "Usage: curl ... | sudo INSTALL_TOKEN=your_token bash"
    exit 1
fi

TOKEN="$PROVIDER_SERVER_TOKEN_INIT"
# Added build-essential and python3-dev for compiling libvirt-python wheels
DEPENDENCIES=("libvirt-dev" "virtinst" "python3-libvirt" "qemu-kvm" "libvirt-daemon-system" "pipx" "build-essential" "python3-dev" "pkg-config")


# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
d='\033[0m' # Default

LOG_FILE="/tmp/mega_install.log"
# Clear previous log
echo "Mega Install Log - $(date)" > "$LOG_FILE"

# Spinner function to show activity
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

run_with_spinner() {
    local msg="$1"
    local cmd="$2"
    
    echo -ne "$msg"
    
    # Run command in background, appending output to log
    # We use a subshell to ensure set -e doesn't kill the main script if this fails immediately
    (eval "$cmd") >> "$LOG_FILE" 2>&1 &
    local pid=$!
    
    spinner $pid
    
    # Wait for the PID and capture its exit code
    # 'wait' returns the exit code of the process being waited for
    wait $pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Done${d}"
    else
        echo -e "${RED}Failed${d}"
        echo -e "${RED}Check log: $LOG_FILE${d}"
        echo -e "${YELLOW}Last 20 lines of error:${d}"
        tail -n 20 "$LOG_FILE"
        # We exit explicitly here because we want to stop on error
        exit $exit_code
    fi
}

echo -e "${BLUE}==========================================${d}"
echo -e "${BLUE}   🚀  Welcome to Mega Server Installer   ${d}"
echo -e "${BLUE}==========================================${d}"
echo ""

# 1. Cleanup /opt/mega but preserve .env and images/
if [ -d "$INSTALL_DIR" ]; then
    run_with_spinner "${YELLOW}[ 20% ] Cleaning up old files... ${d}" "sudo find \"$INSTALL_DIR\" -mindepth 1 -maxdepth 1 ! -name \".env\" ! -name \"images\" -exec rm -rf {} +"
else
    echo -e "${YELLOW}[ 20% ] Clean slate detected. Skipping cleanup.${d}"
fi

# 2. Download the package
# For curl, we want to see the progress bar if possible, but the user asked for % overall.
# Let's stick to the spinner for consistency to avoid "stuck" look, or use curl -# for bar.
# User asked for "terminal is stuck" fix. Accessing correct PID for curl -# is hard in bg.
# Let's use spinner which says "Downloading..."
run_with_spinner "${YELLOW}[ 40% ] Downloading Mega package... ${d}" "curl -L -o \"$DEB_FILE\" \"$DEB_URL\""

# 3. Purge existing installation
run_with_spinner "${YELLOW}[ 60% ] Removing old versions if exists... ${d}" "if dpkg -s mega >/dev/null 2>&1; then sudo apt remove --purge mega -y; fi; sudo rm -rf /etc/mega"

# 4. Install dependencies
echo -e "${YELLOW}[ 80% ] Checking dependencies...${d}"
# We run apt-update first
run_with_spinner "        Updating package lists... ${d}" "sudo apt-get update -qq"

for pkg in "${DEPENDENCIES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $pkg "; then
        run_with_spinner "        Installing $pkg... ${d}" "sudo apt-get install -y \"$pkg\""
    fi
done

# Download and install custom Java
JAVA_URL="https://fileshare.computekart.com/java-1.11.0-openjdk-amd64.tar.gz"
# Ensure install dir exists for extraction
sudo mkdir -p "$INSTALL_DIR"
run_with_spinner "${YELLOW}[ 90% ] Installing Custom Java... ${d}" "curl -L -o /tmp/java.tar.gz \"$JAVA_URL\" && sudo tar -xf /tmp/java.tar.gz -C \"$INSTALL_DIR\""

# 5. Install the new package with token
# Write token to file for postinst to read (env vars can be unreliable across dpkg)
sudo mkdir -p /etc/mega
echo "$TOKEN" | sudo tee /etc/mega/.install_token > /dev/null
sudo chmod 600 /etc/mega/.install_token

run_with_spinner "${YELLOW}[100% ] Installing new Mega package... ${d}" "sudo dpkg -i \"$DEB_FILE\""

echo ""
# Clean up log file on success
rm -f "$LOG_FILE"
echo -e "${GREEN}✨ Success! Your Mega Server is installed and ready to rock! 🎸${d}"
echo -e "${GREEN}   Check status with: systemctl status mega${d}"
echo ""