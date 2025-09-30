#!/usr/bin/env python

import glob
import json
import logging
import os
import re
import shutil
from os.path import basename, join, normpath, splitext

from maglib.script.common import (
    MagOperation,
    MagOperationError,
    MagScriptMain,
    MagScriptOptionParser,
)

log = logging.getLogger(__name__)

# Dizionario delle abbreviazioni per le nomenclature
ABBREVIAZIONI_NOMENCLATURE = {
    "Scheda": "S",
    "Foto": "F",
    "Allegato": "A",
    "Disegno": "D",
    "Pagina": "S",  # NCT mapping
    "Carta": "F",  # NCT mapping
    "Indice": "A",  # NCT mapping
    "Tavola": "P",  # NCT mapping (Planimetria/Disegno)
}

# Progressive numbering by document type (ICCD order)
PROGRESSIVE_ORDER = {
    "S": 1,  # Schede
    "A": 2,  # Allegati
    "F": 3,  # Foto
    "P": 4,  # Planimetrie/Disegni
}

CROP_MAP = {"_crop_1": 1, "_crop_2": 2, "_crop_3": 3, "_crop_4": 4}


class OptionParser(MagScriptOptionParser):
    def __init__(self):
        MagScriptOptionParser.__init__(self)
        self.remove_option("-c")
        self.add_option(
            "-d",
            "--base-dst-dir",
            action="store",
            help="directory base dove copiare i file",
        )
        self.add_option(
            "-s",
            "--base-src-dir",
            action="store",
            help="directory base da cui copiare i file",
        )
        self.add_option(
            "-n",
            "--dry-run",
            action="store_true",
            help="non effettuare nessun spostamento, stampa",
        )
        self.add_option(
            "-C", "--copy", action="store_true", help="copia invece di spostare"
        )
        self.add_option(
            "-b",
            "--basename",
            action="store",
            help="Nome base da usare per la directory delle risorse e i file",
        )
        self.add_option(
            "--ignore-missing",
            action="store_true",
            default=False,
            help="Ignora i file mancanti durante lo spostamento o la copia",
        )
        self.add_option(
            "--json-analysis",
            action="store_true",
            default=False,
            help="Analizza solo il file XML e genera un JSON con la mappatura fascicolo->file",
        )
        self.add_option(
            "--auto-discover",
            action="store_true",
            default=False,
            help="Scopri automaticamente tutti i file XML nella directory sorgente",
        )


