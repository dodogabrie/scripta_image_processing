#!/usr/bin/env python3

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.image_io import load_image, save_image_preserve_format, generate_output_paths
from src.fold_detection import auto_detect_side
from src.image_processing import process_image
from src.utils import resize_width_hd
from src.debug_tools import save_debug_line_visualization
from src.file_listener import start_file_listener_thread, create_default_rename_map


def find_images_recursive(input_dir, format_extensions=['.tif', '.tiff', '.jpg', '.jpeg']):
    """
    Trova tutti i file immagine ricorsivamente nella directory di input.
    
    Args:
        input_dir (str): Directory di input
        format_extensions (list): Lista di estensioni da cercare
    
    Returns:
        list: Lista dei percorsi completi dei file immagine trovati
    """
    image_files = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in format_extensions:
                image_files.append(os.path.join(root, f))
    return image_files


def write_info_json(output_dir, info_data):
    """Scrive il file info.json nella directory di output."""
    info_path = os.path.join(output_dir, 'info.json')
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info_data, f, indent=2, ensure_ascii=False)


def get_file_size_gb(file_path):
    """Ottiene la dimensione del file in GB."""
    return os.path.getsize(file_path) / (1024**3)


def process_single_image(input_path, output_dir, side=None, output_format=None, 
                        apply_rotation=False, smart_crop=False, debug=False):
    """
    Processa una singola immagine usando la funzionalità di crop.py
    
    Args:
        input_path (str): Percorso dell'immagine di input
        output_dir (str): Directory di output
        side (str): Lato della piega ('left', 'right', 'center', None per auto-detect)
        output_format (str): Formato di output ('jpg', 'png', 'tiff', None per mantenere originale)
        apply_rotation (bool): Se applicare la rotazione
        smart_crop (bool): Se usare il crop intelligente
        debug (bool): Se generare file di debug
    
    Returns:
        tuple: (success, message, debug_info)
    """
    try:
        # Carica l'immagine
        img = load_image(input_path)
        
        # Calcola il percorso relativo per mantenere la struttura delle cartelle
        rel_path = os.path.relpath(input_path, os.path.dirname(input_path))
        
        # Genera i percorsi di output
        if output_format:
            # Cambia l'estensione se specificato un formato
            base_name = os.path.splitext(rel_path)[0]
            output_file = os.path.join(output_dir, base_name + f".{output_format}")
        else:
            output_file = os.path.join(output_dir, rel_path)
        
        # Assicurati che la directory di output esista
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Genera i percorsi per left e right
        path_left, path_right, base_path = generate_output_paths(
            input_path, output_file
        )
        
        # Se è specificato un formato, aggiorna le estensioni
        if output_format:
            base_left, _ = os.path.splitext(path_left)
            base_right, _ = os.path.splitext(path_right)
            path_left = base_left + f".{output_format}"
            path_right = base_right + f".{output_format}"
        
        # Debug directory
        debug_dir = None
        if debug:
            debug_dir = base_path + "_debug"
        
        # Rileva il lato automaticamente se non specificato
        detected_side = auto_detect_side(img) if side is None else side
        
        if detected_side not in ('left', 'right', 'center'):
            # Salva originale se non rilevato
            if output_format:
                width = min(1920, img.shape[1])
                hd_img = resize_width_hd(img, target_width=width)
                save_image_preserve_format(hd_img, path_left)
            else:
                save_image_preserve_format(img, path_left)
            
            return True, f"Piega non rilevata, salvato originale: {path_left}", {
                'x_fold': None, 'angle': None, 'side': detected_side
            }
        
        # Processa l'immagine
        left_side, right_side, debug_info = process_image(
            img, detected_side, 
            debug=debug, debug_dir=debug_dir,
            apply_rotation=apply_rotation, 
            smart_crop=smart_crop
        )
        
        # Salva le immagini debug
        if debug_dir and debug_info.get('x_fold') is not None:
            save_debug_line_visualization(
                img, debug_info['x_fold'], debug_info['angle'],
                debug_info['slope'], debug_info['intercept'],
                os.path.join(debug_dir, "fold_line_visualization.jpg")
            )
        
        # Salva i risultati
        saved_files = []
        if left_side is not None:
            if output_format:
                width = min(1920, left_side.shape[1])
                left_processed = resize_width_hd(left_side, target_width=width)
            else:
                left_processed = left_side
            
            save_image_preserve_format(left_processed, path_left)
            saved_files.append(path_left)
        
        if right_side is not None:
            if output_format:
                width = min(1920, right_side.shape[1])
                right_processed = resize_width_hd(right_side, target_width=width)
            else:
                right_processed = right_side
            
            save_image_preserve_format(right_processed, path_right)
            saved_files.append(path_right)
        
        debug_info['side'] = detected_side
        debug_info['saved_files'] = saved_files
        
        return True, f"Processato: {', '.join(saved_files)}", debug_info
        
    except Exception as e:
        return False, f"Errore processing {input_path}: {str(e)}", {}


