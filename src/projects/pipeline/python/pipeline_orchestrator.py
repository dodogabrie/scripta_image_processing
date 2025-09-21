#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/pipeline/python/pipeline_orchestrator.py

import sys
import os
import json
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path

class PipelineOrchestrator:
    def __init__(self, config):
        self.config = config
        self.temp_dirs = []
        self.current_step = 0
        self.total_steps = len(config['steps'])

    def log(self, message, step=None):
        """Log messages with step information"""
        if step is not None:
            print(f"[Step {step + 1}/{self.total_steps}] {message}")
        else:
            print(f"[Pipeline] {message}")
        sys.stdout.flush()

    def create_temp_dir(self, step_index):
        """Create a temporary directory for intermediate results"""
        temp_dir = tempfile.mkdtemp(prefix=f"pipeline_step_{step_index + 1}_")
        self.temp_dirs.append(temp_dir)
        self.log(f"Created temporary directory: {temp_dir}", step_index)
        return temp_dir

    def cleanup_temp_dirs(self):
        """Clean up all temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.log(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.log(f"Warning: Failed to clean up {temp_dir}: {e}")

    def get_project_script_path(self, project_id):
        """Get the path to a project's main Python script"""
        # Get the directory where this script is located
        current_dir = Path(__file__).parent.parent.parent
        self.log(f"Looking for project scripts in: {current_dir}")

        # Look for the project's main script
        project_dir = current_dir / project_id / "python"
        self.log(f"Project directory: {project_dir}")

        # Try different common script names
        possible_scripts = ["main.py", f"{project_id}.py", "process.py"]

        for script_name in possible_scripts:
            script_path = project_dir / script_name
            self.log(f"Checking script: {script_path}")
            if script_path.exists():
                self.log(f"Found script: {script_path}")
                return str(script_path)

        # If no common script found, look at the project's config
        try:
            config_path = current_dir / project_id / "config.json"
            self.log(f"Checking config: {config_path}")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    project_config = json.load(f)
                    python_scripts = project_config.get('python_scripts', [])
                    self.log(f"Python scripts from config: {python_scripts}")
                    if python_scripts:
                        # The script path in config is relative to project root, not python folder
                        script_path = current_dir / project_id / python_scripts[0]
                        self.log(f"Trying script from config: {script_path}")
                        if script_path.exists():
                            self.log(f"Found script from config: {script_path}")
                            return str(script_path)
        except Exception as e:
            self.log(f"Warning: Could not read project config for {project_id}: {e}")

        # List what's actually in the project directory for debugging
        try:
            if project_dir.exists():
                files = list(project_dir.iterdir())
                self.log(f"Files in {project_dir}: {[f.name for f in files]}")
            else:
                self.log(f"Project directory does not exist: {project_dir}")
        except Exception as e:
            self.log(f"Could not list project directory: {e}")

        raise FileNotFoundError(f"No Python script found for project {project_id}")

    def build_project_args(self, step, input_dir, output_dir):
        """Build command line arguments for a project using parameter mapping from config.json"""
        args = [input_dir, output_dir]
        project_id = step['projectId']
        parameters = step.get('parameters', {})

        # Load project config to get parameter mapping
        try:
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / project_id / "config.json"

            if config_path.exists():
                with open(config_path, 'r') as f:
                    project_config = json.load(f)
                    pipeline_parameters = project_config.get('pipeline_parameters', {})

                    # Add project-specific default parameters
                    if project_id == 'project2':
                        # Add Project2 default parameters (same as Vue component)
                        args.extend(['--smart_crop'])  # smartCrop: true (default ON)
                        args.extend(['--enable_file_listener'])  # enableFileListener: true (default ON)
                        self.log("Added Project2 default parameters: --smart_crop --enable_file_listener")

                    # Map user-configurable parameters using the config
                    for param_name, param_value in parameters.items():
                        if param_value and str(param_value).strip():
                            # Get the command line argument name from config
                            arg_name = pipeline_parameters.get(param_name)
                            if arg_name:
                                args.extend([arg_name, str(param_value)])
                                self.log(f"Mapped parameter {param_name}={param_value} to {arg_name}")
                            else:
                                # Fallback to generic mapping if not in config
                                args.extend([f"--{param_name}", str(param_value)])
                                self.log(f"Using generic mapping {param_name}={param_value}")
            else:
                self.log(f"No config found for {project_id}, using generic parameter mapping")
                # Fallback to generic mapping
                for param_name, param_value in parameters.items():
                    if param_value and str(param_value).strip():
                        args.extend([f"--{param_name}", str(param_value)])

        except Exception as e:
            self.log(f"Error loading parameter mapping for {project_id}: {e}")
            # Fallback to generic mapping
            for param_name, param_value in parameters.items():
                if param_value and str(param_value).strip():
                    args.extend([f"--{param_name}", str(param_value)])

        return args

    def execute_project(self, step_index, step, input_dir, output_dir):
        """Execute a single project step"""
        project_id = step['projectId']

        self.log(f"Starting execution of project '{project_id}'", step_index)
        self.log(f"Input directory: {input_dir}", step_index)
        self.log(f"Output directory: {output_dir}", step_index)

        try:
            # Get the project script path
            script_path = self.get_project_script_path(project_id)
            self.log(f"Using script: {script_path}", step_index)

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Build command arguments
            args = self.build_project_args(step, input_dir, output_dir)

            # Execute the project script
            cmd = [sys.executable, script_path] + args
            self.log(f"Executing command: {' '.join(cmd)}", step_index)

            # Run the subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout per step
            )

            if result.returncode == 0:
                self.log(f"Project '{project_id}' completed successfully", step_index)
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log(f"Project '{project_id}' failed with return code {result.returncode}", step_index)
                if result.stderr:
                    print(f"Error output: {result.stderr}", file=sys.stderr)
                if result.stdout:
                    print(f"Standard output: {result.stdout}")
                return False

        except FileNotFoundError as e:
            self.log(f"Script not found for project '{project_id}': {e}", step_index)
            return False
        except subprocess.TimeoutExpired:
            self.log(f"Project '{project_id}' timed out after 1 hour", step_index)
            return False
        except Exception as e:
            self.log(f"Unexpected error executing project '{project_id}': {e}", step_index)
            return False

    def execute_pipeline(self):
        """Execute the complete pipeline"""
        self.log("Starting pipeline execution")
        self.log(f"Input directory: {self.config['inputDir']}")
        self.log(f"Output directory: {self.config['outputDir']}")
        self.log(f"Total steps: {self.total_steps}")

        try:
            # Ensure the final output directory exists
            os.makedirs(self.config['outputDir'], exist_ok=True)

            # Set initial input directory
            current_input_dir = self.config['inputDir']

            # Execute each step in sequence
            for step_index, step in enumerate(self.config['steps']):
                self.current_step = step_index

                # Determine output directory for this step
                if step_index == self.total_steps - 1:
                    # Last step: output to final directory
                    current_output_dir = self.config['outputDir']
                else:
                    # Intermediate step: output to temporary directory
                    current_output_dir = self.create_temp_dir(step_index)

                # Execute the project
                success = self.execute_project(step_index, step, current_input_dir, current_output_dir)

                if not success:
                    self.log(f"Pipeline failed at step {step_index + 1}")
                    return False

                # Set input for next step to current output
                current_input_dir = current_output_dir

                # Progress reporting
                progress = ((step_index + 1) / self.total_steps) * 100
                self.log(f"Pipeline progress: {progress:.1f}%")

            self.log("Pipeline completed successfully!")
            return True

        except Exception as e:
            self.log(f"Pipeline execution failed: {e}")
            return False
        finally:
            # Clean up temporary directories
            self.cleanup_temp_dirs()

def main():
    """Main function to handle command line execution"""
    parser = argparse.ArgumentParser(description="Execute image processing pipeline")
    parser.add_argument("config", type=str, help="Pipeline configuration JSON string")

    args = parser.parse_args()

    try:
        print(f"Pipeline orchestrator started with config: {args.config}")

        # Parse the configuration
        config = json.loads(args.config)
        print(f"Parsed config: {config}")

        # Validate required fields
        required_fields = ['steps', 'inputDir', 'outputDir']
        for field in required_fields:
            if field not in config:
                print(f"Error: Missing required field '{field}' in pipeline configuration", file=sys.stderr)
                sys.exit(1)

        print(f"Configuration validated. Steps: {len(config['steps'])}")

        # Create and execute pipeline
        orchestrator = PipelineOrchestrator(config)
        success = orchestrator.execute_pipeline()

        if success:
            print("Pipeline execution completed successfully!")
            sys.exit(0)
        else:
            print("Pipeline execution failed!", file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON configuration: {e}", file=sys.stderr)
        print(f"Raw config string: {args.config}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Pipeline execution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()