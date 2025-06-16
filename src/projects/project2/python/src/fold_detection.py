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


def detect_document_edge(img, side, x_fold, debug=False, debug_dir=None):
    """
    Rileva il bordo del documento sul lato opposto alla piega analizzando i profili di luminosità.
    
    L'algoritmo funziona nel seguente modo:
    1. Converte l'immagine in scala di grigi e applica un leggero blur
    2. Definisce una zona di ricerca sul lato opposto alla piega
    3. Calcola i profili di luminosità verticali (media per colonna)
    4. Cerca la caduta più significativa di luminosità che indica il bordo del documento
    5. Calcola il margine in pixel dal bordo dell'immagine al documento
    
    Args:
        img: Immagine di input (BGR)
        side: Lato della piega ('left', 'right', 'center')
        x_fold: Posizione x della piega in pixel
        debug: Se True, salva visualizzazioni di debug
        debug_dir: Directory per salvare i file di debug
    
    Returns:
        Per side='center': tupla (left_margin, right_margin)
        Per altri lati: singolo valore di margine in pixel
    """
    # Prepara l'immagine per l'analisi con maggiore smoothing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1.0)  # Blur più intenso per ridurre il rumore
    h, w = blur.shape
    
    if side == 'left':
        # Piega a sinistra: cerchiamo il bordo destro del documento
        search_start = min(w - 10, x_fold + 50)
        search_end = w - 5
        
        edge_profiles = []
        for x in range(search_start, search_end):
            col_profile = blur[:, x]
            mean_brightness = np.mean(col_profile)
            edge_profiles.append((x, mean_brightness))
            
        margin = find_brightness_drop(edge_profiles, 'right', w)
        
        if debug and debug_dir:
            save_edge_detection_debug(edge_profiles, 'right', margin, x_fold, search_start, search_end, debug_dir, gray)
            
    elif side == 'right':
        # Piega a destra: cerchiamo il bordo sinistro del documento
        search_start = max(5, x_fold - 50)
        search_end = 5
        
        edge_profiles = []
        for x in range(search_start, search_end, -1):
            col_profile = blur[:, x]
            mean_brightness = np.mean(col_profile)
            edge_profiles.append((x, mean_brightness))
            
        margin = find_brightness_drop(edge_profiles, 'left', w)
        
        if debug and debug_dir:
            save_edge_detection_debug(edge_profiles, 'left', margin, x_fold, search_start, search_end, debug_dir, gray)
            
    elif side == 'center':
        # Piega al centro: cerchiamo entrambi i bordi del documento
        
        # Analisi del bordo sinistro
        left_search_start = max(5, x_fold - 50)
        left_edge_profiles = []
        for x in range(left_search_start, 5, -1):
            col_profile = blur[:, x]
            mean_brightness = np.mean(col_profile)
            left_edge_profiles.append((x, mean_brightness))
        
        # Analisi del bordo destro
        right_search_start = min(w - 10, x_fold + 50)
        right_edge_profiles = []
        for x in range(right_search_start, w - 5):
            col_profile = blur[:, x]
            mean_brightness = np.mean(col_profile)
            right_edge_profiles.append((x, mean_brightness))
        
        left_margin = find_brightness_drop(left_edge_profiles, 'left', w)
        right_margin = find_brightness_drop(right_edge_profiles, 'right', w)
        
        if debug and debug_dir:
            save_edge_detection_debug_center(left_edge_profiles, right_edge_profiles, 
                                           left_margin, right_margin, x_fold, debug_dir, gray)
        
        return left_margin, right_margin
    
    return margin


