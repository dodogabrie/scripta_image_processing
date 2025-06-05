import sys
import json
from datetime import datetime

def main():
    print("Script Python avviato con successo!")
    print(f"Versione Python: {sys.version}")
    print(f"Script eseguito alle: {datetime.now()}")
    
    # Test command line arguments
    if len(sys.argv) > 1:
        print(f"Argomenti ricevuti: {sys.argv[1:]}")
    
    # Test importing installed packages
    try:
        import numpy as np
        print(f"Versione NumPy: {np.__version__}")
        
        import PIL
        print(f"Versione Pillow: {PIL.__version__}")
        
        import cv2
        print(f"Versione OpenCV: {cv2.__version__}")
        
    except ImportError as e:
        print(f"Errore importazione: {e}")
    
    # Return some test data
    result = {
        "status": "successo",
        "message": "Ambiente Python funziona correttamente",
        "timestamp": datetime.now().isoformat(),
        "packages_available": True
    }
    
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