class AdaptFs(MagOperation):
    def __init__(
        self,
        base_src_dir,
        base_dst_dir,
        bname=None,
        dry_run=False,
        copy=True,
        ignore_missing=False,
        json_analysis=False,
        xml_input_path=None,
    ):
        self._bname = bname
        self._base_dst_dir = base_dst_dir
        self._base_src_dir = base_src_dir
        self._dry_run = dry_run
        self._copy = copy
        self._ignore_missing = ignore_missing
        self._json_analysis = json_analysis
        self._xml_input_path = xml_input_path

        # ICCD-specific counters and tracking
        self._fascicoli_sequence = {}
        self._fascicolo_number = None
        self._current_object_number = None
        self._document_type_counters = {}  # Counts S, A, F, P within object groups
        self._page_counters = {}  # Page numbers within documents

        if self._json_analysis:
            self._transporter = JsonAnalysisTransporter(self._base_src_dir)
        elif self._dry_run:
            self._transporter = DummyTransporter()
        elif self._copy:
            log.warning("!!!!!!Copying files")
            self._transporter = CopyTransporter(self._ignore_missing)
        else:
            self._transporter = MoveTransporter(self._ignore_missing)

    def do_op(self, metadigit):
        bname = self._bname or self._guess_bname(metadigit)
        if not bname:
            raise MagOperationError(
                "Serve un identificatore per adattare il filesystem."
            )

        # Extract fascicolo number from structure
        self._fascicolo_number = self._extract_fascicolo_from_stru(metadigit)
        if not self._fascicolo_number:
            raise MagOperationError("Cannot extract fascicolo number from structure")

        info_json_path = os.path.join(self._base_src_dir, "info.json")
        if os.path.exists(info_json_path):
            with open(info_json_path, "r") as f:
                info = json.load(f)
                self._cropped_files = info.get("cropped")
        else:
            self._cropped_files = None

        # Extract object number from stru sequence_number
        self._current_object_number = None
        for stru_elem in metadigit.stru:
            fascicolo_number_str = stru_elem.element[0].piece[0].issue[0].value
            fascicolo_number = int(fascicolo_number_str.strip().split("fasc.")[1])
            sequence = int(stru_elem.sequence_number[0].value)

            start_seq = int(stru_elem.element[0].start[0].sequence_number.value)
            stop_seq = int(stru_elem.element[0].stop[0].sequence_number.value)

            self._fascicoli_sequence[fascicolo_number] = {
                "sequence": sequence,
                "start": start_seq,
                "stop": stop_seq,
            }

        prev_fascicolo = None
        # Process all images
        for img_node in metadigit.img:
            try:
                nomenclature = img_node.nomenclature[0].value
                nomenclature_short = self._get_nomenclature_short(nomenclature)
                page_number = self._extract_page_number(nomenclature)
                sequence_number = int(img_node.sequence_number[0].value)
                fascicolo = self.find_fascicolo_from_sequence_number(sequence_number)

                self._fascicolo_number = fascicolo

                if fascicolo != prev_fascicolo:
                    self._document_type_counters = {
                        "S": 0,
                        "A": 0,
                        "F": 0,
                        "P": 0,
                    }

                # When we encounter a new S document, update the reference object number
                if page_number == 1:
                    prev_s_number = self._document_type_counters[nomenclature_short]
                    if nomenclature_short == "S":  # reset counters for other types
                        self._document_type_counters = {
                            "S": prev_s_number + 1,
                            "A": 0,
                            "F": 0,
                            "P": 0,
                        }
                    else:  # Increase counters for other types
                        self._document_type_counters[nomenclature_short] += 1

                schede_sequence = self._document_type_counters["S"]
                attachment_sequence = self._document_type_counters[nomenclature_short]

                # Progressive number (S=01, A=02, F=03, P=04)
                progressive_number = self._get_progressive_number(nomenclature_short)

                for img in [img_node] + list(img_node.altimg):
                    self._do_iccd_file_element(
                        schede_sequence,
                        progressive_number,
                        nomenclature_short,
                        attachment_sequence,
                        page_number,
                        img.file[0],
                    )

                prev_fascicolo = fascicolo

            except Exception as e:
                log.warning(f"Error processing image: {e}")
            # log.warning(f"COUNTERS: {self._document_type_counters}")

        # Save JSON analysis if requested
        if self._json_analysis:
            self._save_json_analysis()

    def _do_iccd_file_element(
        self,
        object_number,
        progressive_number,
        nomenclature_short,
        doc_sequence,
        page_number,
        file_el,
    ):
        origpath = file_el.href.value
        filename = basename(origpath)
        files_to_process = 1
        if self._cropped_files:
            if filename in self._cropped_files:
                files_to_process = len(self._cropped_files[filename])

        # Check if this file has cropped versions
        if files_to_process > 1 and self._cropped_files:
            cropped_list = self._cropped_files[filename]

            # Collect crop page numbers for validation
            crop_page_numbers = []
            for cropped_filename in cropped_list:
                crop_page_number = self._extract_crop_page_number(cropped_filename)
                crop_page_numbers.append(crop_page_number)

            # Validate page alignment between XML and crop pages
            self._validate_page_alignment(
                page_number,  # XML page number from nomenclature
                crop_page_numbers,  # Crop page numbers from filenames
                filename,  # Original filename
                cropped_list,  # List of cropped filenames
            )

            # Process each cropped file separately
            for i, cropped_filename in enumerate(cropped_list):
                # Use the already extracted crop page number
                crop_page_number = crop_page_numbers[i]

                # Set extension and subfolder for cropped files
                extension = "tiff"  # cropped files are typically tiff
                subfolder = "tiff"

                # Build path for this specific cropped file
                newpath = self._build_iccd_path(
                    object_number,
                    progressive_number,
                    nomenclature_short,
                    doc_sequence,
                    crop_page_number,  # Use crop-specific page number
                    subfolder,
                    extension,
                )

                # Update XML element only for first cropped file (or handle differently)
                if i == 0 and not self._json_analysis:
                    file_el.href.value = newpath

                # Build source path for cropped file - now uses full relative path from info.json
                clean_origpath = cropped_filename.lstrip("./")
                src = normpath(join(self._base_src_dir, clean_origpath))

                dst = normpath(join(self._base_dst_dir, newpath))

                # Transport this cropped file
                if self._json_analysis:
                    self._transporter.transport_with_paths(
                        cropped_filename, newpath, src, dst
                    )
                else:
                    self._transporter.transport(src, dst)
        else:
            # Original single file processing
            extension = origpath.split(".")[-1].lower()
            subfolder = (
                "tiff"
                if "tiff" in origpath
                else "jpeg300"
                if "jpeg300" in origpath
                else ""
            )

            newpath = self._build_iccd_path(
                object_number,
                progressive_number,
                nomenclature_short,
                doc_sequence,
                page_number,
                subfolder,
                extension,
            )

            # Only update the XML element if not in JSON analysis mode
            if not self._json_analysis:
                file_el.href.value = newpath

            # Clean up relative path prefix for proper joining
            clean_origpath = origpath.lstrip("./")
            src = normpath(join(self._base_src_dir, clean_origpath))
            dst = normpath(join(self._base_dst_dir, newpath))

            # Pass original and target paths to transporter
            if self._json_analysis:
                self._transporter.transport_with_paths(origpath, newpath, src, dst)
            else:
                self._transporter.transport(src, dst)

    def _do_file_element(
        self,
        bname,
        scheda_number,
        category_number,
        sub_index,
        nomenclature_short,
        file_el,
    ):
        origpath = file_el.href.value
        extension = origpath.split(".")[-1].lower()
        subfolder = (
            "tiff" if "tiff" in origpath else "jpeg300" if "jpeg300" in origpath else ""
        )

        newpath = self._build_new_path(
            scheda_number,
            category_number,
            sub_index,
            bname,
            nomenclature_short,
            subfolder,
            extension,
        )
        file_el.href.value = newpath
        # Clean up relative path prefix for proper joining
        clean_origpath = origpath.lstrip("./")
        src = normpath(join(self._base_src_dir, clean_origpath))
        dst = normpath(join(self._base_dst_dir, newpath))
        self._transporter.transport(src, dst)

    def _build_new_path(
        self,
        scheda_number,
        category_number,
        sub_index,
        bname,
        nomenclature_short,
        subfolder,
        extension,
    ):
        new_dir = f"{bname}/{subfolder}"
        new_filename = self._build_new_filename(
            scheda_number,
            category_number,
            sub_index,
            bname,
            nomenclature_short,
            extension,
        )
        return f"{new_dir}/{new_filename}"

    def _build_new_filename(
        self,
        scheda_number,
        category_number,
        sub_index,
        bname,
        nomenclature_short,
        extension,
    ):
        return f"{bname}-{scheda_number:04d}_{nomenclature_short}{category_number:04d}_{sub_index:02d}.{extension}"

    def _build_iccd_path(
        self,
        object_number,
        progressive_number,
        nomenclature_short,
        doc_sequence,
        page_number,
        subfolder,
        extension,
    ):
        # Generate ICCD directory: ICCD_FSC01351 (NCT) or ICCD_1200143419 (NCT)
        if self._is_nct_fascicolo():
            iccd_dir = f"ICCD_{self._fascicolo_number}/{subfolder}"
        else:
            iccd_dir = f"ICCD_FSC{self._fascicolo_number:05d}/{subfolder}"

        # Generate ICCD filename: ICCD_FSC01351-0019_01_S0001_01.tiff (NCT) or ICCD_1200143419_01_S0001_01.tiff (NCT)
        iccd_filename = self._build_iccd_filename(
            object_number,
            progressive_number,
            nomenclature_short,
            doc_sequence,
            page_number,
            extension,
        )

        return f"{iccd_dir}/{iccd_filename}"

    def _build_iccd_filename(
        self,
        object_number,
        progressive_number,
        nomenclature_short,
        doc_sequence,
        page_number,
        extension,
    ):
        progressive_part = f"{progressive_number:02d}"
        doc_part = f"{nomenclature_short}{doc_sequence:04d}"
        page_part = f"{page_number:02d}"

        if self._is_nct_fascicolo():
            # NCT format: ICCD_{fascicolo}_{progressive}_{doc}_{page}.ext
            return f"ICCD_{self._fascicolo_number}_{progressive_part}_{doc_part}_{page_part}.{extension}"
        else:
            # Non NCT format: ICCD_FSC{fascicolo:05d}-{object:04d}_{progressive}_{doc}_{page}.ext
            fascicolo_part = f"FSC{self._fascicolo_number:05d}"
            object_part = f"{object_number:04d}"
            return f"ICCD_{fascicolo_part}-{object_part}_{progressive_part}_{doc_part}_{page_part}.{extension}"

    def _extract_fascicolo_from_stru(self, metadigit):
        """Extract fascicolo number from stru element"""
        for stru_elem in metadigit.stru:
            if hasattr(stru_elem, "element") and stru_elem.element:
                for element in stru_elem.element:
                    if hasattr(element, "piece") and element.piece:
                        for piece in element.piece:
                            if hasattr(piece, "issue") and piece.issue:
                                for issue in piece.issue:
                                    # Extract from "fasc. 1351" format
                                    issue_text = issue.value
                                    match = re.search(r"fasc\.\s*(\d+)", issue_text)
                                    if match:
                                        return int(match.group(1))
        return None

    def find_fascicolo_from_sequence_number(self, sequence_number):
        """Extract fascicolo number given a sequence number"""
        int_sequence_number = int(sequence_number)
        for k, fascicolo in self._fascicoli_sequence.items():
            if fascicolo["start"] <= int_sequence_number <= fascicolo["stop"]:
                return k
        return None

    def _extract_page_number(self, nomenclature):
        """Extract page number from nomenclature like 'Pagina: 1' or 'Carta: 2'"""
        match = re.search(r":\s*(\d+)", nomenclature)
        if match:
            return int(match.group(1))
        return 1

    def _get_progressive_number(self, document_type):
        """Get progressive number for document type (S=01, A=02, F=03, P=04)"""
        return PROGRESSIVE_ORDER.get(document_type, 1)

    def _extract_crop_page_number(self, filename):
        """Extract page number from crop filename using CROP_MAP"""
        for suffix, page_num in CROP_MAP.items():
            if suffix in filename:
                return page_num
        return 1  # default

    def _validate_page_alignment(
        self, xml_page_number, crop_page_numbers, original_filename, cropped_filenames
    ):
        """
        Validate alignment between XML page number and generated crop page numbers.

        Args:
            xml_page_number (int): Page number from XML nomenclature (e.g., from "Pagina: 1")
            crop_page_numbers (list): List of crop page numbers from generated files
            original_filename (str): Original filename for error reporting
            cropped_filenames (list): List of cropped filenames for error reporting

        Returns:
            None (prints warnings/errors directly)
        """
        if xml_page_number >= 3:
            # ERROR: Pagina 3 or higher should never generate crops
            for i, cropped_name in enumerate(cropped_filenames):
                crop_page = crop_page_numbers[i]
                print(
                    f"[ERROR] ERRORE: Pagina {xml_page_number} (>2) ha generato file ritagliato - non supportato {original_filename}->{cropped_name}"
                )
                log.error(
                    f"Page {xml_page_number} generated crop file {cropped_name} - not supported"
                )
            return

        # Sort crop page numbers for consistent comparison
        sorted_crop_pages = sorted(set(crop_page_numbers))

        # Define expected page alignments
        expected_pages = {
            1: [1, 4],  # Pagina: 1 should generate crop pages 1 and 4
            2: [2, 3],  # Pagina: 2 should generate crop pages 2 and 3
        }

        # Check alignment
        if xml_page_number in expected_pages:
            expected_crop_pages = expected_pages[xml_page_number]

            if sorted_crop_pages == sorted(expected_crop_pages):
                # Correct alignment - no warning needed
                return
            else:
                # Misalignment detected - generate warning
                crop_pages_str = ", ".join(map(str, sorted_crop_pages))
                cropped_names_str = ", ".join(cropped_filenames)

                print(
                    f"[WARNING] Possibile disallineamento tra immagini ritagliate e nomenclatura xml: Pagina {xml_page_number} ha generato file {crop_pages_str} {original_filename}->{cropped_names_str}"
                )
                log.warning(
                    f"Page alignment mismatch: XML page {xml_page_number} generated crop pages {crop_pages_str} (expected {expected_crop_pages})"
                )
        else:
            # Unexpected page number - log warning
            crop_pages_str = ", ".join(map(str, sorted_crop_pages))
            cropped_names_str = ", ".join(cropped_filenames)
            print(
                f"[WARNING] Pagina {xml_page_number} non prevista ha generato file {crop_pages_str} {original_filename}->{cropped_names_str}"
            )
            log.warning(
                f"Unexpected XML page number {xml_page_number} generated crop pages {crop_pages_str}"
            )

    def _is_nct_fascicolo(self):
        """Detect if fascicolo is NCT format (long number ≥ 9 digits)"""
        return len(str(self._fascicolo_number)) >= 9

    def clean_mag(self, metadigit):
        raise NotImplementedError()

    @property
    def write_mag(self):
        return not self._dry_run

    def _guess_bname(self, metadigit):
        if metadigit.bib and metadigit.bib[0].identifier:
            return metadigit.bib[0].identifier[0].value
        return None

    def _get_nomenclature_short(self, nomenclature):
        for key in ABBREVIAZIONI_NOMENCLATURE:
            if key in nomenclature:
                return ABBREVIAZIONI_NOMENCLATURE[key]
        return "X"

    def _save_json_analysis(self):
        """Save the JSON analysis mapping to the destination folder"""
        if isinstance(self._transporter, JsonAnalysisTransporter):
            mapping = self._transporter.get_mapping()

            # Generate unique filename based on XML input
            if self._xml_input_path:
                xml_basename = os.path.splitext(os.path.basename(self._xml_input_path))[
                    0
                ]
                json_filename = f"iccd_mapping_analysis_{xml_basename}.json"
            else:
                json_filename = "iccd_mapping_analysis.json"

            json_path = os.path.join(self._base_dst_dir, json_filename)

            # Ensure destination directory exists
            os.makedirs(self._base_dst_dir, exist_ok=True)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)

            print(f"JSON analysis saved to: {json_path}")
            log.info(f"JSON analysis saved to: {json_path}")


