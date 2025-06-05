import sys
import cv2
import numpy as np
import os
from pathlib import Path

def apply_blur(image, intensity=15):
    """Applica sfocatura all'immagine"""
    return cv2.GaussianBlur(image, (intensity, intensity), 0)

def apply_edge_detection(image):
    """Applica rilevamento bordi"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

def apply_grayscale(image):
    """Converte in scala di grigi"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def main():
    if len(sys.argv) < 3:
        print("Uso: python image_processor.py <input_path> <filter_type>")
        return 1
    
    input_path = sys.argv[1]
    filter_type = sys.argv[2]
    
    try:
        # Carica immagine
        image = cv2.imread(input_path)
        if image is None:
            print(f"Errore: impossibile caricare l'immagine da {input_path}")
            return 1
        
        # Applica filtro
        if filter_type == 'blur':
            processed = apply_blur(image)
        elif filter_type == 'edge':
            processed = apply_edge_detection(image)
        elif filter_type == 'grayscale':
            processed = apply_grayscale(image)
        else:
            print(f"Filtro non riconosciuto: {filter_type}")
            return 1
        
        # Salva immagine elaborata
        output_path = input_path.replace('.', f'_processed_{filter_type}.')
        cv2.imwrite(output_path, processed)
        
        # Restituisce il percorso dell'immagine elaborata
        print(output_path)
        return 0
        
    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
