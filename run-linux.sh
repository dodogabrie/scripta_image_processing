#!/bin/bash

# Simple launcher script for Scripta Image Processing
# This script handles the AppImage filename with spaces correctly

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE="$APP_DIR/dist/Scripta Image Processing-1.0.3.AppImage"

if [ -f "$APPIMAGE" ]; then
    echo "Launching Scripta Image Processing..."
    exec "$APPIMAGE" "$@"
else
    echo "Error: AppImage not found at $APPIMAGE"
    echo "Please run ./build-linux.sh first to build the application."
    exit 1
fi
