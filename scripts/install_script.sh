#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

USERNAME="avinash"
TOKEN="asasdasdsadasd"
REPO_URL="https://github.com/avinash84319/providerServer.git"  # Corrected repository URL

# Create the directory and navigate to it
mkdir -p ~/.indra
cd ~/.indra

# Clone the repository (if it doesn't already exist)
if [ ! -d "providerServer" ]; then
    git clone "$REPO_URL"
else
    echo "Repository already exists. Pulling latest changes..."
    cd providerServer
    
    # Stash any local changes
    git stash

    # Pull the latest changes
    git pull
fi

cd ~/.indra/providerServer
pwd  # Print the current directory for debugging

# Install Poetry using the official installation script
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -

    # Add Poetry to PATH
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"  # Apply to current session
fi

# Reload shell configuration (for non-interactive sessions)
export PATH="$HOME/.local/bin:$PATH"
export MNGMT_URL="https://globally-above-fowl.ngrok-free.app"
export PRV_VIRT_SYSTEM="qemu:///system"

# Verify installation
poetry --version

# Install dependencies
poetry install --no-root

# Set environment variables (customize as needed)
MNGMT_URL="https://globally-above-fowl.ngrok-free.app"
PRV_VIRT_SYSTEM="qemu:///system"

# Run the server
poetry run python server.py --port=6996
