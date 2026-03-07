#!/bin/bash

TOKEN=""

for i in {1..20}; do
    TOKEN=$(grep TUNNEL_SERVER_TOKEN /opt/mega/.env 2>/dev/null | cut -d "=" -f2 | tr -d '"')

    if [ ! -z "$TOKEN" ]; then
        echo "Token found. Starting tunnel..."

        /opt/mega/java-1.11.0-openjdk-amd64/bin/java \
        -cp /opt/mega/ComputeKart-tunnel-client-1.0.0.jar \
        main.Main "$TOKEN" localhost 6996 >> /opt/mega/tunnel.log 2>&1 &

        exit 0
    fi

    echo "Waiting for token..."
    sleep 3
done

echo "Error: Token not found after multiple attempts." >> /opt/mega/tunnel.log
exit 1