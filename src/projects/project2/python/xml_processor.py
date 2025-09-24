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
    # New fields for subdirectory support
    full_path: str = ""  # Full path to source file
    subdir: str = None   # Subdirectory name (tiff, jpeg300, etc.)


class XMLProcessorError(Exception):
    """Eccezione per errori di processing XML"""
    pass


class XMLProcessor:
    """Parser per file XML delle Buste ICCD"""

    def __init__(self):
        self.mappings: List[ImageMapping] = []

    def discover_busta_files(self, input_dir: str) -> List[tuple]:
        """
        Scopre tutte le coppie Folder + Folder.xml nell'input directory

        Returns:
            List di tuple (folder_path, xml_file_path)
        """
        folder_pairs = []

        # Pattern per trovare TUTTI i file XML
        xml_pattern = os.path.join(input_dir, "*.xml")
        xml_files = glob.glob(xml_pattern)

        for xml_file in xml_files:
            # Estrai nome base dal filename XML
            xml_basename = os.path.basename(xml_file)
            folder_name = xml_basename.replace('.xml', '')

            # Cerca cartella corrispondente con stesso nome
            folder_path = os.path.join(input_dir, folder_name)

            if os.path.isdir(folder_path):
                folder_pairs.append((folder_path, xml_file))
            else:
                print(f"⚠️  Warning: Found {xml_file} but no corresponding folder {folder_path}")

        print(f"📁 Discovered {len(folder_pairs)} folder-XML pairs")
        return folder_pairs

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
        # Handle both string tags and lxml element tags
        tag_name = element.tag if isinstance(element.tag, str) else str(element.tag)

        elem_data = {
            'tag': tag_name,
            'text': element.text.strip() if element.text else '',
            'attributes': dict(element.attrib),
            'children': []
        }

        for child in element:
            self._parse_elements_recursive(child, elem_data['children'])

        elements_list.append(elem_data)

    def extract_image_mappings(self, xml_data: Dict, folder_path: str,
                             process_jpg: bool = True, process_tiff: bool = True) -> List[ImageMapping]:
        """
        Estrae mappings filename → metadati ICCD dalla struttura XML parsata

        Args:
            xml_data: Dati XML parsati
            folder_path: Path alla cartella con immagini
            process_jpg: Se processare file .jpg/.jpeg
            process_tiff: Se processare file .tiff/.tif

        Returns:
            Lista di ImageMapping objects
        """
        mappings = []

        try:
            # Parse directly from the XML file using lxml
            xml_file = xml_data['xml_file']
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(xml_file, parser)
            root = tree.getroot()

            # Define namespace map
            ns = {'mag': 'http://www.iccu.sbn.it/metaAG1.pdf',
                  'xlink': 'http://www.w3.org/1999/xlink'}

            # Step 1: Parse fascicoli from <stru> elements
            fascicoli = self._parse_fascicoli_direct(root, ns)
            print(f"📋 Found {len(fascicoli)} fascicoli in XML")

            # Step 2: Parse images from <img> elements
            xml_image_mappings = self._parse_images_direct(root, ns)
            print(f"🖼️  Found {len(xml_image_mappings)} image mappings in XML")

            # Step 3: Get actual files in folder
            actual_files = self._get_image_files(folder_path, process_jpg, process_tiff)
            print(f"📁 Found {len(actual_files)} actual files in folder")

            # Step 4: Create progressive mappings by fascicolo and document type
            mappings = self._create_progressive_mappings(actual_files, xml_image_mappings, fascicoli, folder_path)

        except Exception as e:
            print(f"❌ Error in direct XML parsing: {e}")

        return mappings

    def _get_image_files(self, folder_path: str, process_jpg: bool = True, process_tiff: bool = True) -> List[Dict]:
        """
        Ottieni lista file immagine dalla cartella Busta e sottocartelle standard.

        Args:
            folder_path: Path alla cartella Busta
            process_jpg: Se processare .jpg/.jpeg
            process_tiff: Se processare .tiff/.tif

        Returns:
            Lista di dict con 'filename', 'full_path', 'subdir'
        """
        image_extensions = []
        if process_jpg:
            image_extensions.extend(['*.jpg', '*.jpeg'])
        if process_tiff:
            image_extensions.extend(['*.tiff', '*.tif'])
        # Always include PNG
        image_extensions.append('*.png')

        # Standard subdirectories to scan (case insensitive)
        standard_subdirs = ['tif', 'tiff', 'jpeg300', 'jpeg150']

        image_files = []

        # Search in main directory
        for ext in image_extensions:
            pattern = os.path.join(folder_path, ext)
            found_files = glob.glob(pattern) + glob.glob(pattern.upper())
            for file_path in found_files:
                image_files.append({
                    'filename': os.path.basename(file_path),
                    'full_path': file_path,
                    'subdir': None  # Main directory
                })

        # Search in standard subdirectories
        for subdir_name in standard_subdirs:
            # Case insensitive search for subdirectory
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if (os.path.isdir(item_path) and
                    item.lower() == subdir_name.lower()):

                    print(f"   📁 Scanning subdirectory: {item}")

                    # Search for images in this subdirectory
                    for ext in image_extensions:
                        pattern = os.path.join(item_path, ext)
                        found_files = glob.glob(pattern) + glob.glob(pattern.upper())
                        for file_path in found_files:
                            image_files.append({
                                'filename': os.path.basename(file_path),
                                'full_path': file_path,
                                'subdir': item  # Actual subdirectory name (preserves case)
                            })
                    break  # Found matching subdirectory

        print(f"   📁 Scanning {folder_path} for images (JPG: {process_jpg}, TIFF: {process_tiff})")

        # Group by subdirectory for reporting
        by_subdir = {}
        for file_info in image_files:
            subdir = file_info['subdir'] or 'main'
            if subdir not in by_subdir:
                by_subdir[subdir] = []
            by_subdir[subdir].append(file_info['filename'])

        for subdir, files in by_subdir.items():
            print(f"   📁 {subdir}: {len(files)} files - {files[:3]}{'...' if len(files) > 3 else ''}")

        return image_files

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

    def _parse_fascicoli_from_xml(self, xml_data: Dict) -> List[Dict]:
        """Estrae informazioni sui fascicoli dalle strutture <stru> dell'XML"""
        fascicoli = []

        def find_fascicoli_recursive(elements):
            for elem in elements:
                if elem['tag'].endswith('stru'):
                    # Parse stru element
                    fascicolo_info = self._parse_single_stru_element(elem)
                    if fascicolo_info:
                        fascicoli.append(fascicolo_info)

                # Ricorsione sui figli
                find_fascicoli_recursive(elem['children'])

        find_fascicoli_recursive(xml_data['elements'])
        return fascicoli

    def _parse_single_stru_element(self, stru_elem: Dict) -> Optional[Dict]:
        """Parse un singolo elemento <stru>"""
        try:
            fascicolo_info = {
                'sequence_number': None,
                'number': None,
                'start_sequence': None,
                'stop_sequence': None
            }

            for child in stru_elem['children']:
                if child['tag'].endswith('sequence_number'):
                    fascicolo_info['sequence_number'] = int(child['text'])

                elif child['tag'].endswith('element'):
                    # Parse element for piece info and start/stop
                    for element_child in child['children']:
                        if element_child['tag'].endswith('piece'):
                            # Extract fascicolo number from issue
                            for piece_child in element_child['children']:
                                if piece_child['tag'].endswith('issue'):
                                    # Extract number from "fasc. 1351"
                                    issue_text = piece_child['text']
                                    match = re.search(r'fasc\.\s*(\d+)', issue_text)
                                    if match:
                                        fascicolo_info['number'] = int(match.group(1))

                        elif element_child['tag'].endswith('start'):
                            seq_num = element_child['attributes'].get('sequence_number')
                            if seq_num:
                                fascicolo_info['start_sequence'] = int(seq_num)

                        elif element_child['tag'].endswith('stop'):
                            seq_num = element_child['attributes'].get('sequence_number')
                            if seq_num:
                                fascicolo_info['stop_sequence'] = int(seq_num)

            # Validate that we have required info
            if all(fascicolo_info[key] is not None for key in ['number', 'start_sequence', 'stop_sequence']):
                return fascicolo_info

        except Exception as e:
            print(f"Error parsing stru element: {e}")

        return None

    def _parse_images_from_xml(self, xml_data: Dict) -> List[Dict]:
        """Estrae mappings immagini dagli elementi <img> dell'XML"""
        image_mappings = []

        def find_images_recursive(elements):
            for elem in elements:
                if elem['tag'].endswith('img'):
                    # Parse img element
                    img_info = self._parse_single_img_element(elem)
                    if img_info:
                        image_mappings.append(img_info)

                # Ricorsione sui figli
                find_images_recursive(elem['children'])

        find_images_recursive(xml_data['elements'])
        return image_mappings

    def _parse_single_img_element(self, img_elem: Dict) -> Optional[Dict]:
        """Parse un singolo elemento <img>"""
        try:
            img_info = {
                'sequence_number': None,
                'nomenclature': None,
                'page_number': None,
                'filename': None
            }

            for child in img_elem['children']:
                if child['tag'].endswith('sequence_number'):
                    img_info['sequence_number'] = int(child['text'])

                elif child['tag'].endswith('nomenclature'):
                    nomenclature = child['text']
                    img_info['nomenclature'] = nomenclature

                    # Extract page number from "Pagina: 2"
                    page_match = re.search(r'Pagina:\s*(\d+)', nomenclature)
                    if page_match:
                        img_info['page_number'] = int(page_match.group(1))

                elif child['tag'].endswith('file') or child['tag'].endswith('altimg'):
                    # Look for file references
                    filename = self._extract_filename_from_element(child)
                    if filename and filename.endswith(('.jpg', '.jpeg')):
                        # Prefer jpeg versions which are likely in our folder
                        img_info['filename'] = os.path.basename(filename)

            # Validate that we have required info
            if all(img_info[key] is not None for key in ['sequence_number', 'page_number']):
                return img_info

        except Exception as e:
            print(f"Error parsing img element: {e}")

        return None

    def _extract_filename_from_element(self, element: Dict) -> Optional[str]:
        """Extract filename from file or altimg element"""
        # Check direct href attribute
        href = element['attributes'].get('href') or element['attributes'].get('{http://www.w3.org/1999/xlink}href')
        if href:
            return href

        # Check children for file elements
        for child in element['children']:
            if child['tag'].endswith('file'):
                href = child['attributes'].get('href') or child['attributes'].get('{http://www.w3.org/1999/xlink}href')
                if href:
                    return href

        return None

    def _find_xml_mapping_for_file(self, filename: str, xml_mappings: List[Dict]) -> Optional[Dict]:
        """Find XML mapping for a given filename - EXACT MATCH ONLY"""
        for mapping in xml_mappings:
            xml_filename = mapping.get('filename')
            if xml_filename and xml_filename == filename:
                print(f"   ✅ Exact match: {filename} ↔ {xml_filename} (seq {mapping.get('sequence_number')})")
                return mapping

        # Debug: show what we were trying to match
        print(f"   ❌ No exact match for {filename}")
        return None

    def _find_fascicolo_for_sequence(self, sequence_number: int, fascicoli: List[Dict]) -> Optional[Dict]:
        """Find which fascicolo contains a given sequence number"""
        for fascicolo in fascicoli:
            if fascicolo['start_sequence'] <= sequence_number <= fascicolo['stop_sequence']:
                return fascicolo
        return None

    def _parse_fascicoli_direct(self, root, ns: Dict) -> List[Dict]:
        """Parse fascicoli directly from lxml root using XPath"""
        fascicoli = []

        try:
            # Find all stru elements
            stru_elements = root.xpath('.//mag:stru', namespaces=ns)

            for stru in stru_elements:
                fascicolo_info = {
                    'sequence_number': None,
                    'number': None,
                    'start_sequence': None,
                    'stop_sequence': None
                }

                # Get sequence number
                seq_elem = stru.xpath('./mag:sequence_number', namespaces=ns)
                if seq_elem:
                    fascicolo_info['sequence_number'] = int(seq_elem[0].text)

                # Get fascicolo number from issue element
                issue_elem = stru.xpath('.//mag:issue', namespaces=ns)
                if issue_elem:
                    issue_text = issue_elem[0].text
                    match = re.search(r'fasc\.\s*(\d+)', issue_text)
                    if match:
                        fascicolo_info['number'] = int(match.group(1))

                # Get start sequence
                start_elem = stru.xpath('.//mag:start', namespaces=ns)
                if start_elem:
                    seq_attr = start_elem[0].get('sequence_number')
                    if seq_attr:
                        fascicolo_info['start_sequence'] = int(seq_attr)

                # Get stop sequence
                stop_elem = stru.xpath('.//mag:stop', namespaces=ns)
                if stop_elem:
                    seq_attr = stop_elem[0].get('sequence_number')
                    if seq_attr:
                        fascicolo_info['stop_sequence'] = int(seq_attr)

                # Validate and add
                if all(fascicolo_info[key] is not None for key in ['number', 'start_sequence', 'stop_sequence']):
                    fascicoli.append(fascicolo_info)

        except Exception as e:
            print(f"Error parsing fascicoli: {e}")

        return fascicoli

    def _parse_images_direct(self, root, ns: Dict) -> List[Dict]:
        """Parse image mappings directly from lxml root using XPath"""
        image_mappings = []

        try:
            # Find all img elements
            img_elements = root.xpath('.//mag:img', namespaces=ns)

            for img in img_elements:
                img_info = {
                    'sequence_number': None,
                    'nomenclature': None,
                    'page_number': None,
                    'filename': None
                }

                # Get sequence number
                seq_elem = img.xpath('./mag:sequence_number', namespaces=ns)
                if seq_elem:
                    img_info['sequence_number'] = int(seq_elem[0].text)

                # Get nomenclature
                nom_elem = img.xpath('./mag:nomenclature', namespaces=ns)
                if nom_elem:
                    nomenclature = nom_elem[0].text
                    img_info['nomenclature'] = nomenclature

                    # Extract page number and document type from nomenclature
                    # Patterns: "Pagina: 2", "Indice: 1", "Carta: 3", "Tavola: 1"
                    page_match = re.search(r'(Pagina|Indice|Carta|Tavola):\s*(\d+)', nomenclature)
                    if page_match:
                        doc_prefix = page_match.group(1)
                        img_info['page_number'] = int(page_match.group(2))

                        # Map nomenclature to ICCD document type
                        doc_type_mapping = {
                            'Pagina': 'S',  # Scheda
                            'Indice': 'A',  # Allegato
                            'Carta': 'F',   # Foto
                            'Tavola': 'P'   # Disegno
                        }
                        img_info['document_type'] = doc_type_mapping.get(doc_prefix, 'S')

                # Collect all files for this img element (both main file and altimg)
                files_to_add = []

                # Get main file (usually .tif)
                main_file = img.xpath('./mag:file[@xlink:href]', namespaces=ns)
                if main_file:
                    href = main_file[0].get('{http://www.w3.org/1999/xlink}href')
                    if href:
                        files_to_add.append(os.path.basename(href))

                # Get altimg file (usually .jpg)
                altimg_file = img.xpath('.//mag:altimg//mag:file[@xlink:href]', namespaces=ns)
                if altimg_file:
                    href = altimg_file[0].get('{http://www.w3.org/1999/xlink}href')
                    if href:
                        files_to_add.append(os.path.basename(href))

                # Create separate entries for each file found
                for filename in files_to_add:
                    file_info = img_info.copy()  # Copy base info
                    file_info['filename'] = filename

                    # Validate and add
                    if all(file_info[key] is not None for key in ['sequence_number', 'page_number', 'document_type']):
                        image_mappings.append(file_info)
                        print(f"   📁 Added {filename} → seq {file_info['sequence_number']}")

        except Exception as e:
            print(f"Error parsing images: {e}")

        return image_mappings

    def _group_by_document_instances(self, files_of_type: List[Dict]) -> List[List[Dict]]:
        """
        Group files by document instances, detecting when page sequences reset.

        For example:
        - [Pagina:1, Pagina:2, Pagina:1, Pagina:2] → [[Pagina:1, Pagina:2], [Pagina:1, Pagina:2]]
        - [Pagina:1, Pagina:2, Pagina:3] → [[Pagina:1, Pagina:2, Pagina:3]]

        Args:
            files_of_type: List of file data sorted by page number

        Returns:
            List of document instances, each containing a list of files
        """
        if not files_of_type:
            return []

        document_instances = []
        current_instance = []
        last_page_number = 0

        for file_data in files_of_type:
            current_page = file_data['page_number']

            # If current page number is less than or equal to last page number,
            # and we already have files in current instance, start a new instance
            if current_page <= last_page_number and current_instance:
                # Special case: if current page is 1 and we have accumulated pages
                # this likely indicates start of new document instance
                if current_page == 1:
                    document_instances.append(current_instance)
                    current_instance = [file_data]
                else:
                    # Continue current instance for non-page-1 resets
                    current_instance.append(file_data)
            else:
                current_instance.append(file_data)

            last_page_number = current_page

        # Add the last instance if not empty
        if current_instance:
            document_instances.append(current_instance)

        print(f"   📋 Grouped {len(files_of_type)} files into {len(document_instances)} document instances")
        for i, instance in enumerate(document_instances, 1):
            pages = [f['page_number'] for f in instance]
            print(f"      Instance {i}: pages {pages}")

        return document_instances

    def _create_progressive_mappings(self, actual_files: List[str], xml_image_mappings: List[Dict],
                                   fascicoli: List[Dict], folder_path: str) -> List[ImageMapping]:
        """Create ICCD mappings with progressive numbering by document type"""
        mappings = []

        # Step 1: Match files to XML and group by fascicolo and document type
        file_groups = {}  # {fascicolo_number: {doc_type: [file_data, ...]}}

        for file_info in actual_files:
            filename = file_info['filename'] if isinstance(file_info, dict) else file_info
            # Find matching XML entry
            xml_mapping = self._find_xml_mapping_for_file(filename, xml_image_mappings)

            if xml_mapping:
                # Find fascicolo for this sequence_number
                fascicolo = self._find_fascicolo_for_sequence(xml_mapping['sequence_number'], fascicoli)

                if fascicolo:
                    fascicolo_num = str(fascicolo['number'])
                    doc_type = xml_mapping['document_type']

                    # Initialize nested dict structure
                    if fascicolo_num not in file_groups:
                        file_groups[fascicolo_num] = {}
                    if doc_type not in file_groups[fascicolo_num]:
                        file_groups[fascicolo_num][doc_type] = []

                    # Add file data
                    file_data = {
                        'filename': filename,
                        'page_number': xml_mapping['page_number'],
                        'nomenclature': xml_mapping['nomenclature'],
                        'xml_sequence': xml_mapping['sequence_number'],
                        'full_path': file_info.get('full_path', filename) if isinstance(file_info, dict) else filename,
                        'subdir': file_info.get('subdir') if isinstance(file_info, dict) else None
                    }
                    file_groups[fascicolo_num][doc_type].append(file_data)

                    subdir_info = f" ({file_info.get('subdir', 'main')})" if isinstance(file_info, dict) and file_info.get('subdir') else ""
                    print(f"✅ Grouped {filename}{subdir_info} → fascicolo {fascicolo_num} (seq {xml_mapping['sequence_number']}), type {doc_type}, page {xml_mapping['page_number']}")
                else:
                    print(f"⚠️  No fascicolo found for {filename} (sequence {xml_mapping['sequence_number']})")
                    print(f"      Available fascicolo ranges:")
                    for fasc in fascicoli[:3]:  # Show first 3 fascicoli
                        print(f"      - Fascicolo {fasc['number']}: seq {fasc['start_sequence']}-{fasc['stop_sequence']}")
                    print(f"      ... (showing first 3 of {len(fascicoli)} total)")
            else:
                print(f"⚠️  No XML mapping found for {filename}")

        # Step 2: Create progressive mappings by fascicolo, then by object, then by document type
        for fascicolo_num, doc_types in file_groups.items():
            print(f"📋 Processing fascicolo {fascicolo_num}")

            # First, we need to determine object boundaries by looking at Pagina sequences
            # Every time Pagina sequence resets to 1, it's a new object
            all_files = []
            for doc_type, files in doc_types.items():
                for file_data in files:
                    file_data['doc_type'] = doc_type
                    all_files.append(file_data)

            # Sort all files by XML sequence number to maintain original order
            all_files.sort(key=lambda x: x.get('xml_sequence', 0))

            # Group files by physical objects (reset when Pagina:1 appears)
            objects = []
            current_object = []

            for file_data in all_files:
                # If this is Pagina:1 and we already have files, start new object
                if (file_data['doc_type'] == 'S' and file_data['page_number'] == 1 and
                    current_object and any(f['doc_type'] == 'S' for f in current_object)):
                    objects.append(current_object)
                    current_object = [file_data]
                else:
                    current_object.append(file_data)

            # Add the last object
            if current_object:
                objects.append(current_object)

            print(f"   📦 Found {len(objects)} objects in fascicolo {fascicolo_num}")

            # Process each object
            for obj_num, object_files in enumerate(objects, 1):
                print(f"   📦 Processing object {obj_num}")

                # Group files by document type within this object
                object_doc_types = {}
                for file_data in object_files:
                    doc_type = file_data['doc_type']
                    if doc_type not in object_doc_types:
                        object_doc_types[doc_type] = []
                    object_doc_types[doc_type].append(file_data)

                # Sort document types by ICCD order: S(01) → A(02) → F(03) → P(04)
                type_order = {'S': 1, 'A': 2, 'F': 3, 'P': 4}
                sorted_doc_types = sorted(object_doc_types.keys(), key=lambda x: type_order.get(x, 5))

                # Process each document type within this object
                for doc_type in sorted_doc_types:
                    files_of_type = object_doc_types[doc_type]

                    # Sort files by page number within each type
                    files_of_type.sort(key=lambda x: x['page_number'])

                    # Group by document instance - detect when page sequences reset within same type
                    document_instances = self._group_by_document_instances(files_of_type)

                    progressive_num = type_order[doc_type]

                    for doc_instance_num, instance_files in enumerate(document_instances, 1):
                        for file_data in instance_files:
                            mapping = ImageMapping(
                                original_filename=file_data['filename'],
                                fascicolo_number=fascicolo_num,
                                oggetto_number=f"{obj_num:04d}",  # Object number within fascicolo
                                document_type=doc_type,
                                sequence_number=f"{doc_instance_num:04d}",  # Progressive within doc type
                                page_number=file_data['page_number'],  # Original page from XML
                                busta_folder=folder_path,
                                full_path=file_data.get('full_path', file_data['filename']),
                                subdir=file_data.get('subdir')
                            )

                            mappings.append(mapping)
                            print(f"      📝 {file_data['filename']} → Object:{obj_num:04d} {doc_type}{doc_instance_num:04d}_{file_data['page_number']:02d}")

        return mappings

    def process_all_bustas(self, input_dir: str, process_jpg: bool = True, process_tiff: bool = True) -> List[ImageMapping]:
        """
        Processa tutte le Buste nell'input directory

        Args:
            input_dir: Directory contenente le Buste
            process_jpg: Se processare file .jpg/.jpeg
            process_tiff: Se processare file .tiff/.tif

        Returns:
            Lista completa di tutti i mappings estratti
        """
        all_mappings = []

        # Scopri tutte le coppie Folder-XML
        folder_pairs = self.discover_busta_files(input_dir)

        for folder_path, xml_file in folder_pairs:
            print(f"📄 Processing {os.path.basename(xml_file)}...")

            try:
                # Parsa XML
                xml_data = self.parse_busta_xml(xml_file)

                # Estrai mappings
                mappings = self.extract_image_mappings(xml_data, folder_path, process_jpg, process_tiff)

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


