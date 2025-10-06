# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scripta Image Processing is an Electron-based desktop application for automated image processing tasks, primarily focused on document scanning workflows. The application uses a plugin-based architecture where each "project" is a self-contained image processing tool with its own Python backend and Vue.js frontend.

## Core Architecture

### Multi-Manager System
The application uses a manager-based architecture coordinated from `src/main.js`:
- **ProjectManager** (`src/managers/ProjectManager.js`): Discovers and loads project plugins from `src/projects/`, validates pipeline configurations
- **PythonManager** (`src/managers/PythonManager.js`): Manages Python virtual environment, embedded Python distribution (Windows), and script execution
- **WindowManager** (`src/managers/WindowManager.js`): Creates and manages Electron windows for the main app and individual projects
- **IPC Communication** (`src/setupIPC.js`): Handles all renderer-to-main process communication

### Project Plugin System
Each project in `src/projects/` is structured as:
```
src/projects/projectN/
├── config.json           # Project metadata and configuration
├── renderer/             # Vue.js frontend components
│   ├── ProjectNComponent.vue
│   └── assets/
└── python/               # Python backend scripts
    ├── main.py          # Entry point
    └── src/             # Project-specific modules
```

**config.json structure:**
- `name`, `description`, `icon`: UI metadata
- `main`: Path to Vue component
- `python_scripts`: Array of Python entry points
- `requirements`: Python dependencies (optional, overrides global)
- `pipeline_parameters`: CLI parameter mappings for pipeline mode (optional)
- `type`: "pipeline" for orchestration projects (optional)

### Python Environment Management
- **Development**: Uses `.venv/bin/python` in repository root
- **Production (Windows)**: Uses embedded Python from `python-embed/` directory
- **Production (Linux)**: Uses virtual environment in `app.getPath('userData')/python_env`
- Python scripts in production are unpacked to `app.asar.unpacked/src/projects/*/python/`
- libvips Windows DLL dependencies are automatically added to PATH during script execution

### Pipeline System
Projects can be chained together in processing pipelines:
- Pipeline configuration validated via `ProjectManager.validatePipelineConfig()`
- Each step references a project by ID and passes parameters
- Temporary directories created between pipeline steps
- Pipeline orchestrator script expected at `projects/pipeline/python/pipeline_orchestrator.py`

## Development Commands

### Installation & Setup
```bash
npm install              # Install Node.js dependencies
python -m venv .venv     # Create Python virtual environment
source .venv/bin/activate  # Activate venv (Linux/Mac)
pip install -r requirements.txt  # Install Python dependencies
```

### Running the Application
```bash
npm run dev              # Development mode (starts Vite dev server + Electron)
npm start                # Production mode (requires built renderer)
```

### Building
```bash
npm run vite:build       # Build Vue.js renderer only
npm run build-rust       # Build Rust optimizers (if present)
npm run prebuild         # Build renderer + download Windows deps + build Rust
npm run build            # Full production build (creates distributable)
npm run build:win        # Windows-specific build
```

### Project Creation
```bash
npm run create-project   # Interactive script to scaffold new project plugin
```

## Key Technical Details

### IPC Handlers (Main Process → Renderer)
- `projects:getAll`: Loads and returns all project configurations
- `projects:open`: Opens project in new window
- `projects:runScript(projectId, scriptName, args)`: Executes Python script, buffered output
- `projects:runScriptStreaming(projectId, scriptName, args)`: Executes Python with real-time stdout/stderr streaming via `python:output` events
- `pipeline:validate(config)`: Validates pipeline configuration
- `pipeline:runStreaming(config)`: Executes pipeline with streaming output
- `dialog:selectDirectory`: Native directory picker
- `files:listThumbs`, `files:listQualityFiles`, `files:readFile`, `files:writeFile`: File system operations

### Python Script Execution
Python scripts receive arguments as command-line parameters and should:
- Use `print()` for user-facing output (captured and displayed in UI)
- Use `sys.stderr.write()` for errors
- Return exit code 0 for success, non-zero for failure
- For streaming mode, output is sent to renderer in real-time via IPC events

### Existing Projects
1. **project1**: Micro-rotation correction and document cropping using computer vision
2. **project2**: ICCD double-page splitting - detects fold line and splits A4 scans into separate pages with automatic ordering
3. **project3**: MAGLIB - XML processing tool for MAG standard library metadata

## Working with the Codebase

### Adding a New Project
1. Run `npm run create-project` or manually create directory in `src/projects/`
2. Create `config.json` with required fields
3. Implement Vue component in `renderer/` for UI
4. Implement Python script in `python/main.py` with argparse CLI
5. Project will auto-load on next app restart

### Modifying Python Scripts
- Development: Edit directly in `src/projects/*/python/`
- Changes take effect immediately (no rebuild needed in dev mode)
- Production: Scripts are unpacked from asar, modifications require rebuild

### Frontend Development
- Renderer source: `src/renderer/`
- Uses Vite with HMR in development mode
- Production build outputs to `dist/renderer/`
- Main Vue app loads project components dynamically via `config.json`

### Working with Pipelines
- Validate configuration before execution using `pipeline:validate` IPC handler
- Each step must reference an existing non-pipeline project
- Steps execute sequentially with output directory of step N becoming input of step N+1
- Use `pipeline_parameters` in project config to map UI parameters to CLI flags