def find_brightness_drop(profiles, side, image_width):
    """
    Analizza i profili di luminosità per trovare la caduta più significativa
    che indica il bordo del documento.
    
    L'algoritmo utilizza:
    1. Media mobile per smussare le variazioni di rumore
    2. Soglia dinamica basata sulla luminosità massima del profilo
    3. Ricerca della massima derivata negativa (caduta più ripida)
    4. Conversione della posizione in margine dal bordo dell'immagine
    
    Args:
        profiles: Lista di tuple (posizione_x, luminosità_media)
        side: Lato da analizzare ('left', 'right')
        image_width: Larghezza dell'immagine in pixel
    
    Returns:
        Margine in pixel dal bordo dell'immagine al documento (0 se non trovato)
    """
    # Verifica che ci siano abbastanza dati per l'analisi
    if not profiles or len(profiles) < 5:
        return 0  # Dati insufficienti per un'analisi affidabile
    
    # Estrae i dati dai profili
    brightnesses = [brightness for _, brightness in profiles]
    positions = [pos for pos, _ in profiles]
    
    # Applica una media mobile più ampia per maggiore smoothing
    # La finestra è adattiva alla quantità di dati disponibili
    window_size = min(8, len(brightnesses) // 3)  # Finestra più grande
    if window_size < 3:
        window_size = min(3, len(brightnesses))
    
    smoothed = []
    for i in range(len(brightnesses)):
        # Calcola la media nella finestra centrata sul punto corrente
        start = max(0, i - window_size // 2)
        end = min(len(brightnesses), i + window_size // 2 + 1)
        avg = sum(brightnesses[start:end]) / (end - start)
        smoothed.append(avg)
    
    # Applica un secondo livello di smoothing con filtro gaussiano
    if len(smoothed) >= 5:
        smoothed_array = np.array(smoothed)
        # Usa un kernel gaussiano per ulteriore smoothing
        kernel_size = min(5, len(smoothed) // 2)
        if kernel_size % 2 == 0:
            kernel_size += 1
        smoothed_final = cv2.GaussianBlur(smoothed_array.reshape(1, -1), (kernel_size, 1), 1.0).flatten()
        smoothed = smoothed_final.tolist()
    
    # Definisce una soglia dinamica più conservativa per identificare aree scure
    # Usa il 75% della luminosità massima come riferimento (più restrittivo)
    threshold = max(smoothed) * 0.75
    
    # Cerca la caduta di luminosità più significativa
    max_drop = 0  # Massima caduta trovata
    best_position = 0  # Posizione della migliore caduta
    
    # Analizza ogni punto per trovare la derivata (tasso di cambiamento)
    # Usa una finestra più ampia per calcolare la derivata
    derivative_window = min(3, len(smoothed) // 4)
    for i in range(derivative_window, len(smoothed) - derivative_window):
        # Calcola la derivata usando una finestra più ampia per maggiore stabilità
        left_avg = sum(smoothed[i-derivative_window:i]) / derivative_window
        right_avg = sum(smoothed[i+1:i+derivative_window+1]) / derivative_window
        current_drop = left_avg - right_avg
        
        # Considera solo cadute significative in aree sufficientemente scure
        if current_drop > max_drop and smoothed[i] < threshold:
            max_drop = current_drop
            best_position = positions[i]
    
    # Converte la posizione trovata in margine dal bordo dell'immagine
    # Soglia più bassa per essere meno restrittivi nel rilevamento
    if max_drop > 3:  # Soglia ridotta per maggiore sensibilità
        if side == 'left':
            # Per il lato sinistro, il margine è la distanza dal bordo sinistro
            margin = best_position
        elif side == 'right':
            # Per il lato destro, il margine è la distanza dal bordo destro
            margin = image_width - best_position
        else:
            margin = 0
        
        # Assicura che il margine sia non negativo
        return max(0, margin)
    
    # Nessuna caduta significativa trovata
    return 0


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


def save_edge_detection_debug(edge_profiles, side, margin, x_fold, search_start, search_end, debug_dir, gray_img):
    """
    Salva una visualizzazione di debug per il rilevamento del bordo del documento (lato singolo).
    """
    import matplotlib.pyplot as plt
    import os
    
    os.makedirs(debug_dir, exist_ok=True)
    
    if not edge_profiles:
        return
    
    positions = [pos for pos, _ in edge_profiles]
    brightnesses = [brightness for _, brightness in edge_profiles]
    
    # Calcola il punto del bordo rilevato
    if side == 'left':
        edge_position = margin
        title = f"Rilevamento Bordo Sinistro - Margine: {margin}px"
    else:
        edge_position = gray_img.shape[1] - margin
        title = f"Rilevamento Bordo Destro - Margine: {margin}px"
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Grafico del profilo di luminosità
    ax1.plot(positions, brightnesses, 'b-', linewidth=2, label='Profilo luminosità')
    ax1.axvline(x_fold, color='red', linestyle='--', linewidth=2, label=f'Piega (x={x_fold})')
    if margin > 0:
        ax1.axvline(edge_position, color='green', linestyle='--', linewidth=2, 
                   label=f'Bordo rilevato (x={edge_position})')
    ax1.axvspan(search_start, search_end, alpha=0.2, color='yellow', label='Area di ricerca')
    ax1.set_xlabel('Posizione X (pixel)')
    ax1.set_ylabel('Luminosità media')
    ax1.set_title(title)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Visualizzazione dell'immagine con overlay
    ax2.imshow(gray_img, cmap='gray', aspect='auto')
    ax2.axvline(x_fold, color='red', linewidth=2, label='Piega')
    if margin > 0:
        ax2.axvline(edge_position, color='green', linewidth=2, label='Bordo rilevato')
    ax2.axvspan(search_start, search_end, alpha=0.3, color='yellow', label='Area di ricerca')
    ax2.set_title('Immagine con overlay di rilevamento')
    ax2.legend()
    
    plt.tight_layout()
    filename = f'edge_detection_{side}.png'
    plt.savefig(os.path.join(debug_dir, filename), dpi=150, bbox_inches='tight')
    plt.close(fig)


def save_edge_detection_debug_center(left_profiles, right_profiles, left_margin, right_margin, x_fold, debug_dir, gray_img):
    """
    Salva una visualizzazione di debug per il rilevamento del bordo del documento (centro - entrambi i lati).
    """
    import matplotlib.pyplot as plt
    import os
    
    os.makedirs(debug_dir, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Grafico dei profili di luminosità
    if left_profiles:
        left_positions = [pos for pos, _ in left_profiles]
        left_brightnesses = [brightness for _, brightness in left_profiles]
        ax1.plot(left_positions, left_brightnesses, 'b-', linewidth=2, label='Profilo sinistro')
    
    if right_profiles:
        right_positions = [pos for pos, _ in right_profiles]
        right_brightnesses = [brightness for _, brightness in right_profiles]
        ax1.plot(right_positions, right_brightnesses, 'orange', linewidth=2, label='Profilo destro')
    
    # Linee di riferimento
    ax1.axvline(x_fold, color='red', linestyle='--', linewidth=2, label=f'Piega (x={x_fold})')
    
    if left_margin > 0:
        left_edge_pos = left_margin
        ax1.axvline(left_edge_pos, color='green', linestyle='--', linewidth=2, 
                   label=f'Bordo sinistro (x={left_edge_pos})')
    
    if right_margin > 0:
        right_edge_pos = gray_img.shape[1] - right_margin
        ax1.axvline(right_edge_pos, color='purple', linestyle='--', linewidth=2, 
                   label=f'Bordo destro (x={right_edge_pos})')
    
    ax1.set_xlabel('Posizione X (pixel)')
    ax1.set_ylabel('Luminosità media')
    ax1.set_title(f'Rilevamento Bordi Centro - Margini: Sinistro={left_margin}px, Destro={right_margin}px')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Visualizzazione dell'immagine con overlay
    ax2.imshow(gray_img, cmap='gray', aspect='auto')
    ax2.axvline(x_fold, color='red', linewidth=2, label='Piega')
    
    if left_margin > 0:
        ax2.axvline(left_margin, color='green', linewidth=2, label='Bordo sinistro')
        # Area di crop sinistro
        ax2.axvspan(0, x_fold + left_margin, alpha=0.2, color='green', label='Crop sinistro')
    
    if right_margin > 0:
        right_edge_pos = gray_img.shape[1] - right_margin
        ax2.axvline(right_edge_pos, color='purple', linewidth=2, label='Bordo destro')
        # Area di crop destro
        ax2.axvspan(x_fold - right_margin, gray_img.shape[1], alpha=0.2, color='purple', label='Crop destro')
    
    ax2.set_title('Immagine con overlay di rilevamento e aree di crop')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(debug_dir, 'edge_detection_center.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
