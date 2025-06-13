#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project2/python/main.py

import sys
import os
import argparse

def main(input_dir, output_dir):
    """
    Main processing function for Ritaglio doppia pagina
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
    """
    print(f"Processing started...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Add your processing logic here
    print("Processing logic goes here...")
    
    print("Processing complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ritaglia un doppio foglio A4 sulla piega e aggiorna l'ordine delle pagine generate dal ritaglio")
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)