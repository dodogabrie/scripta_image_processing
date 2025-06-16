"""
image_processing.py

Modulo per il processing delle immagini: crop, rotazione opzionale e split.
"""

import cv2
from .fold_detection import detect_fold_brightness_profile


def apply_crop_and_split(img, x_fold, angle, side, apply_rotation=False, smart_crop=False, debug=False, debug_dir=None):
    """
    Divide l'immagine in lato sinistro e destro con rotazione opzionale.
    Se smart_crop è True, usa il rilevamento del bordo del documento per un crop più intelligente.
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
    
    if smart_crop:
        # Usa il rilevamento intelligente del bordo documento
        from .fold_detection import detect_document_edge
        
        if side == 'center':
            left_margin, right_margin = detect_document_edge(img, side, x_fold, debug=debug, debug_dir=debug_dir)
            left_crop_end = x_fold + left_margin 
            right_crop_start = max(0, x_fold - right_margin)
            
            left_side = processed_img[:, :left_crop_end]
            right_side = processed_img[:, right_crop_start:]
            
        elif side == 'right':
            left_margin = detect_document_edge(img, side, x_fold, debug=debug, debug_dir=debug_dir)
            
            crop_end = x_fold + left_margin
            left_side = processed_img[:, :crop_end]
            right_side = None
            
        elif side == 'left':
            right_margin = detect_document_edge(img, side, x_fold, debug=debug, debug_dir=debug_dir)
            
            crop_start = max(0, x_fold - right_margin)
            left_side = None
            right_side = processed_img[:, crop_start:]
        else:
            raise ValueError(f"Lato non supportato per il crop: {side}")
    else:
        # Crop standard sulla piega
        if side == 'center':
            left_side = processed_img[:, :x_fold]
            right_side = processed_img[:, x_fold:]
        elif side == 'right':
            left_side = processed_img[:, :x_fold]
            right_side = None
        elif side == 'left':
            left_side = None
            right_side = processed_img[:, x_fold:]
        else:
            raise ValueError(f"Lato non supportato per il crop: {side}")
    
    return left_side, right_side


def process_image(img, side, debug=False, debug_dir=None, apply_rotation=False, smart_crop=False):
    """
    Processa l'immagine: rileva la piega, applica split con rotazione opzionale e crop intelligente opzionale.
    Ritorna: (immagine_sinistra, immagine_destra, info_debug)
    """
    x_fold, angle, a, b = detect_fold_brightness_profile(img, side, debug=debug, debug_dir=debug_dir)
    left_side, right_side = apply_crop_and_split(img, x_fold, angle, side, 
                                                apply_rotation=apply_rotation, 
                                                smart_crop=smart_crop, 
                                                debug=debug, 
                                                debug_dir=debug_dir)
    
    debug_info = {
        'x_fold': x_fold,
        'angle': angle,
        'slope': a,
        'intercept': b,
        'rotation_applied': apply_rotation,
        'smart_crop_applied': smart_crop
    }
    
    return left_side, right_side, debug_info
