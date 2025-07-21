#!/bin/bash

URL="https://fileshare.computekart.com/base.qcow2"
DEST_DIR="/opt/mega/images"
DEST_FILE="$DEST_DIR/base.qcow2"

# Ensure the destination directory exists
if [ ! -d "$DEST_DIR" ]; then
    echo "Creating directory $DEST_DIR..."
    sudo mkdir -p "$DEST_DIR"
fi

# Resume download if partial file exists
echo "Downloading with resume support..."
sudo curl -L -C - -o "$DEST_FILE" "$URL"

if [ $? -eq 0 ]; then
    echo "Download completed successfully."
else
    echo "Download failed!" >&2
    exit 1
fi