def has_busta_structure(input_dir: str) -> bool:
    """Verifica se l'input directory contiene struttura Folder+XML"""
    if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
        return False

    # Cerca TUTTI i file XML
    xml_pattern = os.path.join(input_dir, "*.xml")
    xml_files = glob.glob(xml_pattern)

    if not xml_files:
        return False

    # Verifica che per ogni XML esista cartella corrispondente con immagini
    for xml_file in xml_files:
        xml_basename = os.path.basename(xml_file)
        folder_name = xml_basename.replace('.xml', '')
        folder_path = os.path.join(input_dir, folder_name)

        if os.path.isdir(folder_path):
            # Verifica che la cartella contenga immagini
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif']
            has_images = False

            for ext in image_extensions:
                pattern = os.path.join(folder_path, ext)
                if glob.glob(pattern) or glob.glob(pattern.upper()):
                    has_images = True
                    break

            if has_images:
                return True

    return False


if __name__ == "__main__":
    # Test del modulo
    import sys

    if len(sys.argv) < 2:
        print("Usage: python xml_processor.py <input_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    processor = XMLProcessor()
    mappings = processor.process_all_bustas(input_dir)

    for mapping in mappings:
        print(f"{mapping.original_filename} → {mapping.fascicolo_number} {mapping.document_type}")