#!/bin/bash

echo "🚀 Starting FDI Package Manager..."

# Wait for packages directory to be mounted
echo "⏳ Waiting for FDI packages directory to be available..."
while [ ! -d "/app/fdi-packages" ]; do
    echo "   Packages directory not found, waiting..."
    sleep 2
done

# Wait for manifest to exist
echo "⏳ Waiting for manifest.json to be available..."
while [ ! -f "/app/fdi-packages/manifest.json" ]; do
    echo "   Manifest not found, waiting..."
    sleep 2
done

# Verify packages are readable
echo "✅ Verifying packages are accessible..."
if [ -r "/app/fdi-packages/manifest.json" ]; then
    echo "   Packages are accessible"
else
    echo "   Warning: Packages directory exists but is not readable"
fi

# Start the application
echo "🚀 Starting Flask application..."
exec python main.py