def main(input_dir, output_dir, side=None, output_format=None, image_input_format=None,
         apply_rotation=False, smart_crop=False, debug=False, verbose=True,
         enable_file_listener=False, rename_map=None):
    """
    Funzione principale per processare le immagini in batch.
    
    Args:
        input_dir (str): Directory di input
        output_dir (str): Directory di output
        side (str): Lato della piega (None per auto-detect)
        output_format (str): Formato di output
        image_input_format (str): Formato delle immagini di input da cercare
        apply_rotation (bool): Se applicare la rotazione
        smart_crop (bool): Se usare il crop intelligente
        debug (bool): Se generare file di debug
        verbose (bool): Se mostrare output verbose
        enable_file_listener (bool): Se abilitare il file listener per rinominazioni
        rename_map (dict): Mappa di rinominazione per il file listener
    """
    print(f"Avvio elaborazione doppia pagina...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Avvia il file listener se richiesto
    file_listener = None
    if enable_file_listener:
        if rename_map is None:
            rename_map = create_default_rename_map()
        
        print(f"Avvio file listener con mappa: {rename_map}")
        file_listener = start_file_listener_thread(output_dir, rename_map, verbose)
    
    start_time = time.time()
    start_datetime = datetime.now().isoformat()
    
    # Assicurati che la directory di output esista
    os.makedirs(output_dir, exist_ok=True)
    
    # Determina le estensioni da cercare
    if image_input_format:
        image_input_format = image_input_format.lower()
        if image_input_format in ['tif', 'tiff']:
            format_extensions = ['.tif', '.tiff']
        elif image_input_format in ['jpg', 'jpeg']:
            format_extensions = ['.jpg', '.jpeg']
        else:
            raise ValueError("Formato immagine non supportato. Usa 'tif', 'tiff', 'jpg', o 'jpeg'.")
    else:
        format_extensions = ['.tif', '.tiff', '.jpg', '.jpeg']
    
    # Trova tutte le immagini
    image_files = find_images_recursive(input_dir, format_extensions)
    total_files = len(image_files)
    
    if total_files == 0:
        print("Nessuna immagine trovata nella directory di input.")
        return
    
    # Calcola dimensione totale
    total_size_gb = sum(get_file_size_gb(f) for f in image_files)
    
    # Determina il formato primario
    formats = {}
    for f in image_files:
        ext = os.path.splitext(f)[1].lower()
        formats[ext] = formats.get(ext, 0) + 1
    primary_format = max(formats.keys(), key=formats.get) if formats else 'unknown'
    
    # Crea il file info.json iniziale
    info_data = {
        "total_images": total_files,
        "processed": 0,
        "primary_format": primary_format.upper().replace('.', ''),
        "all_formats": formats,
        "total_size_gb": round(total_size_gb, 3),
        "start_time": start_datetime,
        "duration_seconds": None,
        "status": "processing",
        "parameters": {
            "side": side,
            "output_format": output_format,
            "apply_rotation": apply_rotation,
            "smart_crop": smart_crop,
            "debug": debug,
            "file_listener_enabled": enable_file_listener,
            "rename_map": rename_map if enable_file_listener else None
        }
    }
    
    write_info_json(output_dir, info_data)
    
    # Processa ogni immagine
    processed_count = 0
    error_count = 0
    
    for i, input_path in enumerate(image_files):
        if verbose:
            rel_path = os.path.relpath(input_path, input_dir)
            print(f"[{i+1}/{total_files}] Processing: {rel_path}")
        
        success, message, debug_info = process_single_image(
            input_path, output_dir, side, output_format,
            apply_rotation, smart_crop, debug
        )
        
        if success:
            processed_count += 1
            if verbose:
                rotation_status = "con rotazione" if debug_info.get('rotation_applied') else "senza rotazione"
                crop_status = "smart crop" if debug_info.get('smart_crop_applied') else "crop standard"
                if debug_info.get('x_fold'):
                    print(f"  x: {debug_info['x_fold']}, angolo: {debug_info['angle']:.2f}°, {rotation_status}, {crop_status}")
                print(f"  {message}")
        else:
            error_count += 1
            print(f"  ERRORE: {message}")
        
        # Aggiorna info.json
        info_data["processed"] = i + 1
        write_info_json(output_dir, info_data)
    
    # Completa info.json
    end_time = time.time()
    duration_seconds = round(end_time - start_time, 2)
    
    info_data["duration_seconds"] = duration_seconds
    info_data["status"] = "completed"
    info_data["end_time"] = datetime.now().isoformat()
    info_data["summary"] = {
        "processed_successfully": processed_count,
        "errors": error_count,
        "success_rate": round(processed_count / total_files * 100, 1) if total_files > 0 else 0
    }
    
    write_info_json(output_dir, info_data)
    
    print(f"\nElaborazione completata!")
    print(f"Processate con successo: {processed_count}/{total_files}")
    print(f"Errori: {error_count}")
    print(f"Tempo totale: {duration_seconds} secondi")
    
    # Ferma il file listener se era attivo
    if file_listener:
        print("Fermando il file listener...")
        file_listener.stop_monitoring()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ritaglia un doppio foglio A4 sulla piega e aggiorna l'ordine delle pagine generate dal ritaglio")
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    parser.add_argument("--side", choices=['left', 'right', 'center'], default=None,
                        help="Lato della piega (default: auto-detect)")
    parser.add_argument("--output_format", choices=['jpg', 'png', 'tiff'], default=None,
                        help="Formato di output (default: mantieni originale)")
    parser.add_argument("--image_input_format", choices=['tif', 'tiff', 'jpg', 'jpeg'], default=None,
                        help="Formato delle immagini di input da cercare (default: tutti)")
    parser.add_argument("--rotate", action='store_true', default=False,
                        help="Applica rotazione per raddrizzare la piega")
    parser.add_argument("--smart_crop", action='store_true', default=False,
                        help="Usa rilevamento intelligente del bordo documento")
    parser.add_argument("--debug", action='store_true', default=False,
                        help="Genera file di debug")
    parser.add_argument("--verbose", action='store_true', default=True,
                        help="Output verbose")
    parser.add_argument("--enable_file_listener", action='store_true', default=False,
                        help="Abilita il file listener per rinominazioni automatiche")
    parser.add_argument("--rename_map_file", type=str, default=None,
                        help="File JSON contenente la mappa di rinominazione")
    
    args = parser.parse_args()
    
    # Carica la mappa di rinominazione se specificata
    rename_map = None
    if args.enable_file_listener:
        if args.rename_map_file and os.path.exists(args.rename_map_file):
            import json
            with open(args.rename_map_file, 'r', encoding='utf-8') as f:
                rename_map = json.load(f)
            print(f"Caricata mappa di rinominazione da: {args.rename_map_file}")
        else:
            rename_map = create_default_rename_map()
            print("Uso mappa di rinominazione di default")
    
    main(
        args.input_dir, args.output_dir,
        side=args.side,
        output_format=args.output_format,
        image_input_format=args.image_input_format,
        apply_rotation=args.rotate,
        smart_crop=args.smart_crop,
        debug=args.debug,
        verbose=args.verbose,
        enable_file_listener=args.enable_file_listener,
        rename_map=rename_map
    )