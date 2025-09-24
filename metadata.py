
from PIL import Image
import sys

def check_metadata(image_path: str):
    """
    Check if an image contains metadata (EXIF or other info).
    
    Parameters:
        image_path (str): Path to the image file.
    
    Returns:
        dict: Dictionary with metadata if present, otherwise empty.
    """
    try:
        with Image.open(image_path) as img:
            # Prova a leggere EXIF
            exif_data = img.getexif()
            # Prova a leggere eventuali info generiche
            info_data = img.info

            metadata_found = {}

            if exif_data and len(exif_data) > 0:
                metadata_found["exif"] = {
                    k: v for k, v in exif_data.items()
                }

            if info_data and len(info_data) > 0:
                metadata_found["info"] = info_data

            return metadata_found

    except Exception as e:
        print(f"Errore nell'apertura del file {image_path}: {e}")
        return {}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python check_metadata.py <immagine>")
        sys.exit(1)

    image_file = sys.argv[1]
    metadata = check_metadata(image_file)

    if metadata:
        print(f"✅ Metadati trovati in '{image_file}':")
        for section, data in metadata.items():
            print(f"\n--- {section.upper()} ---")
            for k, v in data.items():
                print(f"{k}: {v}")
    else:
        print(f"❌ Nessun metadato trovato in '{image_file}'")