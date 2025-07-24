@echo off
setlocal enabledelayedexpansion
REM Simple Rust build script for Windows

echo 🦀 Building Rust projects...
echo =============================

REM Check if Rust is installed
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Rust/Cargo not found. Please install Rust first:
    echo    https://rustup.rs/
    exit /b 1
)

REM Build specific project for now (space_media_optimizer)
set RUST_PROJECT=src\projects\project4\rust\space_media_optimizer

if not exist "%RUST_PROJECT%" (
    echo ❌ Error: Rust project directory not found: %RUST_PROJECT%
    exit /b 1
)

echo 🔨 Building Rust project: %RUST_PROJECT%
echo --------------------------------
pushd "%RUST_PROJECT%"

cargo build --release

if !errorlevel! equ 0 (
    echo ✅ Build successful!
    echo 📍 Binary location: !CD!\target\release\
    
    REM Test the binary if it exists
    if exist "target\release\media-optimizer.exe" (
        echo 🧪 Testing binary...
        target\release\media-optimizer.exe --help >nul 2>nul || echo ⚠️ Binary test failed, but build completed
    ) else (
        echo ⚠️ Binary not found, but build reported success
    )
    
    echo 🎉 Rust build completed successfully!
    popd
    exit /b 0
) else (
    echo ❌ Build failed!
    popd
    exit /b 1
)
