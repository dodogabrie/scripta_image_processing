"""
image_processing.py

Modulo per il processing delle immagini: crop, rotazione opzionale e split.
"""

import cv2
from .fold_detection import detect_fold_brightness_profile


def apply_crop_and_split(img, x_fold, angle, side, apply_rotation=False):
    """
    Divide l'immagine in lato sinistro e destro con rotazione opzionale.
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

    if side == 'center':
        # Per il centro, dividiamo dall'asse della piega
        left_side = processed_img[:, :x_fold]
        right_side = processed_img[:, x_fold:]
    elif side == 'right':
        # La piega è a destra, quindi la parte sinistra è quella valida
        left_side = processed_img[:, :x_fold]
        right_side = None  # Non c'è una parte destra valida
    elif side == 'left':
        # La piega è a sinistra, quindi la parte destra è quella valida
        left_side = None  # Non c'è una parte sinistra valida
        right_side = processed_img[:, x_fold:]
    else:
        raise ValueError(f"Lato non supportato per il crop: {side}")
    
    return left_side, right_side


def process_image(img, side, debug=False, debug_dir=None, apply_rotation=False):
    """
    Processa l'immagine: rileva la piega, applica split con rotazione opzionale.
    Ritorna: (immagine_sinistra, immagine_destra, info_debug)
    """
    x_fold, angle, a, b = detect_fold_brightness_profile(img, side, debug=debug, debug_dir=debug_dir)
    left_side, right_side = apply_crop_and_split(img, x_fold, angle, side, apply_rotation=apply_rotation)
    
    debug_info = {
        'x_fold': x_fold,
        'angle': angle,
        'slope': a,
        'intercept': b,
        'rotation_applied': apply_rotation
    }
    
    return left_side, right_side, debug_info
