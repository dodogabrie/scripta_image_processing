import sys
import os
import tempfile
from pathlib import Path

# Add the microperspective-corrector directory to the path
current_dir = Path(__file__).parent
microperspective_dir = current_dir / "microperspective-corrector"
sys.path.insert(0, str(microperspective_dir))

# Import the main processing function
from edge_detection import process_tiff

def main():
    if len(sys.argv) < 2:
        print("Uso: python microperspective_wrapper.py <input_path> [border_pixels] [show_steps]")
        return 1
    
    input_path = sys.argv[1]
    border_pixels = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    show_steps = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
    
    try:
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as temp_output:
            output_path = temp_output.name
        
        # Process the image using microperspective-corrector
        process_tiff(
            image_path=input_path,
            output_path_tiff=output_path,
            output_path_thumb=None,
            border_pixels=border_pixels,
            show_step_by_step=show_steps,
            show_before_after=False
        )
        
        # Return the path to the processed image
        print(output_path)
        return 0
        
    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
