#!/usr/bin/env python3
"""
Busta Detector Utility
Riconosce se una directory contiene struttura Busta_XX con file XML
Utilizzato dal main.py per decidere quale workflow utilizzare
"""

import os
import glob
import re
from typing import List, Tuple, Optional


class BustaDetector:
    """
    Utility per rilevare struttura Busta ICCD nell'input directory
    """

    @staticmethod
    def has_busta_structure(input_dir: str) -> bool:
        """
        Verifica se l'input directory contiene struttura Busta

        Args:
            input_dir: Directory da analizzare

        Returns:
            True se contiene struttura Busta valida
        """
        if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
            return False

        # Cerca file XML Busta
        xml_pattern = os.path.join(input_dir, "Busta_*.xml")
        xml_files = glob.glob(xml_pattern)

        if not xml_files:
            return False

        # Verifica che per ogni XML esista cartella corrispondente
        valid_pairs = 0

        for xml_file in xml_files:
            xml_basename = os.path.basename(xml_file)
            busta_name = xml_basename.replace('.xml', '')
            busta_folder = os.path.join(input_dir, busta_name)

            if os.path.isdir(busta_folder):
                # Verifica che la cartella contenga immagini
                if BustaDetector._has_images(busta_folder):
                    valid_pairs += 1

        # Considera valida se almeno una coppia Busta+XML è trovata
        return valid_pairs > 0

    @staticmethod
    def _has_images(folder_path: str) -> bool:
        """Verifica se una cartella contiene file immagine"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif']

        for ext in image_extensions:
            pattern = os.path.join(folder_path, ext)
            if glob.glob(pattern):
                return True

            # Case insensitive
            pattern_upper = os.path.join(folder_path, ext.upper())
            if glob.glob(pattern_upper):
                return True

        return False

    @staticmethod
    def discover_busta_pairs(input_dir: str) -> List[Tuple[str, str]]:
        """
        Scopre tutte le coppie valide Busta+XML

        Args:
            input_dir: Directory da scansionare

        Returns:
            Lista di tuple (busta_folder_path, xml_file_path)
        """
        pairs = []

        xml_pattern = os.path.join(input_dir, "Busta_*.xml")
        xml_files = glob.glob(xml_pattern)

        for xml_file in xml_files:
            xml_basename = os.path.basename(xml_file)
            busta_name = xml_basename.replace('.xml', '')
            busta_folder = os.path.join(input_dir, busta_name)

            if os.path.isdir(busta_folder) and BustaDetector._has_images(busta_folder):
                pairs.append((busta_folder, xml_file))

        return pairs

    @staticmethod
    def get_busta_info(input_dir: str) -> dict:
        """
        Ottieni informazioni dettagliate sulle Buste trovate

        Returns:
            Dizionario con statistiche Buste
        """
        pairs = BustaDetector.discover_busta_pairs(input_dir)

        info = {
            'has_busta_structure': len(pairs) > 0,
            'total_bustas': len(pairs),
            'busta_details': []
        }

        for busta_folder, xml_file in pairs:
            # Conta immagini nella cartella
            image_count = len(BustaDetector._get_image_files(busta_folder))

            # Estrai numero busta
            busta_name = os.path.basename(busta_folder)
            busta_match = re.search(r'Busta_(\d+)', busta_name)
            busta_number = busta_match.group(1) if busta_match else "unknown"

            detail = {
                'busta_name': busta_name,
                'busta_number': busta_number,
                'busta_folder': busta_folder,
                'xml_file': xml_file,
                'image_count': image_count
            }

            info['busta_details'].append(detail)

        return info

    @staticmethod
    def _get_image_files(folder_path: str) -> List[str]:
        """Ottieni lista completa file immagine in una cartella"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif']
        image_files = []

        for ext in image_extensions:
            pattern = os.path.join(folder_path, ext)
            image_files.extend(glob.glob(pattern))

            # Case insensitive
            pattern_upper = os.path.join(folder_path, ext.upper())
            image_files.extend(glob.glob(pattern_upper))

        return image_files

    @staticmethod
    def validate_busta_structure(input_dir: str, verbose: bool = False) -> bool:
        """
        Valida completamente la struttura Busta

        Args:
            input_dir: Directory da validare
            verbose: Stampa dettagli validazione

        Returns:
            True se struttura è completamente valida
        """
        if verbose:
            print(f"🔍 Validating Busta structure in: {input_dir}")

        if not BustaDetector.has_busta_structure(input_dir):
            if verbose:
                print("❌ No valid Busta structure found")
            return False

        info = BustaDetector.get_busta_info(input_dir)

        if verbose:
            print(f"📁 Found {info['total_bustas']} valid Bustas:")

            for detail in info['busta_details']:
                print(f"   • {detail['busta_name']}: {detail['image_count']} images")

        # Controlla che ogni XML sia ben formato (parsing base)
        all_valid = True

        for detail in info['busta_details']:
            xml_file = detail['xml_file']

            try:
                from lxml import etree
                etree.parse(xml_file)

                if verbose:
                    print(f"✅ {os.path.basename(xml_file)}: valid XML")

            except Exception as e:
                if verbose:
                    print(f"❌ {os.path.basename(xml_file)}: invalid XML - {e}")
                all_valid = False

        return all_valid

    @staticmethod
    def print_busta_summary(input_dir: str):
        """Stampa summary dettagliato delle Buste trovate"""
        print("\n" + "="*50)
        print("📋 BUSTA DETECTION SUMMARY")
        print("="*50)

        if not BustaDetector.has_busta_structure(input_dir):
            print("❌ No Busta structure detected in input directory")
            print("Expected structure:")
            print("   input_dir/")
            print("   ├── Busta_XX/")
            print("   │   ├── image1.jpg")
            print("   │   └── image2.jpg")
            print("   └── Busta_XX.xml")
            return

        info = BustaDetector.get_busta_info(input_dir)

        print(f"✅ Busta structure detected!")
        print(f"📁 Total Bustas: {info['total_bustas']}")

        total_images = sum(detail['image_count'] for detail in info['busta_details'])
        print(f"🖼️  Total images: {total_images}")

        print("\n📋 Busta Details:")
        for detail in info['busta_details']:
            print(f"   • {detail['busta_name']}")
            print(f"     └── Images: {detail['image_count']}")
            print(f"     └── XML: {os.path.basename(detail['xml_file'])}")

        print("="*50 + "\n")


if __name__ == "__main__":
    # Test utility
    import sys

    if len(sys.argv) < 2:
        print("Usage: python busta_detector.py <input_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]

    # Test detection
    detector = BustaDetector()

    # Summary
    detector.print_busta_summary(input_dir)

    # Validation dettagliata
    print("🔍 Running detailed validation...")
    is_valid = detector.validate_busta_structure(input_dir, verbose=True)

    if is_valid:
        print("\n✅ All Bustas are valid and ready for processing!")
    else:
        print("\n⚠️  Some Bustas have issues. Check XML files and image folders.")

    sys.exit(0 if is_valid else 1)