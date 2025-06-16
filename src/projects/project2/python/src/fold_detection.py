"""
fold_detection.py

Modulo per il rilevamento automatico delle pieghe nei libri scansionati.
"""

import cv2
import numpy as np
from scipy.optimize import curve_fit
from .utils import parabola


def auto_detect_side(img):
    """
    Rileva automaticamente il lato della piega (sinistra, destra o centro)
    in base alla luminosità dei bordi dell'immagine.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    margin = 10
    strip_width = 20  # Increased strip width for better detection

    left_strip = gray[:, margin:margin + strip_width]
    right_strip = gray[:, w - margin - strip_width:w - margin]
    center_strip = gray[:, w//2 - strip_width//2:w//2 + strip_width//2 + 1]

    left_brightness = np.mean(left_strip)
    right_brightness = np.mean(right_strip)
    center_brightness = np.mean(center_strip)

    print(f"Brightness - Left: {left_brightness:.1f}, Right: {right_brightness:.1f}, Center: {center_brightness:.1f}")

    # Check if center is significantly darker (fold in center)
    if center_brightness < min(left_brightness, right_brightness) - 10:
        return 'center'
    
    # Lower threshold for better detection
    if np.abs(left_brightness - right_brightness) < 5:
        return 'center'  # Default to center if unclear
    return 'right' if left_brightness < right_brightness else 'left'


def estimate_fold_angle_from_profile(gray, x_center, step=3):
    """
    Stima l'angolo della piega tramite fit parabolico e regressione lineare.
    Ritorna: (angolo in gradi, coeff. angolare, intercetta, larghezza stimata)
    """
    h = gray.shape[0]
    col_strip = gray[:, max(0, x_center - 2):min(gray.shape[1], x_center + 3)]
    mean_profile = col_strip.mean(axis=1)
    smoothed = cv2.GaussianBlur(mean_profile, (1, 11), 0)
    y = np.arange(len(smoothed))

    try:
        popt = np.polyfit(y, smoothed, 2)
        a, b, c = popt
        h_depth = (smoothed.max() - smoothed.min()) / 2
        width_est = int(2 * np.sqrt(h_depth / abs(a.item())))
        width = np.clip(width_est, 7, 50)
    except:
        width = 20
        print("Fit parabolico fallito, uso width=20")

    x_start = max(0, x_center - width // 2)
    x_end = min(gray.shape[1], x_center + width // 2 + 1)
    roi_strip = gray[:, x_start:x_end]

    xs, ys = [], []
    for y in range(0, h, step):
        col = roi_strip[y, :]
        x_local = np.argmin(col)
        xs.append(x_start + x_local)
        ys.append(y)

    a, b = np.polyfit(ys, xs, 1)
    angle = np.degrees(np.arctan(a))
    return angle, a, b, width


def get_roi_bounds(side, width, height):
    """
    Calcola i bounds della ROI in base al lato specificato.
    Ritorna: (x0, x1) coordinate della regione di interesse
    """
    if side == 'right':
        return int(0.8 * width), width
    elif side == 'left':
        return 0, int(0.2 * width)
    elif side == 'center':
        return int(0.3 * width), int(0.7 * width)
    else:
        raise ValueError(f"Lato non supportato: {side}")


def extract_brightness_profiles(roi, num_samples=40):
    """
    Estrae i profili di luminosità dalla ROI e li filtra per rimuovere outliers.
    Ritorna: (profili_filtrati, profilo_medio, profilo_std)
    """
    h = roi.shape[0]
    rows = np.linspace(0, h-1, num=num_samples, dtype=int)
    tmp = [(r, roi[r, :], roi[r, :].mean()) for r in rows]
    avg_ints = np.array([t[2] for t in tmp])
    mean_int = avg_ints.mean()
    std_int = avg_ints.std()
    filtered = [prof for (_, prof, avg) in tmp if abs(avg - mean_int) <= 1.5 * std_int]
    if not filtered:
        filtered = [prof for (_, prof, _) in tmp]
    
    arr = np.array(filtered)
    mean_profile = arr.mean(axis=0)
    std_profile = arr.std(axis=0)
    return filtered, mean_profile, std_profile


def find_fold_position(mean_profile, std_profile, x0):
    """
    Trova la posizione della piega nel profilo di luminosità usando fit parabolico.
    Ritorna: posizione_x_finale
    """
    smooth = cv2.GaussianBlur(mean_profile + std_profile, (11, 1), 0).flatten()
    x_min = np.argmin(smooth)
    x_fit = np.arange(max(0, x_min-15), min(len(smooth), x_min+16))
    y_fit = smooth[x_fit]
    popt, _ = curve_fit(parabola, x_fit, y_fit)
    x_refined = -popt[1] / (2 * popt[0])
    x_final = int(round(x0 + x_refined))
    return x_final


def detect_fold_brightness_profile(img, side, debug=False, debug_dir=None):
    """
    Rileva la posizione della piega tramite analisi dei profili di luminosità e fit parabolico.
    Opzionalmente salva immagini di debug.
    Ritorna: (x_final, angolo, coeff. angolare, intercetta)
    """
    from .debug_tools import save_debug_visualization
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    h, w = blur.shape
    x0, x1 = get_roi_bounds(side, w, h)
    roi = blur[:, x0:x1]

    x_axis = np.arange(x0, x1)
    filtered_profiles, mean_profile, std_profile = extract_brightness_profiles(roi)
    x_final = find_fold_position(mean_profile, std_profile, x0)
    
    angle, a, b, width = estimate_fold_angle_from_profile(gray, x_final, step=3)

    if debug and debug_dir:
        x_min = np.argmin(cv2.GaussianBlur(mean_profile + std_profile, (11, 1), 0).flatten())
        save_debug_visualization(filtered_profiles, mean_profile, std_profile, x_axis, x0, x_min, x_final, roi, debug_dir)

    return x_final, angle, a, b
