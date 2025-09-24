#!/usr/bin/env python3
"""
BatchProcessor per workflow ICCD con preservazione metadati
Gestisce il processing completo: XML parsing → Crop → ICCD Rename → Metadata preservation
"""

import os
import sys
import tempfile
import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Import ICCD modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'project2', 'python'))
from xml_processor import XMLProcessor, ImageMapping
from iccd_renamer import ICCDRenamer, analyze_crop_output, CropResult


@dataclass
class ProcessingStats:
    """Statistiche del processing ICCD"""
    total_images: int = 0
    successfully_processed: int = 0
    successfully_renamed: int = 0
    errors: List[str] = None
    processing_time: float = 0.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BatchProcessor:
    """
    BatchProcessor per workflow ICCD completo
    """

    def __init__(self):
        self.xml_processor = XMLProcessor()
        self.iccd_renamer = ICCDRenamer()
        self.stats = ProcessingStats()

    def process_all_bustas(self, input_dir: str, output_dir: str) -> ProcessingStats:
        """
        Processo completo per tutte le Buste ICCD

        Args:
            input_dir: Directory contenente Buste + XML
            output_dir: Directory output ICCD

        Returns:
            ProcessingStats con risultati del processing
        """
        start_time = datetime.now()
        print(f"[PHASE 1] XML Processing & Image Discovery")

        # Process all XML files and extract mappings
        mappings = self.xml_processor.process_all_bustas(input_dir)
        self.stats.total_images = len(mappings)

        if not mappings:
            print("[ERROR] No image mappings found")
            return self.stats

        print(f"[INFO] Found {len(mappings)} images to process across Bustas")

        # Create ICCD directory structure
        print(f"\n[PHASE 2] Creating ICCD Output Directory Structure")
        fascicolo_dirs = self.iccd_renamer.create_iccd_directory_structure(output_dir, mappings)

        # Process each image
        print(f"\n[PHASE 3] Processing Images with ICCD Renaming")
        for i, mapping in enumerate(mappings, 1):
            print(f"[{i}/{len(mappings)}] Processing: {mapping.original_filename}")

            try:
                success = self.process_single_image(mapping, fascicolo_dirs, output_dir)

                if success:
                    self.stats.successfully_processed += 1
                else:
                    self.stats.errors.append(f"Failed to process {mapping.original_filename}")

            except Exception as e:
                error_msg = f"Error processing {mapping.original_filename}: {e}"
                print(f"[ERROR] {error_msg}")
                self.stats.errors.append(error_msg)

        # Generate reports
        self.stats.processing_time = (datetime.now() - start_time).total_seconds()
        self._generate_processing_reports(output_dir)

        return self.stats

    def process_single_image(self, mapping: ImageMapping, fascicolo_dirs: Dict, output_base_dir: str) -> bool:
        """
        Processa una singola immagine attraverso il workflow completo

        Args:
            mapping: Mapping XML per l'immagine
            fascicolo_dirs: Directory structure per fascicoli
            output_base_dir: Directory base di output

        Returns:
            True se success
        """
        try:
            # Get source file path - check subdirectories
            source_file = self._find_source_file(mapping)
            if not source_file:
                print(f"[ERROR] Source file not found: {mapping.original_filename}")
                return False

            # Get target directory
            target_dir = self.iccd_renamer.get_target_directory(mapping, fascicolo_dirs)
            if not target_dir:
                print(f"[ERROR] Could not determine target directory for {mapping.original_filename}")
                return False

            # Create subdirectory structure if needed
            if mapping.subdir:
                target_dir = os.path.join(target_dir, mapping.subdir)
                os.makedirs(target_dir, exist_ok=True)
                print(f"    [INFO] Created subdirectory: {mapping.subdir}")

            # Process with crop.py
            crop_output_file, was_cropped = self._run_crop_processing(source_file)
            if not crop_output_file:
                print(f"[ERROR] Crop processing failed for {mapping.original_filename}")
                return False

            # Analyze crop output
            crop_result = analyze_crop_output(
                crop_output_file,
                was_cropped,
                mapping.original_filename,
                source_file  # Pass original file path for metadata
            )

            # Generate ICCD renamings
            renamings = self.iccd_renamer.handle_page_splitting(mapping, crop_result)

            # Apply ICCD naming convention
            renamed_count = 0
            for source_path, target_filename, original_file_path in renamings:
                success = self.iccd_renamer.apply_naming_convention(
                    source_path,
                    target_filename,
                    target_dir,
                    original_file_path  # Pass original file for metadata preservation
                )
                if success:
                    renamed_count += 1

            # Update statistics
            self.stats.successfully_renamed += renamed_count

            # Report results
            if crop_result.fold_detected:
                print(f"    [OK] fold detected, {renamed_count} files renamed")
            else:
                print(f"    [OK] no fold, {renamed_count} files renamed")

            return True

        except Exception as e:
            print(f"[ERROR] Exception in process_single_image: {e}")
            return False

    def _find_source_file(self, mapping: ImageMapping) -> Optional[str]:
        """
        Trova il file sorgente considerando subdirectory
        """
        base_path = os.path.join(mapping.busta_folder, mapping.original_filename)

        # Try direct path first
        if os.path.exists(base_path):
            return base_path

        # Try with full_path if available
        if mapping.full_path and os.path.exists(mapping.full_path):
            return mapping.full_path

        # Try in subdirectory if specified
        if mapping.subdir:
            subdir_path = os.path.join(mapping.busta_folder, mapping.subdir, mapping.original_filename)
            if os.path.exists(subdir_path):
                return subdir_path

        return None

    def _run_crop_processing(self, source_file: str) -> Tuple[Optional[str], bool]:
        """
        Esegue crop processing su un'immagine

        Returns:
            Tuple (output_file_path, was_cropped)
        """
        try:
            # Create temporary directory for crop output
            temp_dir = tempfile.mkdtemp(prefix="iccd_crop_")

            # Path to crop.py
            crop_script = os.path.join(
                os.path.dirname(__file__),
                '..', '..', 'project2', 'python', 'crop.py'
            )

            if not os.path.exists(crop_script):
                print(f"[ERROR] crop.py not found at: {crop_script}")
                return None, False

            # Build crop command
            cmd = [
                sys.executable, crop_script,
                source_file,
                temp_dir
            ]

            # Execute crop
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[ERROR] Crop failed: {result.stderr}")
                return None, False

            # Find output files in temp directory
            output_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif', '.png')):
                        output_files.append(os.path.join(root, f))

            if not output_files:
                print(f"[ERROR] No output files found after crop processing")
                return None, False

            # Determine if fold was detected (multiple output files or _left/_right suffix)
            was_cropped = len(output_files) > 1 or any('_left' in f or '_right' in f for f in output_files)

            # Return first output file path
            return output_files[0], was_cropped

        except Exception as e:
            print(f"[ERROR] Exception in crop processing: {e}")
            return None, False

    def _generate_processing_reports(self, output_dir: str):
        """Genera report del processing"""
        print(f"\n[PHASE 4] Final Report")
        print("=" * 60)
        print(f"[SUMMARY] ICCD PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total images found: {self.stats.total_images}")
        print(f"Successfully processed: {self.stats.successfully_processed}")
        print(f"Successfully renamed: {self.stats.successfully_renamed}")
        print(f"Errors: {len(self.stats.errors)}")

        if self.stats.total_images > 0:
            success_rate = (self.stats.successfully_processed / self.stats.total_images) * 100
            rename_rate = (self.stats.successfully_renamed / self.stats.total_images) * 100 if self.stats.total_images > 0 else 0
            print(f"Processing success rate: {success_rate:.1f}%")
            print(f"Renaming success rate: {rename_rate:.1f}%")

        print(f"Total processing time: {self.stats.processing_time:.2f} seconds")

        # Save detailed report
        report_file = os.path.join(output_dir, "iccd_processing_report_renaming.json")
        self.iccd_renamer.generate_processing_report(report_file)

        print(f"Reports saved to: {output_dir}/")
        print("=" * 60)

        if len(self.stats.errors) == 0:
            print("[SUCCESS] ICCD processing completed successfully!")
        else:
            print("[WARNING] ICCD processing completed with errors:")
            for error in self.stats.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.stats.errors) > 5:
                print(f"  ... and {len(self.stats.errors) - 5} more errors")