"""
batch_crop.py

Script for batch processing of book scans with folder structure preservation.

Usage:
    python batch_crop.py input_dir output_dir [options]
"""

import argparse
import os
import glob
from pathlib import Path
import subprocess
import sys


def find_images(input_dir, extensions=None):
    """
    Find all image files in the input directory recursively.
    
    Args:
        input_dir (str): Input directory path
        extensions (list): List of file extensions to search for
    
    Returns:
        list: List of image file paths
    """
    if extensions is None:
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.bmp']
    
    image_files = []
    for ext in extensions:
        pattern = os.path.join(input_dir, '**', ext)
        image_files.extend(glob.glob(pattern, recursive=True))
        # Also search for uppercase extensions
        pattern_upper = os.path.join(input_dir, '**', ext.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=True))
    
    return sorted(list(set(image_files)))  # Remove duplicates and sort


def process_batch(input_dir, output_dir, **kwargs):
    """
    Process all images in input_dir and save to output_dir preserving structure.
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
        **kwargs: Additional arguments to pass to crop.py
    """
    # Ensure directories exist
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)
    
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all image files
    image_files = find_images(input_dir)
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} image files to process")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Get the directory containing crop.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    crop_script = os.path.join(script_dir, 'crop.py')
    
    if not os.path.exists(crop_script):
        raise ValueError(f"crop.py not found at: {crop_script}")
    
    # Process each image
    successful = 0
    failed = 0
    
    for i, image_path in enumerate(image_files, 1):
        try:
            print(f"\nProcessing {i}/{len(image_files)}: {os.path.relpath(image_path, input_dir)}")
            
            # Build command for crop.py
            cmd = [
                sys.executable, crop_script,
                image_path,
                '--input_base_dir', input_dir,
                output_dir
            ]
            
            # Add optional arguments
            if kwargs.get('side'):
                cmd.extend(['--side', kwargs['side']])
            if kwargs.get('debug'):
                cmd.append('--debug')
            if kwargs.get('output_format'):
                cmd.extend(['--output_format', kwargs['output_format']])
            if kwargs.get('rotate'):
                cmd.append('--rotate')
            if kwargs.get('smart_crop'):
                cmd.append('--smart_crop')
            
            # Execute crop.py
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                successful += 1
                if kwargs.get('verbose', True):
                    print(f"✓ Success")
            else:
                failed += 1
                print(f"✗ Failed: {result.stderr.strip()}")
                
        except Exception as e:
            failed += 1
            print(f"✗ Error processing {image_path}: {e}")
    
    print(f"\nBatch processing completed:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(image_files)}")


def main():
    """Main function for batch processing."""
    parser = argparse.ArgumentParser(
        description="Batch process book scans with folder structure preservation"
    )
    
    parser.add_argument("input_dir", help="Input directory containing images")
    parser.add_argument("output_dir", help="Output directory for processed images")
    parser.add_argument("--side", choices=['left', 'right', 'center'], 
                       help="Force fold side detection (auto-detect if not specified)")
    parser.add_argument("--debug", action='store_true',
                       help="Generate debug visualizations")
    parser.add_argument("--output_format", choices=['jpg', 'png', 'tiff'],
                       help="Output format (resize to HD if specified)")
    parser.add_argument("--rotate", action='store_true',
                       help="Apply rotation to straighten folds")
    parser.add_argument("--smart_crop", action='store_true',
                       help="Use intelligent document edge detection")
    parser.add_argument("--verbose", action='store_true', default=True,
                       help="Print detailed progress information")
    
    args = parser.parse_args()
    
    try:
        process_batch(
            args.input_dir,
            args.output_dir,
            side=args.side,
            debug=args.debug,
            output_format=args.output_format,
            rotate=args.rotate,
            smart_crop=args.smart_crop,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