class FileTransporter(object):
    def transport(self, old_file, new_file):
        raise NotImplementedError()

    def _prepare_dir(self, filepath):
        dir_ = os.path.dirname(filepath)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)


class DummyTransporter(FileTransporter):
    def transport(self, old_path, new_path):
        print(f"{normpath(old_path)} -> {normpath(new_path)}")


class CopyTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.warning(f"Ignorando file mancante: {old_path}")
            return
        shutil.copy2(old_path, new_path)


class MoveTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing

    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            log.warning(f"Ignorando file mancante: {old_path}")
            return
        shutil.move(old_path, new_path)


class JsonAnalysisTransporter(FileTransporter):
    def __init__(self, base_src_dir):
        self.mapping = {}
        self.base_src_dir = base_src_dir

    def transport(self, old_path, new_path):
        # This method is kept for compatibility with other transporters
        # but shouldn't be used in JSON analysis mode
        pass

    def transport_with_paths(
        self, original_path, target_path, full_source_path, full_target_path
    ):
        """Transport method for JSON analysis with original and target paths"""
        # Extract fascicolo from target_path (e.g., "ICCD_FSC01351/tiff/...")
        path_parts = target_path.split("/")
        fascicolo_dir = path_parts[0]  # ICCD_FSC01351
        subfolder = path_parts[1] if len(path_parts) > 1 else ""  # tiff/jpeg300
        filename = (
            path_parts[-1] if len(path_parts) > 2 else path_parts[1]
        )  # actual filename

        if fascicolo_dir not in self.mapping:
            self.mapping[fascicolo_dir] = {}

        if subfolder not in self.mapping[fascicolo_dir]:
            self.mapping[fascicolo_dir][subfolder] = {}

        # Check if the source file exists using the original path
        file_exists = os.path.isfile(full_source_path)

        if not file_exists:
            log.warning(f"Immagine non trovata: {original_path}")
            print(f"[WARNING] Immagine non trovata: {original_path}")

        self.mapping[fascicolo_dir][subfolder][filename] = {
            "original_path": original_path,
            "target_path": target_path,
            "image_found": file_exists,
        }

    def get_mapping(self):
        return self.mapping


