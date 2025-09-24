#!/usr/bin/env python3
"""
Batch Processor Module
Orchestratore principale per l'elaborazione di multiple Buste ICCD
Integra XML parsing, image processing con crop.py, e renaming ICCD
"""

import os
import subprocess
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import tempfile

from xml_processor import XMLProcessor, ImageMapping
from iccd_renamer import ICCDRenamer, CropResult, analyze_crop_output


@dataclass
class ProcessingStats:
    """Statistiche del processing batch"""
    total_bustas: int = 0
    total_images: int = 0
    successful_crops: int = 0
    successful_renames: int = 0
    errors: List[str] = None
    processing_time: float = 0.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class BustaResult:
    """Risultato processing di una singola Busta"""
    busta_name: str
    xml_file: str
    images_processed: int
    images_renamed: int
    errors: List[str]
    processing_time: float


class BatchProcessor:
    """
    Orchestratore per elaborazione batch di Buste ICCD
    Coordina XML parsing, crop processing, e renaming
    """

    def __init__(self):
        self.xml_processor = XMLProcessor()
        self.renamer = ICCDRenamer()
        self.stats = ProcessingStats()

        # Path al crop.py di project2
        self.crop_script_path = self._find_crop_script()

    def _find_crop_script(self) -> str:
        """Trova il path al crop.py di project2"""
        # Percorsi possibili per crop.py
        possible_paths = [
            "src/projects/project2/python/crop.py",
            "../project2/python/crop.py",
            "../../project2/python/crop.py"
        ]

        for path in possible_paths:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                print(f"📄 Found crop.py at: {full_path}")
                return full_path

        # Fallback: assume crop.py è nel PATH o nella directory corrente
        print("⚠️  crop.py not found in expected locations, using 'crop.py'")
        return "crop.py"

    def process_all_bustas(self, input_dir: str, output_dir: str) -> ProcessingStats:
        """
        Processa tutte le Buste nell'input directory

        Args:
            input_dir: Directory contenente le cartelle Busta_XX e file XML
            output_dir: Directory di output per file ICCD rinominati

        Returns:
            ProcessingStats con statistiche complete
        """
        start_time = datetime.now()
        print(f"🚀 Starting batch processing...")
        print(f"📁 Input: {input_dir}")
        print(f"📁 Output: {output_dir}")

        try:
            # Phase 1: XML Processing e discovery
            print("\n📋 Phase 1: XML Processing and Discovery")
            mappings = self.xml_processor.process_all_bustas(input_dir)

            if not mappings:
                print("❌ No valid mappings found. Check XML files and image folders.")
                return self.stats

            self.stats.total_images = len(mappings)

            # Raggruppa mappings per Busta
            busta_groups = self._group_mappings_by_busta(mappings)
            self.stats.total_bustas = len(busta_groups)

            print(f"📊 Found {self.stats.total_bustas} Bustas with {self.stats.total_images} total images")

            # Phase 2: Crea struttura directory output
            print("\n📁 Phase 2: Creating Output Directory Structure")
            fascicolo_dirs = self.renamer.create_iccd_directory_structure(output_dir, mappings)

            # Phase 3: Image Processing per ogni Busta
            print("\n🖼️  Phase 3: Image Processing and Renaming")

            for busta_name, busta_mappings in busta_groups.items():
                print(f"\n🔄 Processing {busta_name}...")

                result = self.process_single_busta(busta_mappings, fascicolo_dirs)

                self.stats.successful_crops += result.images_processed
                self.stats.successful_renames += result.images_renamed
                self.stats.errors.extend(result.errors)

                print(f"✅ {busta_name}: {result.images_processed}/{len(busta_mappings)} processed, "
                      f"{result.images_renamed} renamed")

            # Phase 4: Finalization e reporting
            print("\n📊 Phase 4: Finalization and Reporting")
            self._generate_final_report(output_dir)

        except Exception as e:
            error_msg = f"Critical error in batch processing: {e}"
            print(f"❌ {error_msg}")
            self.stats.errors.append(error_msg)

        # Calcola tempo totale
        end_time = datetime.now()
        self.stats.processing_time = (end_time - start_time).total_seconds()

        self._print_final_stats()
        return self.stats

    def process_single_busta(self, busta_mappings: List[ImageMapping],
                           fascicolo_dirs: Dict[str, str]) -> BustaResult:
        """
        Processa una singola Busta (gruppo di immagini)

        Args:
            busta_mappings: Lista di mappings per questa Busta
            fascicolo_dirs: Dizionario directory fascicoli

        Returns:
            BustaResult con statistiche processing
        """
        start_time = datetime.now()
        busta_name = os.path.basename(busta_mappings[0].busta_folder)

        result = BustaResult(
            busta_name=busta_name,
            xml_file="",
            images_processed=0,
            images_renamed=0,
            errors=[],
            processing_time=0.0
        )

        # Crea directory temporanea per crop output
        with tempfile.TemporaryDirectory() as temp_dir:

            for mapping in busta_mappings:
                try:
                    # Percorso immagine originale
                    original_image = os.path.join(mapping.busta_folder, mapping.original_filename)

                    if not os.path.exists(original_image):
                        error_msg = f"Image not found: {original_image}"
                        result.errors.append(error_msg)
                        continue

                    # Chiama crop.py per processing
                    crop_result = self.call_crop_processor(original_image, temp_dir)

                    if crop_result:
                        result.images_processed += 1

                        # Applica renaming ICCD
                        renamed_count = self.apply_iccd_renaming(mapping, crop_result, fascicolo_dirs)
                        result.images_renamed += renamed_count

                    else:
                        result.errors.append(f"Crop processing failed for {mapping.original_filename}")

                except Exception as e:
                    error_msg = f"Error processing {mapping.original_filename}: {e}"
                    result.errors.append(error_msg)
                    print(f"❌ {error_msg}")

        # Calcola tempo processing
        end_time = datetime.now()
        result.processing_time = (end_time - start_time).total_seconds()

        return result

    def call_crop_processor(self, image_path: str, output_dir: str) -> Optional[CropResult]:
        """
        Chiama crop.py di project2 per elaborare l'immagine

        Args:
            image_path: Path all'immagine da processare
            output_dir: Directory temporanea per output

        Returns:
            CropResult con informazioni sui file generati
        """
        try:
            # Prepara comando crop.py
            cmd = [
                sys.executable,  # Python executable corrente
                self.crop_script_path,
                image_path,
                "--side", "center",  # Auto-detection fold
                output_dir,
                "--output_format", "jpg",  # Output in JPG per performance
                "--rotate",  # Abilita rotazione
                "--smart_crop"  # Abilita smart crop
            ]

            # Esegui crop.py
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                print(f"❌ Crop.py failed for {os.path.basename(image_path)}: {result.stderr}")
                return None

            # Analizza output per determinare risultato crop
            original_filename = os.path.basename(image_path)
            crop_result = analyze_crop_output(output_dir, result.stdout, original_filename)

            print(f"🔄 Processed {original_filename}: "
                  f"{'fold detected' if crop_result.fold_detected else 'no fold'}")

            return crop_result

        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout processing {os.path.basename(image_path)}")
            return None
        except Exception as e:
            print(f"❌ Error calling crop.py for {image_path}: {e}")
            return None

    def apply_iccd_renaming(self, mapping: ImageMapping, crop_result: CropResult,
                          fascicolo_dirs: Dict[str, str]) -> int:
        """
        Applica renaming ICCD ai file processati

        Args:
            mapping: Mapping XML per l'immagine
            crop_result: Risultato del crop processing
            fascicolo_dirs: Directory fascicoli

        Returns:
            Numero di file rinominati con successo
        """
        renamed_count = 0

        try:
            # Ottieni directory target
            target_dir = self.renamer.get_target_directory(mapping, fascicolo_dirs)

            if not target_dir:
                print(f"❌ Cannot determine target directory for {mapping.original_filename}")
                return 0

            # Gestisci renaming in base a fold detection
            renamings = self.renamer.handle_page_splitting(mapping, crop_result)

            for source_file, target_filename in renamings:
                success = self.renamer.apply_naming_convention(
                    source_file, target_filename, target_dir
                )

                if success:
                    renamed_count += 1

        except Exception as e:
            print(f"❌ Error renaming files for {mapping.original_filename}: {e}")

        return renamed_count

    def _group_mappings_by_busta(self, mappings: List[ImageMapping]) -> Dict[str, List[ImageMapping]]:
        """Raggruppa mappings per Busta"""
        groups = {}

        for mapping in mappings:
            busta_name = os.path.basename(mapping.busta_folder)

            if busta_name not in groups:
                groups[busta_name] = []

            groups[busta_name].append(mapping)

        return groups

    def _generate_final_report(self, output_dir: str):
        """Genera report finale del processing"""
        # Report delle rinominazioni
        renaming_report = os.path.join(output_dir, "renaming_report.json")
        self.renamer.generate_processing_report(renaming_report)

        # Report dei mappings estratti
        mappings_csv = os.path.join(output_dir, "extracted_mappings.csv")
        self.xml_processor.export_mappings_csv(mappings_csv)

        # Report generale
        general_report = {
            'processing_stats': {
                'total_bustas': self.stats.total_bustas,
                'total_images': self.stats.total_images,
                'successful_crops': self.stats.successful_crops,
                'successful_renames': self.stats.successful_renames,
                'processing_time_seconds': self.stats.processing_time,
                'success_rate_crop': (self.stats.successful_crops / self.stats.total_images * 100)
                if self.stats.total_images > 0 else 0,
                'success_rate_rename': (self.stats.successful_renames / self.stats.total_images * 100)
                if self.stats.total_images > 0 else 0
            },
            'errors': self.stats.errors,
            'timestamp': datetime.now().isoformat()
        }

        general_report_file = os.path.join(output_dir, "processing_summary.json")
        with open(general_report_file, 'w', encoding='utf-8') as f:
            json.dump(general_report, f, indent=2, ensure_ascii=False)

        print(f"📊 Reports generated in {output_dir}")

    def _print_final_stats(self):
        """Stampa statistiche finali"""
        print("\n" + "="*60)
        print("📊 PROCESSING SUMMARY")
        print("="*60)
        print(f"🏷️  Total Bustas processed: {self.stats.total_bustas}")
        print(f"🖼️  Total images found: {self.stats.total_images}")
        print(f"✂️  Successfully cropped: {self.stats.successful_crops}")
        print(f"📝 Successfully renamed: {self.stats.successful_renames}")

        if self.stats.total_images > 0:
            crop_rate = (self.stats.successful_crops / self.stats.total_images) * 100
            rename_rate = (self.stats.successful_renames / self.stats.total_images) * 100
            print(f"📈 Crop success rate: {crop_rate:.1f}%")
            print(f"📈 Rename success rate: {rename_rate:.1f}%")

        print(f"⏱️  Total processing time: {self.stats.processing_time:.1f} seconds")

        if self.stats.errors:
            print(f"⚠️  Errors encountered: {len(self.stats.errors)}")
            print("First 5 errors:")
            for error in self.stats.errors[:5]:
                print(f"   • {error}")

        print("="*60)


def integrate_with_crop_py(image_path: str, crop_params: Dict) -> CropResult:
    """
    Funzione helper per integrare con crop.py
    Questa funzione può essere usata da altri moduli
    """
    processor = BatchProcessor()
    temp_dir = tempfile.mkdtemp()

    try:
        result = processor.call_crop_processor(image_path, temp_dir)
        return result
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Test del modulo
    import argparse

    parser = argparse.ArgumentParser(description="Batch processor for ICCD Bustas")
    parser.add_argument("input_dir", help="Input directory containing Busta folders and XML files")
    parser.add_argument("output_dir", help="Output directory for ICCD renamed files")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"❌ Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    # Crea processor e avvia processing
    processor = BatchProcessor()
    stats = processor.process_all_bustas(args.input_dir, args.output_dir)

    # Exit code basato su successo
    if len(stats.errors) > 0:
        print(f"\n⚠️  Processing completed with {len(stats.errors)} errors")
        sys.exit(1)
    else:
        print(f"\n✅ Processing completed successfully!")
        sys.exit(0)