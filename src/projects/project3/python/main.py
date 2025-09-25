#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project3/python/main.py

import argparse
import os
import subprocess
import glob
import json
import sys
from pathlib import Path


def load_maglib_commands():
    """Load maglib commands from JSON configuration file"""
    config_path = Path(__file__).parent.parent / "maglib_commands.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config["commands"]
    except FileNotFoundError:
        print(f"[ERROR] Configuration file not found: {config_path}")
        print("Using fallback command definitions...")
        return get_fallback_commands()
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in configuration file: {e}")
        print("Using fallback command definitions...")
        return get_fallback_commands()


def get_fallback_commands():
    """Fallback command definitions if JSON config is not available"""
    return {
        "adapt_fs_iccd": {
            "script": "adapt_fs_iccd.py",
            "name": "Adatta FS ICCD",
            "description": "Adatta file system per standard ICCD",
            "category": "File System",
            "base_params": ["-M", "{file}"],
            "required_params": ["--ignore-missing"],
            "configurable_params": {},
            "usage_pattern": "mass_mode"
        }
    }


def build_command_params(command_key, xml_file, config_commands, custom_params=None):
    """Build complete command parameters for a command"""
    if command_key not in config_commands:
        raise ValueError(f"Unknown command: {command_key}")

    command_info = config_commands[command_key]

    if custom_params:
        # Use custom parameters if provided
        return custom_params

    # Build from JSON configuration
    params = []

    # Add base parameters
    base_params = command_info.get("base_params", [])
    for param in base_params:
        params.append(param.replace("{file}", xml_file))

    # Add required parameters
    required_params = command_info.get("required_params", [])
    params.extend(required_params)

    # Add configurable parameters with defaults
    configurable_params = command_info.get("configurable_params", {})
    for param_key, param_info in configurable_params.items():
        param_flag = param_info["param"]
        default_value = param_info["default"]
        param_type = param_info.get("type", "string")

        if param_type == "boolean" and default_value:
            params.append(param_flag)
        elif param_type != "boolean" and default_value:
            params.extend([param_flag, str(default_value)])

    return params


# Load commands from JSON config
MAGLIB_COMMANDS = load_maglib_commands()


def setup_maglib_environment():
    """Setup environment variables for maglib"""
    current_dir = Path(__file__).parent / "maglib"
    script_dir = current_dir / "script"

    # Add maglib script directory to PATH
    current_path = os.environ.get('PATH', '')
    if str(script_dir) not in current_path:
        os.environ['PATH'] = f"{script_dir}{os.pathsep}{current_path}"

    # Add maglib to PYTHONPATH
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    if str(current_dir) not in current_pythonpath:
        os.environ['PYTHONPATH'] = f"{current_dir}{os.pathsep}{current_pythonpath}"

    print(f"[INFO] Added {script_dir} to PATH")
    print(f"[INFO] Added {current_dir} to PYTHONPATH")


def get_xml_files(directory):
    """Get all XML files in the directory"""
    xml_files = glob.glob(os.path.join(directory, "*.xml"))
    return xml_files



def execute_command(command_key, xml_file, custom_params=None):
    """Execute a maglib command on an XML file using module invocation"""
    if command_key not in MAGLIB_COMMANDS:
        raise ValueError(f"Unknown command: {command_key}")

    command_info = MAGLIB_COMMANDS[command_key]

    # Build command parameters
    cmd_params = build_command_params(command_key, xml_file, MAGLIB_COMMANDS, custom_params)

    # Convert script filename (e.g., adapt_fs_iccd.py) → module name (maglib.script.adapt_fs_iccd)
    script_name = command_info["script"]
    module_name = f"maglib.script.{Path(script_name).stem}"

    # Build final command: python -m maglib.script.adapt_fs_iccd ...
    cmd = [sys.executable, "-m", module_name] + cmd_params

    print(f"[EXEC] {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,
            cwd=os.path.dirname(xml_file),
        )

        if result.stdout:
            print(f"[STDOUT] {result.stdout}")
        if result.stderr:
            print(f"[STDERR] {result.stderr}")

        if result.returncode != 0:
            print(f"[ERROR] Command failed with return code {result.returncode}")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Exception executing command: {e}")
        return False


