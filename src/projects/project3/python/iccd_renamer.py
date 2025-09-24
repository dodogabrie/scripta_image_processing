#!/usr/bin/env python3
"""
ICCD Renamer Module
Applica le regole di naming ICCD secondo convenzioni definite in desiderata.md
Gestisce logica crop (fold detection) per renaming intelligente delle pagine
"""

import os
from typing import Optional, Tuple, List
from dataclasses import dataclass
from xml_processor import ImageMapping


@dataclass
class CropResult:
    """Risultato del processing crop.py"""
    fold_detected: bool
    left_file: Optional[str] = None
    right_file: Optional[str] = None
    single_file: Optional[str] = None
    processing_logs: str = ""
    original_filename: str = ""


class ICCDRenamer:
    """
    Gestisce la rinomina dei file secondo convenzioni ICCD
    Implementa le regole definite in desiderata.md
    """

    # Mapping tipi documento secondo desiderata.md
    DOCUMENT_TYPES = {
        'S': 'S',  # Scheda (Pagina)
        'A': 'A',  # Allegato (Indice)
        'F': 'F',  # Foto (Carta)
        'P': 'P'   # Disegno (Tavola)
    }

    def __init__(self):
        self.renamed_files = []

    def generate_iccd_filename(self, mapping: ImageMapping, crop_result: CropResult,
                             side: Optional[str] = None) -> str:
        """
        Genera filename ICCD secondo convenzioni desiderata.md

        Args:
            mapping: Mapping XML per l'immagine
            crop_result: Risultato del processing crop
            side: 'left' o 'right' se specificato

        Returns:
            Filename ICCD formattato
        """
        if mapping.has_nct and mapping.nct_code:
            # Schema CON NCT: ICCD_1000000000_01_S0001_01
            return self._generate_nct_filename(mapping, crop_result, side)
        else:
            # Schema SENZA NCT: ICCD_FSC00001-0001_01_S0001_01
            return self._generate_non_nct_filename(mapping, crop_result, side)

    def _generate_nct_filename(self, mapping: ImageMapping, crop_result: CropResult,
                             side: Optional[str] = None) -> str:
        """Genera filename per schema CON NCT"""

        # Formato: ICCD_1200143419_01_S0001_01
        nct_code = mapping.nct_code

        # Numero progressivo (scheda = 01, foto = 02, etc.)
        progressive_num = self._get_progressive_number(mapping.document_type)

        # Tipologia documento
        doc_type = mapping.document_type
        doc_number = mapping.sequence_number

        # Numero pagina con logica crop
        page_number = self._calculate_page_number(mapping.page_number, crop_result, side)

        filename = f"ICCD_{nct_code}_{progressive_num:02d}_{doc_type}{doc_number}_{page_number:02d}.tiff"
        return filename

    def _generate_non_nct_filename(self, mapping: ImageMapping, crop_result: CropResult,
                                 side: Optional[str] = None) -> str:
        """Genera filename per schema SENZA NCT"""

        # Formato: ICCD_FSC00001-0001_01_S0001_01
        fascicolo = f"FSC{int(mapping.fascicolo_number):05d}"
        oggetto = f"{int(mapping.oggetto_number):04d}"

        # Numero progressivo
        progressive_num = self._get_progressive_number(mapping.document_type)

        # Tipologia documento
        doc_type = mapping.document_type
        doc_number = mapping.sequence_number

        # Numero pagina con logica crop
        page_number = self._calculate_page_number(mapping.page_number, crop_result, side)

        filename = f"ICCD_{fascicolo}-{oggetto}_{progressive_num:02d}_{doc_type}{doc_number}_{page_number:02d}.tiff"
        return filename

    def _get_progressive_number(self, document_type: str) -> int:
        """
        Ottieni numero progressivo secondo ordine desiderata.md:
        Schede → Allegati → Foto → Disegni
        """
        type_order = {'S': 1, 'A': 2, 'F': 3, 'P': 4}
        return type_order.get(document_type, 1)

    def _calculate_page_number(self, original_page: int, crop_result: CropResult,
                             side: Optional[str] = None) -> int:
        """
        Calcola numero pagina finale secondo regole desiderata.md

        Regole crop:
        - Pagina 1 + crop → pagina 4 (left), pagina 1 (right)
        - Pagina 2 + crop → pagina 2 (left), pagina 3 (right)
        - No crop → mantieni numerazione originale
        """
        if not crop_result.fold_detected or side is None:
            # No crop o no side specified
            return original_page

        # Applica regole split secondo desiderata.md
        if original_page == 1:
            return 4 if side == 'left' else 1
        elif original_page == 2:
            return 2 if side == 'left' else 3
        else:
            # Per pagine > 2, mantieni logica sequenziale
            # Pagina N → (N*2, N*2+1)
            return (original_page * 2) if side == 'left' else (original_page * 2 + 1)

    def handle_page_splitting(self, mapping: ImageMapping, crop_result: CropResult) -> List[Tuple[str, str]]:
        """
        Gestisce split delle pagine quando fold è rilevato

        Returns:
            Lista di tuple (source_file, target_filename)
        """
        renamings = []

        if crop_result.fold_detected:
            # Fold rilevato - genera nomi per left e right
            if crop_result.left_file:
                left_name = self.generate_iccd_filename(mapping, crop_result, 'left')
                renamings.append((crop_result.left_file, left_name))

            if crop_result.right_file:
                right_name = self.generate_iccd_filename(mapping, crop_result, 'right')
                renamings.append((crop_result.right_file, right_name))
        else:
            # No fold - rinomina file singolo
            if crop_result.single_file:
                single_name = self.generate_iccd_filename(mapping, crop_result)
                renamings.append((crop_result.single_file, single_name))

        return renamings

    def apply_naming_convention(self, source_file: str, target_filename: str,
                              output_dir: str) -> bool:
        """
        Applica effettivamente la rinomina del file

        Args:
            source_file: File sorgente
            target_filename: Nome target ICCD
            output_dir: Directory di output

        Returns:
            True se rinomina riuscita
        """
        try:
            # Assicurati che output directory esista
            os.makedirs(output_dir, exist_ok=True)

            # Path completo target
            target_path = os.path.join(output_dir, target_filename)

            # Verifica che source file esista
            if not os.path.exists(source_file):
                print(f"❌ Source file not found: {source_file}")
                return False

            # Controlla conflitti naming
            if os.path.exists(target_path):
                print(f"⚠️  Target file already exists: {target_path}")
                # Genera nome alternativo
                target_path = self._generate_unique_filename(target_path)
                target_filename = os.path.basename(target_path)

            # Copia/sposta file
            import shutil
            shutil.copy2(source_file, target_path)

            print(f"✅ Renamed: {os.path.basename(source_file)} → {target_filename}")

            # Traccia rinomina
            self.renamed_files.append({
                'source': source_file,
                'target': target_path,
                'target_filename': target_filename
            })

            return True

        except Exception as e:
            print(f"❌ Error renaming {source_file}: {e}")
            return False

    def _generate_unique_filename(self, filepath: str) -> str:
        """Genera filename unico in caso di conflitti"""
        base, ext = os.path.splitext(filepath)
        counter = 1

        while os.path.exists(f"{base}_{counter:02d}{ext}"):
            counter += 1

        return f"{base}_{counter:02d}{ext}"

    def create_iccd_directory_structure(self, output_base_dir: str,
                                      mappings: List[ImageMapping]) -> dict:
        """
        Crea struttura directory ICCD organizzata per fascicolo

        Returns:
            Dizionario mapping fascicolo → directory path
        """
        fascicolo_dirs = {}

        for mapping in mappings:
            if mapping.has_nct and mapping.nct_code:
                # Schema CON NCT
                dir_name = f"ICCD_{mapping.nct_code}"
            else:
                # Schema SENZA NCT
                fascicolo = f"FSC{int(mapping.fascicolo_number):05d}"
                dir_name = f"ICCD_{fascicolo}"

            dir_path = os.path.join(output_base_dir, dir_name)

            if dir_name not in fascicolo_dirs:
                os.makedirs(dir_path, exist_ok=True)
                fascicolo_dirs[dir_name] = dir_path
                print(f"📁 Created directory: {dir_name}")

        return fascicolo_dirs

    def get_target_directory(self, mapping: ImageMapping, fascicolo_dirs: dict) -> str:
        """Ottieni directory target per un mapping specifico"""
        if mapping.has_nct and mapping.nct_code:
            dir_name = f"ICCD_{mapping.nct_code}"
        else:
            fascicolo = f"FSC{int(mapping.fascicolo_number):05d}"
            dir_name = f"ICCD_{fascicolo}"

        return fascicolo_dirs.get(dir_name, "")

    def validate_iccd_filename(self, filename: str) -> bool:
        """Valida che un filename rispetti le convenzioni ICCD"""
        import re

        # Pattern per schema SENZA NCT
        pattern_no_nct = r'ICCD_FSC\d{5}-\d{4}_\d{2}_[SAFP]\d{4}_\d{2}\.tiff'

        # Pattern per schema CON NCT
        pattern_nct = r'ICCD_\d{10}_\d{2}_[SF]\d{4}_\d{2}\.tiff'

        return bool(re.match(pattern_no_nct, filename) or re.match(pattern_nct, filename))

    def generate_processing_report(self, output_file: str):
        """Genera report delle rinominazioni effettuate"""
        import json
        from datetime import datetime

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_renamed': len(self.renamed_files),
            'files': self.renamed_files
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Processing report saved: {output_file}")


