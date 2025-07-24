#!/bin/bash

# Build script for Scripta Image Processing on Linux
# This script automates the complete build process including dependencies and packaging

set -e  # Exit on any error

echo "🚀 Building Scripta Image Processing for Linux..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Make sure you're in the project root directory."
    exit 1
fi

# Step 1: Fix ownership of tools directory (if needed)
print_status "Checking tools directory ownership..."
if [ -d "src/tools" ] && [ "$(stat -c %U src/tools)" = "root" ]; then
    print_warning "Tools directory is owned by root, fixing ownership..."
    sudo chown -R $(whoami):$(whoami) src/tools/
    print_success "Tools directory ownership fixed"
fi

# Step 2: Download and setup optimization tools
print_status "Setting up optimization tools..."
node scripts/download-optimization-tools.js
if [ $? -eq 0 ]; then
    print_success "Optimization tools setup completed"
else
    print_error "Failed to setup optimization tools"
    exit 1
fi

# Step 3: Run the full build process
print_status "Running npm build (includes Vue build, tools setup, Rust build, and Electron packaging)..."
npm run build
if [ $? -eq 0 ]; then
    print_success "Build completed successfully!"
else
    print_error "Build failed"
    exit 1
fi

# Step 4: Check if AppImage was created
if [ -f "dist/Scripta Image Processing-"*.AppImage ]; then
    APPIMAGE_PATH=$(ls "dist/Scripta Image Processing-"*.AppImage | head -n 1)
    print_success "AppImage created: $APPIMAGE_PATH"
    
    # Make it executable
    chmod +x "$APPIMAGE_PATH"
    print_success "AppImage made executable"
    
    # Get file size
    SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)
    print_status "AppImage size: $SIZE"
    
    # Test if AppImage can be executed
    print_status "Testing AppImage..."
    if timeout 5s "$APPIMAGE_PATH" --help >/dev/null 2>&1 || [ $? -eq 124 ]; then
        print_success "AppImage is executable"
    else
        print_warning "AppImage created but GUI app (no CLI help available)"
    fi
    
else
    print_error "No AppImage found in dist/ directory"
    ls -la dist/
    exit 1
fi

# Step 5: Optionally install desktop entry
read -p "Do you want to install the desktop entry for system integration? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Installing desktop entry..."
    
    # Create desktop file if it doesn't exist
    if [ ! -f "scripta-image-processing.desktop" ]; then
        print_status "Creating desktop entry file..."
        cat > scripta-image-processing.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Scripta Image Processing
Comment=Advanced image processing and optimization tool
Exec=$PWD/$APPIMAGE_PATH
Icon=applications-graphics
Terminal=false
Categories=Graphics;Photography;
Keywords=image;photo;processing;optimization;
StartupNotify=true
EOF
    fi
    
    # Install desktop entry
    mkdir -p ~/.local/share/applications/
    cp scripta-image-processing.desktop ~/.local/share/applications/
    chmod +x ~/.local/share/applications/scripta-image-processing.desktop
    
    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database ~/.local/share/applications/
    fi
    
    print_success "Desktop entry installed. You can now find 'Scripta Image Processing' in your applications menu."
fi

echo
print_success "Build process completed successfully!"
echo "=================================================="
print_status "AppImage location: $APPIMAGE_PATH"
print_status "To run the application:"
echo "  ./'$APPIMAGE_PATH'"
echo "  # or with full path:"
echo "  '$PWD/$APPIMAGE_PATH'"
echo
print_status "To install system-wide (optional):"
echo "  sudo cp '$APPIMAGE_PATH' /opt/scripta-image-processing.AppImage"
echo "  sudo ln -s /opt/scripta-image-processing.AppImage /usr/local/bin/scripta-image-processing"
echo
