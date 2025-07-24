#!/bin/bash
# Build script for all Rust binaries in projects

set -e

echo "🦀 Building Rust projects..."
echo "============================="

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: Rust/Cargo not found. Please install Rust first:"
    echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Find all Rust projects in src/projects/*/rust/*/
echo "� Searching for Rust projects..."

BUILD_FAILED=0
PROJECTS_BUILT=0

for project_dir in src/projects/*/rust/*/; do
    if [ -d "$project_dir" ] && [ -f "$project_dir/Cargo.toml" ]; then
        echo ""
        echo "�🔨 Building Rust project: $project_dir"
        echo "--------------------------------"
        
        pushd "$project_dir" > /dev/null
        
        if cargo build --release; then
            echo "✅ Build successful for $project_dir"
            echo "📍 Binary location: $PWD/target/release/"
            
            # Make binaries executable
            chmod +x target/release/* 2>/dev/null || true
            
            # Test the binary if it exists
            for binary in target/release/*; do
                if [ -x "$binary" ] && [ ! -d "$binary" ]; then
                    echo "🧪 Testing binary: $(basename "$binary")"
                    "$binary" --help &>/dev/null || echo "⚠️  Binary test failed for $(basename "$binary"), but build completed"
                fi
            done
            
            ((PROJECTS_BUILT++))
        else
            echo "❌ Build failed for $project_dir"
            BUILD_FAILED=1
        fi
        
        popd > /dev/null
    fi
done

echo ""
echo "============================="
if [ $PROJECTS_BUILT -eq 0 ]; then
    echo "⚠️  No Rust projects found to build"
    exit 0
else
    echo "✅ Built $PROJECTS_BUILT Rust project(s)"
fi

if [ $BUILD_FAILED -eq 1 ]; then
    echo "❌ Some builds failed!"
    exit 1
else
    echo "🎉 All Rust builds completed successfully!"
fi
