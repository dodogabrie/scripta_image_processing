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
    args = p.parse_args()

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
        path_left, path_right, base_path = generate_output_paths(args.input, modified_out)
        # Ensure the extensions match the output format
        base_left, _ = os.path.splitext(path_left)
        base_right, _ = os.path.splitext(path_right)
        path_left = base_left + f".{args.output_format}"
        path_right = base_right + f".{args.output_format}"
    else:
        path_left, path_right, base_path = generate_output_paths(args.input, args.out)

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