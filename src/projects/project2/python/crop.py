"""
crop.py

Script per il rilevamento automatico della piega di un libro in una scansione,
crop e rotazione dell'immagine, e salvataggio in formato JPG.

Funzionalità principali:
- Rilevamento automatico del lato della piega (sinistra/destra/centro)
- Stima dell'angolo della piega tramite fit parabolico e regressione lineare
- Crop e rotazione per portare la piega al bordo dell'immagine
- Salvataggio dell'immagine croppata e ridimensionata
- Opzionale: generazione di immagini di debug per analisi visiva

Utilizzo:
    python crop.py input.jpg [--side left|right|center] output.jpg [--debug]
"""

import argparse
import os

from src.image_io import load_image, save_image_preserve_format, generate_output_paths
from src.fold_detection import auto_detect_side
from src.image_processing import process_image
from src.utils import resize_width_hd
from src.debug_tools import save_debug_line_visualization
from PIL import Image
from PIL.ExifTags import TAGS


def test_lab(image_path):
    """
    Test function to examine TIF image metadata and properties.
    """
    print(f"\n=== TIF METADATA TEST for {image_path} ===")

    try:
        # Open image with PIL to check metadata
        with Image.open(image_path) as pil_img:
            print(f"Format: {pil_img.format}")
            print(f"Mode: {pil_img.mode}")
            print(f"Size: {pil_img.size}")

            # Check for EXIF data
            if hasattr(pil_img, '_getexif') and pil_img._getexif() is not None:
                exif = pil_img._getexif()
                print(f"EXIF data found: {len(exif)} entries")
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    print(f"  {tag}: {value}")
            else:
                print("No EXIF data found")

            # Check for other metadata
            info = pil_img.info
            if info:
                print(f"PIL Info metadata: {len(info)} entries")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("No PIL Info metadata found")

            # Check compression and quality
            if 'compression' in info:
                print(f"Compression: {info['compression']}")
            if 'quality' in info:
                print(f"Quality: {info['quality']}")

            # Check DPI information and calculate physical size
            dpi_x = dpi_y = None

            # Try to get DPI from various sources
            if hasattr(pil_img, 'info') and 'dpi' in pil_img.info:
                dpi_info = pil_img.info['dpi']
                if isinstance(dpi_info, tuple) and len(dpi_info) >= 2:
                    dpi_x, dpi_y = dpi_info[0], dpi_info[1]
                else:
                    dpi_x = dpi_y = dpi_info
                print(f"DPI: {dpi_info}")
            elif hasattr(pil_img, 'tag') and 'dpi' in pil_img.tag:
                dpi_info = pil_img.tag['dpi']
                dpi_x = dpi_y = dpi_info
                print(f"DPI (from tag): {dpi_info}")
            else:
                print("No DPI information found")

            # Calculate physical dimensions in cm if DPI is available
            if dpi_x and dpi_y:
                try:
                    width_px, height_px = pil_img.size

                    # Convert DPI to float to handle Fraction objects
                    dpi_x_float = float(dpi_x)
                    dpi_y_float = float(dpi_y)

                    # Convert pixels to inches, then to cm
                    width_inches = width_px / dpi_x_float
                    height_inches = height_px / dpi_y_float
                    width_cm = width_inches * 2.54
                    height_cm = height_inches * 2.54

                    print(f"\n📏 PHYSICAL DIMENSIONS:")
                    print(f"  Size in pixels: {width_px} x {height_px}")
                    print(f"  DPI: {dpi_x_float:.1f} x {dpi_y_float:.1f}")
                    print(f"  Size in inches: {width_inches:.2f}\" x {height_inches:.2f}\"")
                    print(f"  Size in cm: {width_cm:.2f} cm x {height_cm:.2f} cm")

                    # Calculate area
                    area_cm2 = width_cm * height_cm
                    print(f"  Area: {area_cm2:.2f} cm²")

                    # Standard paper sizes for reference
                    print(f"\n📄 REFERENCE SIZES:")
                    print(f"  A4: 21.0 x 29.7 cm")
                    print(f"  A3: 29.7 x 42.0 cm")
                    print(f"  A2: 42.0 x 59.4 cm")
                    print(f"  A1: 59.4 x 84.1 cm")
                    print(f"  A0: 84.1 x 118.9 cm")

                    # Check if image matches specific paper formats
                    print(f"\n🔍 FORMAT DETECTION:")

                    # Define tolerances (±15% for "more or less" matching)
                    tolerance = 0.15

                    # A4 dimensions
                    a4_w, a4_h = 21.0, 29.7
                    # A3 dimensions
                    a3_w, a3_h = 29.7, 42.0

                    def matches_size(actual_w, actual_h, target_w, target_h, tolerance):
                        """Check if actual dimensions match target within tolerance"""
                        w_diff = abs(actual_w - target_w) / target_w
                        h_diff = abs(actual_h - target_h) / target_h
                        return w_diff <= tolerance and h_diff <= tolerance

                    # Check orientation
                    is_portrait = height_cm > width_cm
                    is_landscape = width_cm > height_cm

                    print(f"  Orientation: {'Portrait (H>W)' if is_portrait else 'Landscape (W>H)' if is_landscape else 'Square'}")

                    # Check A4 vertical (portrait)
                    if is_portrait and matches_size(width_cm, height_cm, a4_w, a4_h, tolerance):
                        print(f"  ✅ MATCHES: A4 Vertical (Portrait)")
                        print(f"     Expected: {a4_w} x {a4_h} cm")
                        print(f"     Actual:   {width_cm:.1f} x {height_cm:.1f} cm")

                    # Check A3 horizontal (landscape)
                    elif is_landscape and matches_size(width_cm, height_cm, a3_h, a3_w, tolerance):
                        print(f"  ✅ MATCHES: A3 Horizontal (Landscape)")
                        print(f"     Expected: {a3_h} x {a3_w} cm")
                        print(f"     Actual:   {width_cm:.1f} x {height_cm:.1f} cm")

                    # Check other possibilities
                    else:
                        print(f"  ❌ No exact match found")

                        # Check if close to A4 vertical
                        if is_portrait:
                            w_diff_a4 = abs(width_cm - a4_w) / a4_w * 100
                            h_diff_a4 = abs(height_cm - a4_h) / a4_h * 100
                            print(f"     A4 Vertical difference: W {w_diff_a4:.1f}%, H {h_diff_a4:.1f}%")

                        # Check if close to A3 horizontal
                        if is_landscape:
                            w_diff_a3 = abs(width_cm - a3_h) / a3_h * 100
                            h_diff_a3 = abs(height_cm - a3_w) / a3_w * 100
                            print(f"     A3 Horizontal difference: W {w_diff_a3:.1f}%, H {h_diff_a3:.1f}%")

                except Exception as calc_error:
                    print(f"Error calculating physical dimensions: {calc_error}")
            else:
                print("Cannot calculate physical dimensions without DPI information")

    except Exception as e:
        print(f"Error reading metadata: {e}")

    print("=== END TIF METADATA TEST ===\n")


