"""
image_io.py

Modulo per il caricamento e salvataggio delle immagini con supporto per diversi formati.
"""

import cv2
import os


def load_image(input_path):
    """Carica un'immagine senza perdita di qualità."""
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Image not found: {input_path}")
    return img


def save_image_preserve_format(img, out_path):
    """Salva un'immagine preservando il formato originale senza perdita di qualità."""
    if out_path is None:
        raise ValueError("Output path cannot be None")
    
    # Get file extension to determine format
    _, ext = os.path.splitext(out_path)
    ext = ext.lower()
    
    if ext in ['.jpg', '.jpeg']:
        cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 100])  # Maximum quality
    elif ext in ['.tiff', '.tif']:
        # Try different TIFF compression options for better compatibility
        try:
            # Try LZW compression (value 5)
            success = cv2.imwrite(out_path, img, [cv2.IMWRITE_TIFF_COMPRESSION, 5])
            if not success:
                raise Exception("LZW compression failed")
        except:
            try:
                # Fallback: try no compression (value 1)
                print(f"Warning: LZW compression failed, trying no compression for {out_path}")
                success = cv2.imwrite(out_path, img, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
                if not success:
                    raise Exception("No compression failed")
            except:
                # Final fallback: save without compression parameters
                print(f"Warning: All TIFF compression options failed, using default settings for {out_path}")
                cv2.imwrite(out_path, img)
    elif ext in ['.png']:
        cv2.imwrite(out_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # No compression
    elif ext == '':
        # No extension provided, assume same format as input
        raise ValueError(f"Output path has no file extension: {out_path}")
    else:
        # Default save without specific parameters
        cv2.imwrite(out_path, img)
        
    # Verify file was created and has reasonable size
    if os.path.exists(out_path):
        file_size = os.path.getsize(out_path)
        if file_size < 1000:  # Less than 1KB is suspicious
            print(f"Warning: Output file {out_path} is very small ({file_size} bytes)")
        else:
            print(f"Successfully saved {out_path} ({file_size} bytes)")
    else:
        print(f"Error: Failed to create output file {out_path}")


def generate_output_paths(input_path, output_path=None):
    """
    Genera i percorsi di output per le immagini sinistra e destra.
    Ritorna: (path_left, path_right, base_path_for_debug)
    """
    input_base, input_ext = os.path.splitext(input_path)
    input_filename = os.path.basename(input_base)
    
    if output_path is None:
        # No output specified, use input directory
        output_base = input_base
        output_ext = input_ext
    elif os.path.isdir(output_path):
        # Output is a directory, use input filename in that directory
        output_base = os.path.join(output_path, input_filename)
        output_ext = input_ext
    else:
        # Output is a file path
        output_base, output_ext = os.path.splitext(output_path)
        if not output_ext:
            # No extension in output, use input extension
            output_ext = input_ext
    
    path_left = output_base + "_left" + output_ext
    path_right = output_base + "_right" + output_ext
    
    return path_left, path_right, output_base
