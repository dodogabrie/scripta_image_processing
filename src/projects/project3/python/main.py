#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project3/python/main.py

import sys
import os
import argparse
from utils.busta_detector import BustaDetector

def main(input_dir, output_dir):
    """
    Main processing function for MAGLIB with ICCD Busta support

    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
    """
    print(f"🚀 Processing started...")
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")

    # Ensure input directory exists
    if not os.path.exists(input_dir):
        print(f"❌ Input directory does not exist: {input_dir}")
        return False

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check if input contains Busta structure with XML files
    detector = BustaDetector()

    if detector.has_busta_structure(input_dir):
        print("🏷️  Detected ICCD Busta structure - using XML-based processing")

        # Print Busta summary
        detector.print_busta_summary(input_dir)

        # Validate structure before processing
        if not detector.validate_busta_structure(input_dir, verbose=True):
            print("❌ Busta structure validation failed. Please check XML files and image folders.")
            return False

        # Import and use batch processor for Busta workflow
        try:
            from batch_processor import BatchProcessor

            processor = BatchProcessor()
            stats = processor.process_all_bustas(input_dir, output_dir)

            # Check if processing was successful
            if len(stats.errors) > 0:
                print(f"⚠️  Processing completed with {len(stats.errors)} errors")
                print("Check the processing reports for details.")
                return False
            else:
                print("✅ ICCD Busta processing completed successfully!")
                return True

        except ImportError as e:
            print(f"❌ Error importing batch processor: {e}")
            print("Make sure all required modules are available.")
            return False
        except Exception as e:
            print(f"❌ Error in ICCD processing: {e}")
            return False

    else:
        print("📄 Standard processing mode (no Busta structure detected)")

        # Original processing logic for non-Busta workflows
        print("ℹ️  Add your standard processing logic here...")
        print("    This is where you can implement other MAGLIB processing workflows")
        print("    that don't involve ICCD Busta structure.")

        # Placeholder for other processing types
        # You can add other processing workflows here

        print("✅ Standard processing complete!")
        return True

def show_help():
    """Show detailed help information"""
    print("""
MAGLIB Processing Tool with ICCD Busta Support

This tool supports two processing modes:

1. ICCD Busta Mode (automatic detection):
   - Input structure: Multiple Busta_XX folders with corresponding Busta_XX.xml files
   - Processes images using crop.py from project2
   - Renames files according to ICCD conventions
   - Generates organized output with proper ICCD structure

2. Standard Mode:
   - For other MAGLIB processing workflows
   - Add custom processing logic as needed

Examples:
   python main.py /path/to/bustas /path/to/output
   python main.py --help

For Busta processing, expected input structure:
   input_dir/
   ├── Busta_42/
   │   ├── 0382.jpg
   │   └── 0383.jpg
   ├── Busta_42.xml
   ├── Busta_43/
   │   └── images...
   └── Busta_43.xml

The tool will automatically detect this structure and process accordingly.
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tool per elaborazione xml MAG standard con supporto ICCD Busta",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--help-detailed", action="store_true",
                       help="Show detailed help information")

    # Parse known args to handle --help-detailed before argparse validation
    if "--help-detailed" in sys.argv:
        show_help()
        sys.exit(0)

    args = parser.parse_args()

    # Set verbose logging if requested
    if args.verbose:
        print("🔍 Verbose mode enabled")

    # Run main processing
    success = main(args.input_dir, args.output_dir)

    # Exit with appropriate code
    sys.exit(0 if success else 1)