def analyze_crop_output(output_dir: str, processing_logs: str, original_filename: str) -> CropResult:
    """
    Analizza output del crop.py per determinare se fold è stato rilevato

    Args:
        output_dir: Directory dove crop.py ha salvato i file
        processing_logs: Log output del crop.py
        original_filename: Nome file originale

    Returns:
        CropResult con informazioni sui file generati
    """
    base_name = os.path.splitext(original_filename)[0]

    # Controlla se esistono file _left e _right (fold rilevato)
    left_pattern = os.path.join(output_dir, f"{base_name}_left.*")
    right_pattern = os.path.join(output_dir, f"{base_name}_right.*")

    import glob
    left_files = glob.glob(left_pattern)
    right_files = glob.glob(right_pattern)

    if left_files and right_files:
        # Fold rilevato
        return CropResult(
            fold_detected=True,
            left_file=left_files[0],
            right_file=right_files[0],
            processing_logs=processing_logs,
            original_filename=original_filename
        )
    else:
        # No fold - cerca file singolo processato
        single_pattern = os.path.join(output_dir, f"{base_name}.*")
        single_files = [f for f in glob.glob(single_pattern)
                       if not f.endswith('_left.jpg') and not f.endswith('_right.jpg')]

        single_file = single_files[0] if single_files else None

        return CropResult(
            fold_detected=False,
            single_file=single_file,
            processing_logs=processing_logs,
            original_filename=original_filename
        )


if __name__ == "__main__":
    # Test del modulo
    import sys

    # Test validazione filename
    renamer = ICCDRenamer()

    test_filenames = [
        "ICCD_FSC01351-0001_01_S0001_01.tiff",
        "ICCD_1200143419_01_S0001_01.tiff",
        "invalid_filename.jpg"
    ]

    for filename in test_filenames:
        is_valid = renamer.validate_iccd_filename(filename)
        print(f"{'✅' if is_valid else '❌'} {filename}: {is_valid}")