def main(input_dir, command_key, custom_params=None, dry_run=False):
    """
    Main processing function for maglib commands

    Args:
        input_dir (str): Input directory path containing XML files
        command_key (str): Key of the command to execute
        custom_params (list): Custom parameters for the command
        dry_run (bool): If True, only show what would be executed
    """
    print("MAGLIB XML Processing Tool")
    print("=" * 50)
    print(f"Input directory: {input_dir}")
    print(f"Command: {command_key}")

    if command_key not in MAGLIB_COMMANDS:
        print(f"[ERROR] Unknown command: {command_key}")
        print("Available commands:")
        for cmd_key, cmd_info in MAGLIB_COMMANDS.items():
            print(f"  {cmd_key}: {cmd_info['description']}")
        return False

    command_info = MAGLIB_COMMANDS[command_key]
    print(f"Name: {command_info.get('name', command_info['script'])}")
    print(f"Description: {command_info['description']}")
    print(f"Category: {command_info['category']}")

    # Setup maglib environment
    setup_maglib_environment()

    # Find XML files
    xml_files = get_xml_files(input_dir)
    if not xml_files:
        print("[ERROR] No XML files found in input directory")
        return False

    print(f"[INFO] Found {len(xml_files)} XML files to process")

    if dry_run:
        print("[DRY RUN] Would execute the following commands:")
        for xml_file in xml_files:
            params = build_command_params(command_key, xml_file, MAGLIB_COMMANDS, custom_params)
            cmd = [command_info["script"]] + params
            print(f"  {' '.join(cmd)}")
        return True

    # Process each XML file
    success_count = 0
    error_count = 0

    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n[{i}/{len(xml_files)}] Processing: {os.path.basename(xml_file)}")

        success = execute_command(command_key, xml_file, custom_params)
        if success:
            success_count += 1
            print(f"[OK] Successfully processed {os.path.basename(xml_file)}")
        else:
            error_count += 1
            print(f"[FAILED] Error processing {os.path.basename(xml_file)}")

    # Final report
    print("\n" + "=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Total files: {len(xml_files)}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {(success_count/len(xml_files)*100):.1f}%")

    return error_count == 0


def list_commands():
    """List all available commands grouped by category"""
    categories = {}
    for cmd_key, cmd_info in MAGLIB_COMMANDS.items():
        category = cmd_info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append((cmd_key, cmd_info))

    print("Available MAGLIB Commands:")
    print("=" * 50)
    for category, commands in categories.items():
        print(f"\n{category}:")
        for cmd_key, cmd_info in commands:
            name = cmd_info.get('name', cmd_key)
            print(f"  {cmd_key}: {name} - {cmd_info['description']}")


def export_commands_json():
    """Export commands configuration as JSON for frontend consumption"""
    try:
        config_path = Path(__file__).parent.parent / "maglib_commands.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"{{\"error\": \"Failed to load config: {e}\"}}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAGLIB XML Processing Tool")
    parser.add_argument("input_dir", nargs="?", type=str, help="Input directory containing XML files")
    parser.add_argument("command", nargs="?", type=str, help="Command to execute")
    parser.add_argument("--list-commands", action="store_true",
                       help="List all available commands and exit")
    parser.add_argument("--export-json", action="store_true",
                       help="Export commands configuration as JSON")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be executed without running")
    parser.add_argument("--custom-params", type=str, nargs="*",
                       help="Custom parameters for the command")

    args = parser.parse_args()

    if args.export_json:
        success = export_commands_json()
        sys.exit(0 if success else 1)

    if args.list_commands:
        list_commands()
        sys.exit(0)

    if not args.input_dir or not args.command:
        parser.print_help()
        sys.exit(1)

    success = main(args.input_dir, args.command, args.custom_params, args.dry_run)
    sys.exit(0 if success else 1)
