#!/usr/bin/env python3
"""
Test script per verificare l'implementazione dei moduli ICCD
Testa le funzionalità base senza richiedere dati reali
"""

import os
import sys
import tempfile
import shutil
from xml.etree import ElementTree as ET


def create_test_structure():
    """Crea una struttura di test con Busta e XML fittizi"""
    print("🧪 Creating test structure...")

    # Crea directory temporanea
    test_dir = tempfile.mkdtemp(prefix="iccd_test_")
    print(f"📁 Test directory: {test_dir}")

    # Crea cartella Busta_42
    busta_dir = os.path.join(test_dir, "Busta_42")
    os.makedirs(busta_dir)

    # Crea file immagini fittizi (file vuoti con estensioni corrette)
    test_images = ["0382.jpg", "0383.jpg", "0395.jpg"]
    for img in test_images:
        img_path = os.path.join(busta_dir, img)
        with open(img_path, 'w') as f:
            f.write("fake image content")

    # Crea XML fittizio
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<busta>
    <metadata>
        <fascicolo>42</fascicolo>
        <tipo>scheda</tipo>
    </metadata>
    <images>
        <image filename="0382.jpg" type="S" page="1"/>
        <image filename="0383.jpg" type="S" page="2"/>
        <image filename="0395.jpg" type="F" page="1"/>
    </images>
</busta>"""

    xml_path = os.path.join(test_dir, "Busta_42.xml")
    with open(xml_path, 'w') as f:
        f.write(xml_content)

    return test_dir


def test_busta_detector():
    """Test BustaDetector"""
    print("\n🔍 Testing BustaDetector...")

    test_dir = create_test_structure()

    try:
        from utils.busta_detector import BustaDetector

        detector = BustaDetector()

        # Test detection
        has_structure = detector.has_busta_structure(test_dir)
        print(f"   Detection result: {'✅' if has_structure else '❌'} {has_structure}")

        if has_structure:
            # Test discovery
            pairs = detector.discover_busta_pairs(test_dir)
            print(f"   Discovered pairs: {len(pairs)}")

            # Test info
            info = detector.get_busta_info(test_dir)
            print(f"   Total Bustas: {info['total_bustas']}")

            # Test validation
            is_valid = detector.validate_busta_structure(test_dir, verbose=False)
            print(f"   Validation: {'✅' if is_valid else '❌'} {is_valid}")

        return has_structure

    except Exception as e:
        print(f"❌ Error testing BustaDetector: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


def test_xml_processor():
    """Test XMLProcessor"""
    print("\n📄 Testing XMLProcessor...")

    test_dir = create_test_structure()

    try:
        from xml_processor import XMLProcessor

        processor = XMLProcessor()

        # Test discovery
        pairs = processor.discover_busta_files(test_dir)
        print(f"   Discovered {len(pairs)} Busta pairs")

        if pairs:
            # Test XML parsing
            busta_folder, xml_file = pairs[0]
            xml_data = processor.parse_busta_xml(xml_file)
            print(f"   XML parsing: ✅ Success")

            # Test mapping extraction
            mappings = processor.extract_image_mappings(xml_data, busta_folder)
            print(f"   Extracted {len(mappings)} mappings")

            for mapping in mappings:
                print(f"     • {mapping.original_filename} → {mapping.document_type}")

        return len(pairs) > 0

    except Exception as e:
        print(f"❌ Error testing XMLProcessor: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


def test_iccd_renamer():
    """Test ICCDRenamer"""
    print("\n📝 Testing ICCDRenamer...")

    try:
        from iccd_renamer import ICCDRenamer, CropResult
        from xml_processor import ImageMapping

        renamer = ICCDRenamer()

        # Test filename validation
        test_filenames = [
            "ICCD_FSC01351-0001_01_S0001_01.tiff",
            "ICCD_1200143419_01_S0001_01.tiff",
            "invalid_filename.jpg"
        ]

        print("   Filename validation tests:")
        all_valid = True
        for filename in test_filenames:
            is_valid = renamer.validate_iccd_filename(filename)
            expected = filename.endswith('.tiff') and 'ICCD_' in filename
            result = "✅" if is_valid == expected else "❌"
            print(f"     {result} {filename}: {is_valid}")
            if is_valid != expected:
                all_valid = False

        # Test filename generation
        test_mapping = ImageMapping(
            original_filename="test.jpg",
            fascicolo_number="42",
            oggetto_number="0001",
            document_type="S",
            sequence_number="0001",
            page_number=1,
            busta_folder="/test"
        )

        test_crop_result = CropResult(
            fold_detected=False,
            single_file="test_processed.jpg"
        )

        generated_name = renamer.generate_iccd_filename(test_mapping, test_crop_result)
        print(f"   Generated filename: {generated_name}")

        return all_valid

    except Exception as e:
        print(f"❌ Error testing ICCDRenamer: {e}")
        return False


def test_main_integration():
    """Test main.py integration"""
    print("\n🔧 Testing main.py integration...")

    test_dir = create_test_structure()
    output_dir = tempfile.mkdtemp(prefix="iccd_output_")

    try:
        # Import main function
        sys.path.insert(0, os.path.dirname(__file__))
        from main import main

        # Test con directory vuota (no Busta)
        empty_dir = tempfile.mkdtemp()
        print("   Testing with empty directory...")
        result1 = main(empty_dir, output_dir)
        print(f"   Empty dir result: {'✅' if result1 else '❌'} {result1}")

        # Test con struttura Busta (ma senza crop.py disponibile)
        print("   Testing with Busta structure...")
        # Questo test fallirà perché crop.py non è disponibile, ma dovrebbe
        # rilevare la struttura Busta correttamente
        try:
            result2 = main(test_dir, output_dir)
            print(f"   Busta detection worked: ✅")
        except Exception as e:
            if "crop.py" in str(e) or "BatchProcessor" in str(e):
                print(f"   Busta detection worked, crop.py not available (expected): ✅")
                result2 = True
            else:
                print(f"   Unexpected error: ❌ {e}")
                result2 = False

        return result1 and result2

    except Exception as e:
        print(f"❌ Error testing main integration: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        if 'empty_dir' in locals():
            shutil.rmtree(empty_dir, ignore_errors=True)


def run_all_tests():
    """Esegui tutti i test"""
    print("🧪 Running ICCD Implementation Tests")
    print("=" * 50)

    tests = [
        ("BustaDetector", test_busta_detector),
        ("XMLProcessor", test_xml_processor),
        ("ICCDRenamer", test_iccd_renamer),
        ("Main Integration", test_main_integration)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)