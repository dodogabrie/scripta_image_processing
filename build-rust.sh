#!/bin/bash
# Build script for Space Media Optimizer Rust binary

set -e

echo "🦀 Building Space Media Optimizer..."
echo "=================================="

RUST_DIR="src/projects/project4/rust/space_media_optimizer"

if [ ! -d "$RUST_DIR" ]; then
    echo "❌ Error: Rust project directory not found: $RUST_DIR"
    exit 1
fi

cd "$RUST_DIR"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: Rust/Cargo not found. Please install Rust first:"
    echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "🔨 Building release binary..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📍 Binary location: $PWD/target/release/media-optimizer"
    
    # Make binary executable
    chmod +x target/release/media-optimizer*
    
    echo "🧪 Testing binary..."
    ./target/release/media-optimizer --help || echo "⚠️  Binary test failed, but build completed"
else
    echo "❌ Build failed!"
    exit 1
fi
