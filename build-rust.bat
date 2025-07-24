@echo off
REM Build script for all Rust binaries in projects (Windows)

echo 🦀 Building Rust projects...
echo =============================

REM Check if Rust is installed
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Rust/Cargo not found. Please install Rust first:
    echo    https://rustup.rs/
    exit /b 1
)

REM Find all Rust projects in src/projects/*/rust/*/
echo � Searching for Rust projects...

set BUILD_FAILED=0
set PROJECTS_BUILT=0

for /d %%i in (src\projects\*) do (
    if exist "%%i\rust" (
        for /d %%j in (%%i\rust\*) do (
            if exist "%%j\Cargo.toml" (
                echo.
                echo 🔨 Building Rust project: %%j
                echo --------------------------------
                pushd "%%j"
                
                cargo build --release
                
                if !errorlevel! equ 0 (
                    echo ✅ Build successful for %%j
                    echo 📍 Binary location: !CD!\target\release\
                    
                    REM Test the binary if it exists
                    for %%f in (target\release\*.exe) do (
                        echo 🧪 Testing binary: %%f
                        "%%f" --help >nul 2>nul || echo ⚠️  Binary test failed for %%f, but build completed
                    )
                    set /a PROJECTS_BUILT+=1
                ) else (
                    echo ❌ Build failed for %%j
                    set BUILD_FAILED=1
                )
                
                popd
            )
        )
    )
)

echo.
echo =============================
if %PROJECTS_BUILT% equ 0 (
    echo ⚠️  No Rust projects found to build
    exit /b 0
) else (
    echo ✅ Built %PROJECTS_BUILT% Rust project(s)
)

if %BUILD_FAILED% equ 1 (
    echo ❌ Some builds failed!
    exit /b 1
) else (
    echo 🎉 All Rust builds completed successfully!
    exit /b 0
)
