#!/usr/bin/env python3
"""
XML Processor per parsing file Busta_XX.xml
Estrae mappings filename → metadati ICCD secondo convenzioni desiderata.md
"""

import os
import glob
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass
from lxml import etree
import re


@dataclass
class ImageMapping:
    """Struttura dati per mapping immagine → metadati ICCD"""
    original_filename: str
    fascicolo_number: str
    oggetto_number: str
    document_type: str  # S/A/F/P
    sequence_number: str
    page_number: int
    busta_folder: str
    has_nct: bool = False
    nct_code: str = ""


class XMLProcessorError(Exception):
    """Eccezione per errori di processing XML"""
    pass


class XMLProcessor:
    """Parser per file XML delle Buste ICCD"""

    def __init__(self):
        self.mappings: List[ImageMapping] = []

    def discover_busta_files(self, input_dir: str) -> List[tuple]:
        """
        Scopre tutte le coppie Busta_XX + Busta_XX.xml nell'input directory

        Returns:
            List di tuple (busta_folder_path, xml_file_path)
        """
        busta_pairs = []

        # Pattern per trovare file XML Busta
        xml_pattern = os.path.join(input_dir, "Busta_*.xml")
        xml_files = glob.glob(xml_pattern)

        for xml_file in xml_files:
            # Estrai numero busta dal filename XML
            xml_basename = os.path.basename(xml_file)
            busta_name = xml_basename.replace('.xml', '')

            # Cerca cartella corrispondente
            busta_folder = os.path.join(input_dir, busta_name)

            if os.path.isdir(busta_folder):
                busta_pairs.append((busta_folder, xml_file))
            else:
                print(f"⚠️  Warning: Found {xml_file} but no corresponding folder {busta_folder}")

        print(f"📁 Discovered {len(busta_pairs)} Busta pairs")
        return busta_pairs

    def parse_busta_xml(self, xml_file_path: str) -> Dict:
        """
        Parsa un singolo file Busta_XX.xml

        Args:
            xml_file_path: Path al file XML da parsare

        Returns:
            Dizionario con metadati estratti
        """
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(xml_file_path, parser)
            root = tree.getroot()

            # Estrai informazioni base dalla struttura XML
            xml_data = {
                'xml_file': xml_file_path,
                'root_tag': root.tag,
                'namespaces': root.nsmap,
                'elements': []
            }

            # Parsing ricorsivo degli elementi
            self._parse_elements_recursive(root, xml_data['elements'])

            return xml_data

        except etree.XMLSyntaxError as e:
            raise XMLProcessorError(f"Errore parsing XML {xml_file_path}: {e}")
        except Exception as e:
            raise XMLProcessorError(f"Errore generico parsing {xml_file_path}: {e}")

    def _parse_elements_recursive(self, element, elements_list):
        """Parsing ricorsivo degli elementi XML"""
        elem_data = {
            'tag': element.tag,
            'text': element.text.strip() if element.text else '',
            'attributes': dict(element.attrib),
            'children': []
        }

        for child in element:
            self._parse_elements_recursive(child, elem_data['children'])

        elements_list.append(elem_data)

    def extract_image_mappings(self, xml_data: Dict, busta_folder: str) -> List[ImageMapping]:
        """
        Estrae mappings filename → metadati ICCD dalla struttura XML parsata

        Args:
            xml_data: Dati XML parsati
            busta_folder: Path alla cartella Busta corrispondente

        Returns:
            Lista di ImageMapping objects
        """
        mappings = []
        busta_name = os.path.basename(busta_folder)

        # Estrai numero fascicolo dal nome busta
        fascicolo_match = re.search(r'Busta_(\d+)', busta_name)
        if not fascicolo_match:
            raise XMLProcessorError(f"Impossibile estrarre numero fascicolo da {busta_name}")

        fascicolo_number = fascicolo_match.group(1)

        # Scansiona immagini nella cartella per creare mappings di base
        image_files = self._get_image_files(busta_folder)

        for i, image_file in enumerate(sorted(image_files)):
            # Estrai informazioni base dal filename
            base_name = os.path.splitext(image_file)[0]

            # Determina tipo documento e sequenza dal filename o dalla posizione
            document_type, sequence_num = self._infer_document_info(base_name, i)

            mapping = ImageMapping(
                original_filename=image_file,
                fascicolo_number=fascicolo_number,
                oggetto_number="0001",  # Default, può essere sovrascritto da XML
                document_type=document_type,
                sequence_number=sequence_num,
                page_number=i + 1,  # Default sequential numbering
                busta_folder=busta_folder
            )

            mappings.append(mapping)

        # Tenta di arricchire mappings con informazioni XML specifiche
        self._enrich_mappings_from_xml(mappings, xml_data)

        return mappings

    def _get_image_files(self, busta_folder: str) -> List[str]:
        """Ottieni lista file immagine dalla cartella Busta"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif']
        image_files = []

        for ext in image_extensions:
            pattern = os.path.join(busta_folder, ext)
            image_files.extend(glob.glob(pattern))
            # Case insensitive
            pattern_upper = os.path.join(busta_folder, ext.upper())
            image_files.extend(glob.glob(pattern_upper))

        # Ritorna solo i nomi file, non i path completi
        return [os.path.basename(f) for f in image_files]

    def _infer_document_info(self, base_name: str, index: int) -> tuple:
        """
        Inferisce tipo documento e numero sequenza dal filename

        Returns:
            (document_type, sequence_number)
        """
        # Logica base di inferenza - può essere migliorata con pattern specifici

        # Se il filename contiene pattern specifici
        if 'foto' in base_name.lower() or 'f_' in base_name.lower():
            return 'F', f"{index+1:04d}"
        elif 'disegno' in base_name.lower() or 'p_' in base_name.lower():
            return 'P', f"{index+1:04d}"
        elif 'allegato' in base_name.lower() or 'a_' in base_name.lower():
            return 'A', f"{index+1:04d}"
        else:
            # Default: scheda
            return 'S', f"{index+1:04d}"

    def _enrich_mappings_from_xml(self, mappings: List[ImageMapping], xml_data: Dict):
        """
        Arricchisce i mappings con informazioni specifiche dall'XML
        Questa funzione può essere estesa per parsing XML specifici
        """
        # Cerca informazioni NCT nell'XML
        nct_codes = self._extract_nct_codes(xml_data)

        # Se trovati codici NCT, aggiorna i mappings
        if nct_codes:
            for mapping in mappings:
                mapping.has_nct = True
                # Assegna NCT in base alla posizione o logica specifica
                if len(nct_codes) == 1:
                    mapping.nct_code = nct_codes[0]
                elif len(nct_codes) > len(mappings):
                    # Più NCT che immagini - usa il primo
                    mapping.nct_code = nct_codes[0]
                else:
                    # Distribuzione sequenziale
                    idx = min(mappings.index(mapping), len(nct_codes) - 1)
                    mapping.nct_code = nct_codes[idx]

    def _extract_nct_codes(self, xml_data: Dict) -> List[str]:
        """Estrae codici NCT dalla struttura XML"""
        nct_codes = []

        def search_nct_recursive(elements):
            for elem in elements:
                # Cerca pattern NCT nel testo
                if elem['text'] and re.match(r'\d{10}', elem['text']):
                    nct_codes.append(elem['text'])

                # Cerca negli attributi
                for attr_value in elem['attributes'].values():
                    if re.match(r'\d{10}', str(attr_value)):
                        nct_codes.append(str(attr_value))

                # Ricorsione sui figli
                search_nct_recursive(elem['children'])

        search_nct_recursive(xml_data['elements'])
        return list(set(nct_codes))  # Rimuovi duplicati

    def validate_xml_structure(self, xml_file: str) -> bool:
        """
        Valida la struttura del file XML

        Returns:
            True se la struttura è valida
        """
        try:
            tree = etree.parse(xml_file)
            root = tree.getroot()

            # Validazioni base
            if root is None:
                return False

            # Controlla che ci siano elementi
            if len(list(root)) == 0:
                print(f"⚠️  Warning: XML {xml_file} appears to be empty")
                return False

            return True

        except Exception as e:
            print(f"❌ XML validation failed for {xml_file}: {e}")
            return False

    def process_all_bustas(self, input_dir: str) -> List[ImageMapping]:
        """
        Processa tutte le Buste nell'input directory

        Returns:
            Lista completa di tutti i mappings estratti
        """
        all_mappings = []

        # Scopri tutte le coppie Busta
        busta_pairs = self.discover_busta_files(input_dir)

        for busta_folder, xml_file in busta_pairs:
            print(f"📄 Processing {os.path.basename(xml_file)}...")

            try:
                # Valida XML
                if not self.validate_xml_structure(xml_file):
                    print(f"❌ Skipping invalid XML: {xml_file}")
                    continue

                # Parsa XML
                xml_data = self.parse_busta_xml(xml_file)

                # Estrai mappings
                mappings = self.extract_image_mappings(xml_data, busta_folder)

                print(f"✅ Extracted {len(mappings)} image mappings from {os.path.basename(xml_file)}")

                all_mappings.extend(mappings)

            except XMLProcessorError as e:
                print(f"❌ Error processing {xml_file}: {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error processing {xml_file}: {e}")
                continue

        self.mappings = all_mappings
        print(f"🎯 Total mappings extracted: {len(all_mappings)}")

        return all_mappings

    def get_mapping_by_filename(self, filename: str) -> Optional[ImageMapping]:
        """Trova mapping per filename specifico"""
        for mapping in self.mappings:
            if mapping.original_filename == filename:
                return mapping
        return None

    def export_mappings_csv(self, output_file: str):
        """Esporta mappings in formato CSV per debug"""
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'original_filename', 'fascicolo_number', 'oggetto_number',
                'document_type', 'sequence_number', 'page_number',
                'busta_folder', 'has_nct', 'nct_code'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for mapping in self.mappings:
                writer.writerow({
                    'original_filename': mapping.original_filename,
                    'fascicolo_number': mapping.fascicolo_number,
                    'oggetto_number': mapping.oggetto_number,
                    'document_type': mapping.document_type,
                    'sequence_number': mapping.sequence_number,
                    'page_number': mapping.page_number,
                    'busta_folder': mapping.busta_folder,
                    'has_nct': mapping.has_nct,
                    'nct_code': mapping.nct_code
                })


if __name__ == "__main__":
    # Test del modulo
    import sys

    if len(sys.argv) < 2:
        print("Usage: python xml_processor.py <input_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    processor = XMLProcessor()
    mappings = processor.process_all_bustas(input_dir)

    # Esporta CSV per debug
    if mappings:
        csv_output = os.path.join(input_dir, "extracted_mappings.csv")
        processor.export_mappings_csv(csv_output)
        print(f"📊 Mappings exported to: {csv_output}")