def discover_xml_files(directory):
    """Discover all XML files in the given directory"""
    xml_pattern = os.path.join(directory, "*.xml")
    xml_files = glob.glob(xml_pattern)
    return sorted(xml_files)


class AutoDiscoveryOperation(MagOperation):
    """Special operation for auto-discovering and processing multiple XML files"""

    def __init__(
        self, src_dir, dst_dir, basename, dry_run, copy, ignore_missing, json_analysis
    ):
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.basename = basename
        self.dry_run = dry_run
        self.copy = copy
        self.ignore_missing = ignore_missing
        self.json_analysis = json_analysis

    def do_op(self, metadigit):
        """This method is called by the framework but we override it for auto-discovery"""
        xml_files = discover_xml_files(self.src_dir)

        if not xml_files:
            raise MagOperationError(f"No XML files found in directory: {self.src_dir}")

        print(f"Found {len(xml_files)} XML files to process:")
        for xml_file in xml_files:
            print(f"  - {basename(xml_file)}")

        # Process each XML file
        success_count = 0
        for i, xml_file in enumerate(xml_files, 1):
            print(f"\n[{i}/{len(xml_files)}] Processing: {basename(xml_file)}")

            try:
                bname = self.basename or splitext(basename(xml_file))[0]
                adapter = AdaptFs(
                    self.src_dir,
                    self.dst_dir,
                    bname,
                    self.dry_run,
                    self.copy,
                    self.ignore_missing,
                    self.json_analysis,
                    xml_file,
                )

                # Load and process this XML file
                from maglib import Metadigit

                metadigit = Metadigit(xml_file)
                adapter.do_op(metadigit)

                print(f"[OK] Successfully processed {basename(xml_file)}")
                success_count += 1

            except Exception as e:
                print(f"[ERROR] Failed to process {basename(xml_file)}: {e}")
                log.error(f"Error processing {xml_file}: {e}")

        print(f"\nProcessed {success_count}/{len(xml_files)} files successfully")

    def clean_mag(self, metadigit):
        return False

    @property
    def write_mag(self):
        return not self.dry_run


class Main(MagScriptMain):
    def _build_opt_parser(self):
        return OptionParser()

    def _build_mag_operation(self, options, args):
        src_dir = options.base_src_dir or os.getcwd()
        dst_dir = options.base_dst_dir or os.getcwd()

        # Handle auto-discovery mode
        if options.auto_discover:
            return AutoDiscoveryOperation(
                src_dir,
                dst_dir,
                options.basename,
                options.dry_run,
                options.copy,
                options.ignore_missing,
                options.json_analysis,
            )

        # Original single-file mode
        if not options.input:
            raise MagOperationError(
                "Either provide an XML input file or use --auto-discover"
            )

        bname = options.basename or splitext(basename(options.input))[0]
        return AdaptFs(
            src_dir,
            dst_dir,
            bname,
            options.dry_run,
            options.copy,
            options.ignore_missing,
            options.json_analysis,
            options.input,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys

    main = Main()
    sys.exit(main(sys.argv))
