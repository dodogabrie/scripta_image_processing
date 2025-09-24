import cv2
import numpy as np

from .utils import show_image


def rgb_to_gray_from_tuple(bgr):
    """
    Converte una tripla (B, G, R) in valore scala di grigi usando la formula BT.601.

    Args:
        bgr (tuple[float, float, float]): Valori medi BGR.

    Returns:
        float: Valore di grigio corrispondente.
    """
    b, g, r = bgr
    return 0.114 * b + 0.587 * g + 0.299 * r


def estimate_threshold_and_border_rgb(image, gray_blurred):
    """
    Calcola una soglia binaria dinamica e il valore medio RGB dei bordi dell'immagine.

    Args:
        image (np.ndarray): Immagine BGR originale (uint8).
        gray_blurred (np.ndarray): Immagine sfocata in scala di grigi (uint8).

    Returns:
        int: Valore di soglia stimato per la binarizzazione (0–255).
        tuple[float, float, float]: Valore medio (B, G, R) dei bordi in float32.
    """
    h, w = gray_blurred.shape
    min_dim = min(h, w)
    center = int(min_dim * 0.3) // 2  # 10% per il centro

    # Calcola media RGB dei 4 angoli (patch 3x3)
    patches = []

    # Top-left
    patches.append(image[0:3, 0:3])

    # Top-right
    patches.append(image[0:3, -3:])

    # Bottom-left
    patches.append(image[-3:, 0:3])

    # Bottom-right
    patches.append(image[-3:, -3:])

    # Concatena e calcola la media RGB
    border_pixels = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0).astype(
        np.float32
    )
    border_rgb = tuple(border_pixels.mean(axis=0))  # B, G, R

    # Converti media RGB in grigio
    border_gray = rgb_to_gray_from_tuple(border_rgb)

    # Calcola media nel centro dell'immagine grigia
    cx, cy = w // 2, h // 2
    center_patch = gray_blurred[cy - center : cy + center, cx - center : cx + center]
    center_mean = center_patch.mean(dtype=np.float32)

    # Interpolazione pesata
    alpha = 0.6
    threshold_val = int(
        np.clip(border_gray + (center_mean - border_gray) * alpha, 0, 255)
    )

    border_val = tuple(int(round(c)) for c in border_rgb)
    return threshold_val, border_val


def smooth_edges(thresh, show_step_by_step=False):
    """
    Esegue erosione seguita da dilatazione (opening) per eliminare piccole irregolarità.

    Args:
        thresh (np.ndarray): Immagine binaria (uint8).
        show_step_by_step (bool): Se True, mostra i passaggi.

    Returns:
        np.ndarray: Immagine con bordi più lisci.
    """
    kernel = np.ones((20, 20), np.uint8)
    eroded = cv2.erode(thresh, kernel, iterations=5)
    dilated = cv2.dilate(eroded, kernel, iterations=5)

    if show_step_by_step:
        show_image(eroded, "Eroded")
        show_image(dilated, "Dilated after Erosion")

    return dilated


def refine_mask_morphology(thresh, show_step_by_step=False):
    """
    Applica chiusura e apertura morfologica per rendere i bordi più regolari.

    Args:
        thresh (np.ndarray): Immagine binaria (uint8).
        show_step_by_step (bool): Se True, mostra i passaggi.

    Returns:
        np.ndarray: Maschera binaria raffinata.
    """
    kernel_close = np.ones((15, 15), np.uint8)
    kernel_open = np.ones((5, 5), np.uint8)

    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)

    if show_step_by_step:
        show_image(closed, "After Morphological Close")
        show_image(opened, "After Morphological Open")

    return opened


def fill_internal_holes(thresh, show_step_by_step=False):
    """
    Riempie i buchi interni nell'immagine binaria per migliorare la detection del contorno esterno.

    Args:
        thresh (np.ndarray): Immagine binaria (uint8).
        show_step_by_step (bool): Se True, mostra i passaggi.

    Returns:
        np.ndarray: Immagine con buchi interni riempiti.
    """
    # Metodo 1: Flood fill dai bordi per identificare il background
    filled = thresh.copy()
    h, w = thresh.shape

    # Crea una maschera leggermente più grande per flood fill
    mask = np.zeros((h + 2, w + 2), np.uint8)

    # Flood fill da tutti i 4 angoli (riempie tutto il background connesso ai bordi)
    cv2.floodFill(filled, mask, (0, 0), 255)
    cv2.floodFill(filled, mask, (w - 1, 0), 255)
    cv2.floodFill(filled, mask, (0, h - 1), 255)
    cv2.floodFill(filled, mask, (w - 1, h - 1), 255)

    # Inverti per ottenere solo le aree che non sono background
    filled_inverted = cv2.bitwise_not(filled)

    # Combina con l'originale: mantieni tutto ciò che era già bianco + aree interne isolate
    flood_result = cv2.bitwise_or(thresh, filled_inverted)

    # Metodo 2: Morphological closing aggressivo per riempire buchi
    kernel_large = np.ones((50, 50), np.uint8)
    morph_result = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_large)

    # Metodo 3: Combinazione dei due approcci
    # Usa il closing morphologico come base, poi applica il flood fill
    combined = cv2.morphologyEx(
        flood_result, cv2.MORPH_CLOSE, np.ones((50, 50), np.uint8)
    )

    if show_step_by_step:
        show_image(filled, "After flood fill from borders")
        show_image(flood_result, "After hole filling with flood fill")
        show_image(morph_result, "After morphological closing")
        show_image(combined, "Combined approach")

    return combined


def preprocess_image(image, show_step_by_step=False):
    """
    Converte l'immagine in scala di grigi, la sfoca, calcola soglia dinamica
    basata sui valori medi dei bordi e binarizza. Restituisce anche il valore RGB medio dei bordi.

    Args:
        image (np.ndarray): Immagine BGR originale (uint8).
        show_step_by_step (bool): Se True, mostra i passaggi.

    Returns:
        np.ndarray: Immagine binarizzata (uint8, 0 o 255).
        tuple[float, float, float]: Media (B, G, R) dei bordi in float32.
    """
    # Converte in scala di grigi
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if show_step_by_step:
        show_image(gray, "Grayscale")

    # Applica blur adattivo in base alla dimensione minima
    min_dim = min(gray.shape[:2])
    k = max(3, int((min_dim / 50) // 2 * 2 + 1))  # Kernel dispari, minimo 3
    k = min(k, 51)  # Massimo 51
    print(f"Kernel size: {k}x{k}")
    blurred = cv2.GaussianBlur(gray, (k, k), 0)
    if show_step_by_step:
        show_image(blurred, f"Blurred (kernel={k}x{k})")

    # Calcola soglia e valore RGB del bordo
    threshold_val, border_rgb = estimate_threshold_and_border_rgb(image, blurred)

    _, thresh = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY)

    thresh = refine_mask_morphology(thresh, False)

    thresh = smooth_edges(thresh, False)

    # Riempi i buchi interni per migliorare la detection del contorno esterno
    thresh = fill_internal_holes(thresh, show_step_by_step)

    if show_step_by_step:
        show_image(thresh, f"Final processed (th={threshold_val})")

    return thresh, border_rgb
