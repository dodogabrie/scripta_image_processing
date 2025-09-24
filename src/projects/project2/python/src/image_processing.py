"""
image_processing.py

Modulo per il processing delle immagini: crop, rotazione opzionale e split.
"""

import cv2
from .fold_detection import detect_fold_brightness_profile


def apply_crop_and_split(img, x_fold, angle, side, apply_rotation=False, smart_crop=False, debug=False, debug_dir=None, fold_border=50):
    """
    Divide l'immagine in lato sinistro e destro con rotazione opzionale.
    Se smart_crop è True, usa il rilevamento del bordo del documento per un crop più intelligente.

    Args:
        fold_border (int): Pixel di margine da aggiungere attorno alla piega (default: 50)

    Ritorna: (immagine_sinistra, immagine_destra)
    """
    if apply_rotation:
        # Applica rotazione se richiesta
        h = img.shape[0]
        M = cv2.getRotationMatrix2D(center=(x_fold, h//2), angle=-angle, scale=1.0)
        processed_img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else:
        # Mantieni l'immagine originale senza rotazione
        processed_img = img

    h, w = processed_img.shape[:2]
    

    # Crop con margine attorno alla piega
    if side == 'center':
        # Left side: from 0 to x_fold + fold_border
        left_end = min(w, x_fold + fold_border)
        left_side = processed_img[:, :left_end]

        # Right side: from x_fold - fold_border to end
        right_start = max(0, x_fold - fold_border)
        right_side = processed_img[:, right_start:]

        if debug:
            print(f"Fold border: {fold_border}px")
            print(f"Left crop: 0 to {left_end} (fold at {x_fold})")
            print(f"Right crop: {right_start} to {w} (fold at {x_fold})")

    elif side == 'right':
        left_end = min(w, x_fold + fold_border)
        left_side = processed_img[:, :left_end]
        right_side = None

        if debug:
            print(f"Right-side fold border: {fold_border}px")
            print(f"Left crop: 0 to {left_end} (fold at {x_fold})")

    elif side == 'left':
        left_side = None
        right_start = max(0, x_fold - fold_border)
        right_side = processed_img[:, right_start:]

        if debug:
            print(f"Left-side fold border: {fold_border}px")
            print(f"Right crop: {right_start} to {w} (fold at {x_fold})")
    else:
        raise ValueError(f"Lato non supportato per il crop: {side}")
    
    return left_side, right_side


def process_image(img, side, debug=False, debug_dir=None, apply_rotation=False, smart_crop=False, fold_border=50, image_path=None):
    """
    Processa l'immagine: rileva la piega, applica split con rotazione opzionale e crop intelligente opzionale.
    Ritorna: (immagine_sinistra, immagine_destra, info_debug)
    """
    from .page_processor import detect_document_format

    # Check if this is A3 landscape - only do fold detection on A3 landscape
    if image_path:
        is_a3 = detect_document_format(image_path, debug=debug)
        if not is_a3:
            if debug:
                print("Non-A3 format detected - skipping fold detection, returning original image")
            debug_info = {
                'x_fold': None,
                'angle': 0.0,
                'slope': 0.0,
                'intercept': 0.0,
                'confidence': 0.0,
                'rotation_applied': False,
                'smart_crop_applied': False
            }
            # Return original image without fold-based cropping
            return img, None, debug_info

    x_fold, angle, a, b, confidence = detect_fold_brightness_profile(img, side, debug=debug, debug_dir=debug_dir)

    left_side, right_side = apply_crop_and_split(img, x_fold, angle, side,
                                                apply_rotation=apply_rotation,
                                                smart_crop=smart_crop,
                                                debug=debug,
                                                debug_dir=debug_dir,
                                                fold_border=fold_border)

    debug_info = {
        'x_fold': x_fold,
        'angle': angle,
        'slope': a,
        'intercept': b,
        'confidence': confidence,
        'rotation_applied': apply_rotation,
        'smart_crop_applied': smart_crop
    }

    return left_side, right_side, debug_info
