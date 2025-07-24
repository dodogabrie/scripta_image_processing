#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project4/python/main.py

import sys
import os
import argparse
from rust_optimizer import run_optimizer

# Force unbuffered output by setting environment variable and flags
os.environ['PYTHONUNBUFFERED'] = '1'

def main(input_dir, output_dir, quality=85, workers=4, webp=False, verbose=False, webp_quality=80):
    """
    Main processing function for Leggio Massive Builder
    Uses the Rust Space Media Optimizer for high-performance media processing.
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
        quality (int): JPEG quality (1-100)
        workers (int): Number of parallel workers
        webp (bool): Convert to WebP format
        verbose (bool): Enable verbose logging
    """
    
    # Validate input directory
    if not os.path.exists(input_dir):
        print(f"❌ Error: Input directory does not exist: {input_dir}")
        sys.stdout.flush()
        return False
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the Rust optimizer - all output will come directly from Rust
    success = run_optimizer(
        input_dir=input_dir,
        output_dir=output_dir,
        quality=quality,
        workers=workers,
        webp=webp,
        webp_quality=webp_quality,  # Fix: passa correttamente webp_quality
        verbose=verbose,
        skip_video_compression=False  # Enable video compression by default
    )
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Riorganizza i file multimediali di una istanza di Leggio in modo tale da ottimizzarne il caricamento sul server")
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality (1-100)")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--webp", action="store_true", help="Convert to WebP format")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--webp-quality", type=int, default=80, help="WebP quality (1-100)")

    args = parser.parse_args()
    
    success = main(args.input_dir, args.output_dir, args.quality, args.workers, args.webp, args.verbose, args.webp_quality)
    sys.exit(0 if success else 1)