def main():
    """
    Parsing degli argomenti, caricamento immagine, rilevamento piega, crop, rotazione e salvataggio.
    """
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--side", choices=('left','right','center'), default=None)
    p.add_argument("out", nargs='?')
    p.add_argument("--debug", action='store_true')
    p.add_argument("--output_format", choices=('jpg', 'png', 'tiff'), default=None,
                   help="Output format. If specified, images will be resized to HD and converted to this format.")
    p.add_argument("--rotate", action='store_true', default=False,
                   help="Apply rotation to straighten the fold. Default is False.")
    p.add_argument("--smart_crop", action='store_true', default=False,
                   help="Use document edge detection for intelligent cropping. Default is False.")
    p.add_argument("--input_base_dir", default=None,
                   help="Base directory for preserving folder structure in batch processing.")
    p.add_argument("--test-lab", action='store_true', default=False,
                   help="Run metadata test only, skip normal processing.")
    args = p.parse_args()

    # If test lab mode, run only metadata test
    if args.test_lab:
        test_lab(args.input)
        return

    # Load image without quality loss
    img = load_image(args.input)

    # Generate output paths - modify extension if output format is specified
    if args.output_format:
        # Override extension based on output format
        input_base, _ = os.path.splitext(args.input)
        if args.out and not os.path.isdir(args.out):
            # If specific output file provided, change its extension
            output_base, _ = os.path.splitext(args.out)
            modified_out = output_base + f".{args.output_format}"
        else:
            modified_out = args.out
        path_left, path_right, base_path = generate_output_paths(args.input, modified_out, args.input_base_dir)
        # Ensure the extensions match the output format
        base_left, _ = os.path.splitext(path_left)
        base_right, _ = os.path.splitext(path_right)
        path_left = base_left + f".{args.output_format}"
        path_right = base_right + f".{args.output_format}"
    else:
        path_left, path_right, base_path = generate_output_paths(args.input, args.out, args.input_base_dir)

    debug_dir = None
    if args.debug:
        debug_dir = base_path + "_debug"

    side = auto_detect_side(img) if args.side is None else args.side

    if side not in ('left', 'right', 'center'):
        print("Attenzione: Lato della piega non rilevato, salvo originale")
        if args.output_format:
            # Resize and convert format
            width = min(1920, img.shape[1])
            hd_img = resize_width_hd(img, target_width=width)
            save_image_preserve_format(hd_img, path_left)
        else:
            # Save at maximum quality without resizing
            save_image_preserve_format(img, path_left)
        return

    left_side, right_side, debug_info = process_image(img, side, debug=args.debug, debug_dir=debug_dir, 
                                                     apply_rotation=args.rotate, smart_crop=args.smart_crop)
    
    rotation_status = "con rotazione" if debug_info['rotation_applied'] else "senza rotazione"
    crop_status = "smart crop" if debug_info['smart_crop_applied'] else "crop standard"
    print(f"x: {debug_info['x_fold']}, inclinazione stimata: {debug_info['angle']:.2f}°, processato {rotation_status}, {crop_status}")

    if debug_dir:
        save_debug_line_visualization(img, debug_info['x_fold'], debug_info['angle'], 
                                    debug_info['slope'], debug_info['intercept'], 
                                    os.path.join(debug_dir, "fold_line_visualization.jpg"))

    # Process and save results based on output format preference
    if left_side is not None:
        if args.output_format:
            # Resize and convert format
            width = min(1920, left_side.shape[1])
            left_processed = resize_width_hd(left_side, target_width=width)
        else:
            # Save at maximum quality without resizing
            left_processed = left_side
        
        save_image_preserve_format(left_processed, path_left)
        print(f"Salvato lato sinistro: {path_left}")
    
    if right_side is not None:
        if args.output_format:
            # Resize and convert format
            width = min(1920, right_side.shape[1])
            right_processed = resize_width_hd(right_side, target_width=width)
        else:
            # Save at maximum quality without resizing
            right_processed = right_side
        
        save_image_preserve_format(right_processed, path_right)
        print(f"Salvato lato destro: {path_right}")


if __name__=="__main__":
    main()