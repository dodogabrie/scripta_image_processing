#!/usr/bin/env python3
"""
Wrapper script to call the Rust Space Media Optimizer binary from Python/Electron.
This allows seamless integration with the existing project infrastructure.
"""

import os
import sys
import subprocess
import platform
import json
import signal
import atexit
from pathlib import Path

# Global variable to track the current process
current_process = None

def cleanup_process():
    """Cleanup function to ensure process is terminated on exit."""
    global current_process
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
            current_process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            try:
                current_process.kill()
            except OSError:
                pass

def signal_handler(signum, frame):
    """Handle termination signals."""
    global current_process
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
        except OSError:
            pass
    sys.exit(0)

# Register cleanup functions
atexit.register(cleanup_process)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def stop_current_process():
    """Stop the currently running process."""
    global current_process
    if current_process and current_process.poll() is None:
        try:
            print(json.dumps({"type": "info", "message": "Stopping current process..."}), flush=True)
            current_process.terminate()
            
            # Wait a bit for graceful termination
            try:
                current_process.wait(timeout=5)
                print(json.dumps({"type": "info", "message": "Process stopped successfully"}), flush=True)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated gracefully
                current_process.kill()
                current_process.wait()
                print(json.dumps({"type": "info", "message": "Process forcefully killed"}), flush=True)
                
            return True
        except OSError as e:
            print(json.dumps({"type": "error", "message": f"Error stopping process: {e}"}), flush=True)
            return False
    else:
        print(json.dumps({"type": "info", "message": "No process currently running"}), flush=True)
        return True

def format_bytes(bytes_val):
    """Format bytes into human readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val/1024:.1f} KB"
    elif bytes_val < 1024**3:
        return f"{bytes_val/(1024**2):.1f} MB"
    else:
        return f"{bytes_val/(1024**3):.1f} GB"

def get_rust_binary_path():
    """Get the path to the Rust binary based on the current platform."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    rust_project_dir = script_dir.parent / "rust" / "space_media_optimizer"
    
    # Determine binary name based on platform
    if platform.system() == "Windows":
        binary_name = "media-optimizer.exe"
    else:
        binary_name = "media-optimizer"
    
    binary_path = rust_project_dir / "target" / "release" / binary_name
    
    if not binary_path.exists():
        raise FileNotFoundError(f"Rust binary not found at: {binary_path}")
    
    return str(binary_path)

def run_optimizer(input_dir, output_dir, **kwargs):
    """
    Run the Space Media Optimizer with the specified parameters.
    
    Args:
        input_dir (str): Input directory containing media files
        output_dir (str): Output directory for optimized files
        **kwargs: Additional parameters for the optimizer
    """
    global current_process
    
    try:
        binary_path = get_rust_binary_path()
        
        # Build command arguments
        cmd = [binary_path, input_dir]
        
        # Add output directory if specified
        if output_dir:
            cmd.extend(["--output", output_dir])
        
        # Add optional parameters
        if "quality" in kwargs and kwargs["quality"] is not None:
            cmd.extend(["--quality", str(kwargs["quality"])])
        
        if kwargs.get("crf"):
            cmd.extend(["--crf", str(kwargs["crf"])])
        
        if kwargs.get("workers"):
            cmd.extend(["--workers", str(kwargs["workers"])])
        
        if kwargs.get("dry_run"):
            cmd.append("--dry-run")
        
        if kwargs.get("webp"):
            cmd.append("--webp")
        
        if kwargs.get("webp_quality"):
            cmd.extend(["--webp-quality", str(kwargs["webp_quality"])])
        
        if kwargs.get("skip_video_compression"):
            cmd.append("--skip-video-compression")
        
        if kwargs.get("verbose"):
            cmd.append("--verbose")
        
        # Always use JSON output for structured communication
        cmd.append("--json-output")
        
        # Create the process and store it globally for termination control
        current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,  # No buffering - immediate output
            universal_newlines=True,
            cwd=os.path.dirname(binary_path)
        )
        
        # Read output line by line in real-time
        if current_process.stdout:
            for line in iter(current_process.stdout.readline, ''):
                if line:
                    line = line.strip()
                    # Try to parse as JSON first
                    try:
                        data = json.loads(line)
                        # Pass JSON data directly to frontend with immediate flush
                        try:
                            print(json.dumps(data), flush=True)
                        except BrokenPipeError:
                            # Frontend disconnected, stop processing
                            stop_current_process()
                            break
                    except json.JSONDecodeError:
                        # If not JSON, wrap in a message object
                        message = {"type": "raw", "data": line}
                        try:
                            print(json.dumps(message), flush=True)
                        except BrokenPipeError:
                            # Frontend disconnected, stop processing
                            stop_current_process()
                            break
                
                # Check if process was terminated externally
                if current_process.poll() is not None:
                    break
        
        # Wait for process to complete
        current_process.wait()
        result_code = current_process.returncode
        
        # Clear the global process reference
        current_process = None
        
        return result_code == 0
        
    except Exception as e:
        try:
            error_msg = {"type": "error", "message": f"Error running optimizer: {e}"}
            print(json.dumps(error_msg), flush=True)
        except BrokenPipeError:
            # Frontend disconnected, just exit silently
            pass
        
        # Clear the global process reference
        current_process = None
        return False

def main():
    """Main entry point when script is run directly."""
    # Check if this is a stop command
    if len(sys.argv) == 2 and sys.argv[1] == "stop":
        return stop_current_process()
    
    if len(sys.argv) < 3:
        print("Usage: python rust_optimizer.py <input_dir> <output_dir> [options]")
        print("       python rust_optimizer.py stop")
        print("")
        print("Options:")
        print("  --quality <1-100>       JPEG quality")
        print("  --webp-quality <1-100>  WebP quality (works with --webp or standalone)")
        print("  --crf <0-51>           Video CRF value")
        print("  --workers <num>        Number of parallel workers")
        print("  --dry-run              Don't actually replace files")
        print("  --webp                 Convert to WebP format")
        print("  --skip-video           Skip video compression")
        print("  --verbose              Verbose logging")
        print("")
        print("Commands:")
        print("  stop                   Stop any currently running process")
        return False
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Parse additional arguments
    kwargs = {}
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--quality" and i + 1 < len(sys.argv):
            kwargs["quality"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--crf" and i + 1 < len(sys.argv):
            kwargs["crf"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--workers" and i + 1 < len(sys.argv):
            kwargs["workers"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--webp-quality" and i + 1 < len(sys.argv):
            kwargs["webp_quality"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--dry-run":
            kwargs["dry_run"] = True
            i += 1
        elif arg == "--webp":
            kwargs["webp"] = True
            i += 1
        elif arg == "--skip-video":
            kwargs["skip_video_compression"] = True
            i += 1
        elif arg == "--verbose":
            kwargs["verbose"] = True
            i += 1
        else:
            i += 1
    
    return run_optimizer(input_dir, output_dir, **kwargs)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
