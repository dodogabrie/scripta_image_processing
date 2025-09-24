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
# auto_detect_side removed - fold is always center
from src.image_processing import process_image
from src.page_processor import process_page_if_needed
from src.contour_detector.utils import save_outputs
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


def process_single_image(input_path, output_dir, input_base_dir, side=None, output_format=None,
                        apply_rotation=False, smart_crop=False, debug=False, verbose=True, contour_border=150, fold_border=None, save_thumbs=False):
    """
    Processa una singola immagine usando la funzionalità di crop.py

    Args:
        input_path (str): Percorso dell'immagine di input
        output_dir (str): Directory di output
        input_base_dir (str): Directory base di input per preservare la struttura
        side (str): Lato della piega ('left', 'right', 'center', None per auto-detect)
        output_format (str): Formato di output ('jpg', 'png', 'tiff', None per mantenere originale)
        apply_rotation (bool): Se applicare la rotazione
        smart_crop (bool): Se usare il crop intelligente
        debug (bool): Se generare file di debug
    
    Returns:
        tuple: (success, message, debug_info)
    """
    try:
        # If fold_border not specified, use same value as contour_border
        if fold_border is None:
            fold_border = contour_border

        # Carica l'immagine
        img = load_image(input_path)
        
        # Genera i percorsi di output preservando la struttura delle cartelle
        if output_format:
            # Cambia l'estensione se specificato un formato
            input_base, _ = os.path.splitext(input_path)
            modified_output = output_dir
        else:
            modified_output = output_dir
        
        # Usa generate_output_paths con input_base_dir per preservare la struttura
        path_left, path_right, base_path = generate_output_paths(
            input_path, modified_output, input_base_dir
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
        detected_side = "center" if side is None else side

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

        # Apply page processing (contour detection for A3 landscape)
        processed_img, was_processed, actual_border = process_page_if_needed(
            img,
            image_path=input_path,
            debug=debug,
            contour_border=contour_border
        )
        if verbose and was_processed:
            print(f"  [OK] Applicato processing pagina (correzione prospettiva A3 landscape) - border: {actual_border}px")
        elif verbose:
            print("  [INFO] Processing pagina saltato (formato non A3 landscape)")

        # Processa l'immagine
        left_side, right_side, debug_info = process_image(
            processed_img, detected_side,
            debug=debug, debug_dir=debug_dir,
            apply_rotation=apply_rotation,
            smart_crop=smart_crop,
            fold_border=fold_border,
            image_path=input_path
        )
        
        # Salva le immagini debug
        if debug_dir and debug_info.get('x_fold') is not None:
            save_debug_line_visualization(
                processed_img, debug_info['x_fold'], debug_info['angle'],
                debug_info['slope'], debug_info['intercept'],
                os.path.join(debug_dir, "fold_line_visualization.jpg")
            )
        
        # Salva i risultati
        saved_files = []

        # Check if fold detection was applied
        fold_detected = debug_info['x_fold'] is not None

        if fold_detected:
            # Fold detection applied - save left and right sides
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
        else:
            # No fold detection - save with original name (no _left/_right suffix)
            original_output_path = base_path + os.path.splitext(input_path)[1]

            if output_format:
                # Change extension if output format specified
                original_output_path = os.path.splitext(original_output_path)[0] + f".{output_format}"
                width = min(1920, left_side.shape[1])
                processed = resize_width_hd(left_side, target_width=width)
            else:
                processed = left_side

            save_image_preserve_format(processed, original_output_path)
            saved_files.append(original_output_path)
        
        # Generate comparison thumbnails if requested
        if save_thumbs:
            thumb_dir = base_path + "_thumbs"
            os.makedirs(thumb_dir, exist_ok=True)

            if left_side is not None:
                # For thumbnails: use original full image vs processed result
                save_outputs(
                    img,  # True original image (uncropped, unprocessed)
                    left_processed,  # Final processed result
                    path_left,  # This will be ignored since we only want thumbs
                    output_path_thumb=thumb_dir,
                    original_path=input_path
                )

            if right_side is not None:
                # For thumbnails: use original full image vs processed result
                save_outputs(
                    img,  # True original image (uncropped, unprocessed)
                    right_processed,  # Final processed result
                    path_right,  # This will be ignored since we only want thumbs
                    output_path_thumb=thumb_dir,
                    original_path=input_path
                )

        debug_info['side'] = detected_side
        debug_info['saved_files'] = saved_files

        return True, f"Processato: {', '.join(saved_files)}", debug_info
        
    except Exception as e:
        return False, f"Errore processing {input_path}: {str(e)}", {}


def main(input_dir, output_dir, side=None, output_format=None, image_input_format=None,
         apply_rotation=False, smart_crop=False, debug=False, verbose=True,
         enable_file_listener=False, rename_map=None, contour_border=150, fold_border=None, save_thumbs=False,
         process_jpg=True, process_tiff=True):
    """
    Funzione principale per processare le immagini in batch con supporto ICCD Busta.

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
    print(f"[INFO] Avvio elaborazione doppia pagina...")
    print(f"[INFO] Input directory: {input_dir}")
    print(f"[INFO] Output directory: {output_dir}")

    # Check if input contains ICCD Folder+XML structure
    try:
        # Add current directory to path for imports
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        from xml_processor import has_busta_structure

        if has_busta_structure(input_dir):
            print("[INFO] Detected ICCD Folder+XML structure - using XML-based processing")
            return process_iccd_bustas(
                input_dir, output_dir, side, output_format,
                apply_rotation, smart_crop, debug, verbose,
                contour_border, fold_border, save_thumbs,
                process_jpg, process_tiff
            )
        else:
            print("[INFO] Standard batch processing mode (no Folder+XML pairs found)")
    except ImportError as e:
        print(f"[WARNING] XML processor not available: {e}, using standard processing")
    except Exception as e:
        print(f"[WARNING] Error checking Folder+XML structure: {e}, using standard processing")

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
            input_path, output_dir, input_dir, side, output_format,
            apply_rotation, smart_crop, debug, verbose, contour_border, fold_border, save_thumbs
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


def process_iccd_bustas(input_dir, output_dir, side=None, output_format=None,
                       apply_rotation=False, smart_crop=False, debug=False, verbose=True,
                       contour_border=150, fold_border=None, save_thumbs=False,
                       process_jpg=True, process_tiff=True):
    """
    Processa tutte le Buste ICCD nell'input directory con XML mapping e renaming

    Args:
        input_dir (str): Directory contenente Busta_XX folders e XML files
        output_dir (str): Directory di output per file ICCD rinominati
        Altri args: come nel main standard
    """
    from xml_processor import XMLProcessor
    from iccd_renamer import ICCDRenamer, analyze_crop_output, CropResult
    import tempfile

    start_time = time.time()
    start_datetime = datetime.now().isoformat()

    print("\n[PHASE 1] XML Processing and Discovery")

    # Inizializza processors
    xml_processor = XMLProcessor()
    renamer = ICCDRenamer()

    # Processa tutti gli XML e estrai mappings
    print(f"[INFO] File processing settings: JPG={process_jpg}, TIFF={process_tiff}")
    mappings = xml_processor.process_all_bustas(input_dir, process_jpg, process_tiff)

    if not mappings:
        print("[ERROR] No valid ICCD mappings found. Check XML files and image folders.")
        return

    total_images = len(mappings)
    print(f"[INFO] Found {total_images} images to process across Bustas")

    # Phase 2: Crea struttura directory output ICCD
    print("\n[PHASE 2] Creating ICCD Output Directory Structure")
    fascicolo_dirs = renamer.create_iccd_directory_structure(output_dir, mappings)

    # Phase 3: Process images con XML mapping
    print(f"\n[PHASE 3] Processing Images with ICCD Renaming")

    processed_count = 0
    renamed_count = 0
    error_count = 0

    # Create temp directory for intermediate processing
    with tempfile.TemporaryDirectory() as temp_dir:

        for i, mapping in enumerate(mappings):
            if verbose:
                print(f"[{i+1}/{total_images}] Processing: {mapping.original_filename}")

            try:
                # Path originale immagine - usa full_path se disponibile
                if hasattr(mapping, 'full_path') and mapping.full_path:
                    original_image = mapping.full_path
                else:
                    # Fallback per compatibilità
                    if hasattr(mapping, 'subdir') and mapping.subdir:
                        original_image = os.path.join(mapping.busta_folder, mapping.subdir, mapping.original_filename)
                    else:
                        original_image = os.path.join(mapping.busta_folder, mapping.original_filename)

                if not os.path.exists(original_image):
                    error_count += 1
                    print(f"[ERROR] Image not found: {original_image}")
                    continue

                # Process image usando la logica esistente
                temp_output = os.path.join(temp_dir, f"temp_{i}")
                os.makedirs(temp_output, exist_ok=True)

                success, message, debug_info = process_single_image(
                    original_image, temp_output, mapping.busta_folder,
                    side=side, output_format=None,  # Preserve original format
                    apply_rotation=apply_rotation, smart_crop=smart_crop,
                    debug=debug, verbose=False,  # Suppress verbose for cleaner output
                    contour_border=contour_border, fold_border=fold_border,
                    save_thumbs=False  # No thumbs in temp
                )

                if not success:
                    error_count += 1
                    print(f"[ERROR] Processing failed: {message}")
                    continue

                processed_count += 1

                # Analizza risultato crop per determinare files generati
                saved_files = debug_info.get('saved_files', [])
                fold_detected = debug_info.get('x_fold') is not None

                if fold_detected and len(saved_files) == 2:
                    # Fold rilevato - files left/right
                    left_file = next((f for f in saved_files if '_left' in f), None)
                    right_file = next((f for f in saved_files if '_right' in f), None)

                    crop_result = CropResult(
                        fold_detected=True,
                        left_file=left_file,
                        right_file=right_file,
                        original_filename=mapping.original_filename
                    )
                else:
                    # No fold - file singolo
                    single_file = saved_files[0] if saved_files else None

                    crop_result = CropResult(
                        fold_detected=False,
                        single_file=single_file,
                        original_filename=mapping.original_filename
                    )

                # Applica renaming ICCD
                base_target_dir = renamer.get_target_directory(mapping, fascicolo_dirs)

                if base_target_dir:
                    # Create subdirectory in output if source has subdirectory
                    final_target_dir = base_target_dir
                    if hasattr(mapping, 'subdir') and mapping.subdir:
                        final_target_dir = os.path.join(base_target_dir, mapping.subdir)
                        os.makedirs(final_target_dir, exist_ok=True)
                        if verbose:
                            print(f"  [INFO] Created subdirectory: {mapping.subdir}")

                    renamings = renamer.handle_page_splitting(mapping, crop_result)

                    for source_file, target_filename in renamings:
                        success = renamer.apply_naming_convention(
                            source_file, target_filename, final_target_dir
                        )

                        if success:
                            renamed_count += 1

                # Status update
                if verbose:
                    fold_status = "fold detected" if fold_detected else "no fold"
                    print(f"  [OK] {fold_status}, {len(renamings) if 'renamings' in locals() else 0} files renamed")

            except Exception as e:
                error_count += 1
                print(f"[ERROR] Error processing {mapping.original_filename}: {e}")

    # Phase 4: Final reporting
    print(f"\n[PHASE 4] Final Report")

    end_time = time.time()
    duration_seconds = round(end_time - start_time, 2)

    print("="*60)
    print("[SUMMARY] ICCD PROCESSING SUMMARY")
    print("="*60)
    print(f"Total images found: {total_images}")
    print(f"Successfully processed: {processed_count}")
    print(f"Successfully renamed: {renamed_count}")
    print(f"Errors: {error_count}")

    if total_images > 0:
        success_rate = (processed_count / total_images) * 100
        rename_rate = (renamed_count / total_images) * 100
        print(f"Processing success rate: {success_rate:.1f}%")
        print(f"Renaming success rate: {rename_rate:.1f}%")

    print(f"Total processing time: {duration_seconds} seconds")

    # Generate reports
    try:
        import json
        report_file = os.path.join(output_dir, "iccd_processing_report.json")
        renamer.generate_processing_report(report_file.replace('.json', '_renaming.json'))

        # General report
        general_report = {
            'timestamp': datetime.now().isoformat(),
            'total_images': total_images,
            'processed': processed_count,
            'renamed': renamed_count,
            'errors': error_count,
            'duration_seconds': duration_seconds,
            'success_rates': {
                'processing': round(success_rate, 1) if total_images > 0 else 0,
                'renaming': round(rename_rate, 1) if total_images > 0 else 0
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(general_report, f, indent=2, ensure_ascii=False)

        print(f"Reports saved to: {output_dir}")

    except Exception as e:
        print(f"[WARNING] Could not generate reports: {e}")

    print("="*60)

    if error_count == 0:
        print("[SUCCESS] ICCD processing completed successfully!")
    else:
        print(f"[WARNING] ICCD processing completed with {error_count} errors")

    return error_count == 0


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
    parser.add_argument("--contour_border", type=int, default=150,
                        help="Border pixels per correzione prospettiva contour detection (default: 150)")
    parser.add_argument("--fold_border", type=int, default=None,
                        help="Border pixels attorno alla piega per contenuto sovrapposto (default: same as contour_border)")
    parser.add_argument("--save_thumbs", action='store_true', default=False,
                        help="Genera thumbnails di confronto prima/dopo per ogni lato")
    parser.add_argument("--process_jpg", action='store_true', default=True,
                        help="Processa file .jpg/.jpeg (default: True)")
    parser.add_argument("--no_process_jpg", dest='process_jpg', action='store_false',
                        help="Non processare file .jpg/.jpeg")
    parser.add_argument("--process_tiff", action='store_true', default=True,
                        help="Processa file .tiff/.tif (default: True)")
    parser.add_argument("--no_process_tiff", dest='process_tiff', action='store_false',
                        help="Non processare file .tiff/.tif")

    args = parser.parse_args()

    # If fold_border not specified, use same value as contour_border
    if args.fold_border is None:
        args.fold_border = args.contour_border
    
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
        rename_map=rename_map,
        contour_border=args.contour_border,
        fold_border=args.fold_border,
        save_thumbs=args.save_thumbs,
        process_jpg=args.process_jpg,
        process_tiff=args.process_tiff
    )