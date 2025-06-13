const fs = require('fs');
const path = require('path');

function createProject(projectName, projectDisplayName, projectDescription) {
    const projectsDir = path.join(__dirname, '..', 'src', 'projects');
    const projectDir = path.join(projectsDir, projectName);
    
    // Check if project already exists
    if (fs.existsSync(projectDir)) {
        console.error(`Project ${projectName} already exists!`);
        process.exit(1);
    }
    
    // Create project directory structure
    const dirs = [
        projectDir,
        path.join(projectDir, 'renderer'),
        path.join(projectDir, 'renderer', 'assets'),
        path.join(projectDir, 'python')
    ];
    
    dirs.forEach(dir => {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created directory: ${dir}`);
    });
    
    // Create config.json
    const config = {
        "name": projectDisplayName,
        "description": projectDescription,
        "icon": "renderer/assets/icon.svg",
        "version": "1.0.0",
        "main": "renderer/main.html",
        "renderer_script": `renderer/${projectName}.js`,
        "python_scripts": [
            "python/main.py"
        ],
        "requirements": [
            "opencv-python==4.10.0.84",
            "numpy==2.2.1"
        ]
    };
    
    fs.writeFileSync(
        path.join(projectDir, 'config.json'),
        JSON.stringify(config, null, 2),
        'utf-8'
    );
    
    // Create main.html
    const mainHtml = `<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${projectDisplayName}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body>
    <div id="app"></div>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="${projectName}.js"></script>
    <script>
        const { createApp } = Vue;
        createApp(window.${projectName}).mount('#app');
    </script>
</body>
</html>`;
    
    fs.writeFileSync(
        path.join(projectDir, 'renderer', 'main.html'),
        mainHtml,
        'utf-8'
    );
    
    // Create template.html
    const templateHtml = `<!-- filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/${projectName}/renderer/${projectName}.template.html -->
<div>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h1>${projectDisplayName}</h1>
                        <p class="text-muted">${projectDescription}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Input Section -->
            <div class="col-lg-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Configurazione Input</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <button @click="selectInputDir" class="btn btn-primary w-100 mb-2">
                                <i class="bi bi-folder2-open"></i> Scegli cartella di input
                            </button>
                            <div v-if="inputDir" class="alert alert-info py-2 px-3 mb-2">
                                <strong>Input:</strong>
                                <div class="small text-break">{{ inputDir }}</div>
                            </div>
                            <button @click="selectOutputDir" class="btn btn-secondary w-100 mb-2">
                                <i class="bi bi-folder2-open"></i> Scegli cartella di output
                            </button>
                            <div v-if="outputDir" class="alert alert-info py-2 px-3">
                                <strong>Output:</strong>
                                <div class="small text-break">{{ outputDir }}</div>
                            </div>
                            <div v-if="!inputDir" class="text-muted mt-2">
                                Nessuna cartella di input selezionata.
                            </div>
                            <div v-if="!outputDir" class="text-muted">
                                Nessuna cartella di output selezionata.
                            </div>
                        </div>
                        <!-- Add your custom parameters here -->
                        <div class="mt-3">
                            <label class="form-label">Parametri aggiuntivi:</label>
                            <p class="text-muted small">Aggiungi qui i controlli specifici per questo progetto</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Output Section -->
            <div class="col-lg-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Risultato</h5>
                    </div>
                    <div class="card-body position-relative">
                        <div v-if="!processing && !elaborazioneCompletata" class="text-center text-muted py-5">
                            <i class="bi bi-image fs-1"></i>
                            <h5 class="mt-3">I risultati appariranno qui</h5>
                            <p>Seleziona le cartelle e clicca "Elabora" per processare</p>
                        </div>
                        
                        <!-- Progress bar during processing -->
                        <div v-else-if="processing" class="text-center py-5">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Elaborazione...</span>
                            </div>
                            <h5 class="text-muted">Elaborazione in corso...</h5>
                            <p class="text-muted">Attendere...</p>
                        </div>
                        
                        <div v-else-if="elaborazioneCompletata" class="alert alert-success py-2 px-3">
                            <strong>Elaborazione completata!</strong><br>
                            <span>Risultati salvati in:</span>
                            <div class="small text-break">{{ outputDir }}</div>
                        </div>
                    </div>
                    <div class="card-footer" v-if="inputDir && outputDir">
                        <button @click="processData"
                                :disabled="processing || !inputDir || !outputDir"
                                class="btn btn-primary w-100">
                            <span v-if="processing" class="spinner-border spinner-border-sm me-2"></span>
                            <i v-else class="bi bi-gear"></i>
                            {{ processing ? 'Elaborazione...' : 'Elabora' }}
                        </button>
                        <button class="btn btn-outline-danger w-100 mt-2" @click="stopProcessing" :disabled="!processing">
                            <i class="bi bi-stop-circle"></i> Stop
                        </button>
                    </div>
                    <!-- Console output -->
                    <div class="mt-3">
                        <h6 class="text-muted mb-1"><i class="bi bi-terminal"></i> Console</h6>
                        <div style="background:#222;color:#eee;padding:10px;border-radius:6px;min-height:80px;max-height:180px;overflow:auto;font-size:13px;font-family:monospace;"
                             id="console-output">
                            <div v-for="(line, idx) in consoleLines" :key="idx" :style="{color: line.type==='error' ? '#ff6b6b' : (line.type==='success' ? '#51cf66' : '#eee')}">
                                {{ line.text }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>`;
    
    fs.writeFileSync(
        path.join(projectDir, 'renderer', `${projectName}.template.html`),
        templateHtml,
        'utf-8'
    );
    
    // Create JS file
    const jsFile = `// filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/${projectName}/renderer/${projectName}.js
// Carica il template da file esterno via fetch
fetch('../projects/${projectName}/renderer/${projectName}.template.html')
    .then(response => response.text())
    .then(template => {
        window.${projectName} = {
            name: '${projectName}',
            template,
            data() {
                return {
                    processing: false,
                    inputDir: null,
                    outputDir: null,
                    consoleLines: [],
                    elaborazioneCompletata: false,
                    // Add your data properties here
                };
            },
            methods: {
                addConsoleLine(text, type = 'normal') {
                    this.consoleLines.push({ text, type });
                    if (this.consoleLines.length > 100) this.consoleLines.shift();
                    this.$nextTick(() => {
                        const el = document.getElementById('console-output');
                        if (el) el.scrollTop = el.scrollHeight;
                    });
                },
                async selectInputDir() {
                    this.addConsoleLine('Selezione cartella di input...', 'info');
                    if (!window.electronAPI || !window.electronAPI.selectDirectory) {
                        this.addConsoleLine('electronAPI.selectDirectory non disponibile', 'error');
                        return;
                    }
                    const dir = await window.electronAPI.selectDirectory();
                    if (dir) {
                        this.inputDir = dir;
                        this.elaborazioneCompletata = false;
                        this.addConsoleLine('Cartella input selezionata: ' + dir, 'success');
                    } else {
                        this.addConsoleLine('Selezione cartella input annullata.', 'warning');
                    }
                },
                async selectOutputDir() {
                    this.addConsoleLine('Selezione cartella di output...', 'info');
                    if (!window.electronAPI || !window.electronAPI.selectDirectory) {
                        this.addConsoleLine('electronAPI.selectDirectory non disponibile', 'error');
                        return;
                    }
                    const dir = await window.electronAPI.selectDirectory();
                    if (dir) {
                        this.outputDir = dir;
                        this.elaborazioneCompletata = false;
                        this.addConsoleLine('Cartella output selezionata: ' + dir, 'success');
                    } else {
                        this.addConsoleLine('Selezione cartella output annullata.', 'warning');
                    }
                },
                async processData() {
                    this.addConsoleLine('Inizio elaborazione...', 'info');
                    if (!this.inputDir || !this.outputDir) return;
                    this.processing = true;
                    this.elaborazioneCompletata = false;
                    this.addConsoleLine(\`Input: \${this.inputDir}\`, 'info');
                    this.addConsoleLine(\`Output: \${this.outputDir}\`, 'info');
                    try {
                        // Add your processing logic here
                        const result = await window.electronAPI.runProjectScript(
                            '${projectName}',
                            'main.py',
                            [this.inputDir, this.outputDir]
                        );
                        if (result.success) {
                            this.addConsoleLine('Elaborazione completata con successo!', 'success');
                            this.elaborazioneCompletata = true;
                            if (result.output) {
                                result.output.toString().split('\\n').forEach(line => {
                                    if (line.trim()) this.addConsoleLine(line.trim(), 'normal');
                                });
                            }
                        } else {
                            this.addConsoleLine('Errore durante l\\'elaborazione: ' + result.error, 'error');
                            this.elaborazioneCompletata = false;
                        }
                    } catch (error) {
                        this.addConsoleLine('Errore JS: ' + error.message, 'error');
                        this.elaborazioneCompletata = false;
                    } finally {
                        this.processing = false;
                    }
                },
                async stopProcessing() {
                    try {
                        if (window.electronAPI && typeof window.electronAPI.stopPythonProcess === 'function') {
                            await window.electronAPI.stopPythonProcess();
                            this.addConsoleLine('Processo terminato.', 'warning');
                        }
                    } catch (e) {
                        this.addConsoleLine('Errore durante lo stop: ' + e.message, 'error');
                    }
                    this.processing = false;
                },
                goBack() {
                    this.$emit('goBack');
                },
            },
            mounted() {
                // Initialize component
            }
        };
    });`;
    
    fs.writeFileSync(
        path.join(projectDir, 'renderer', `${projectName}.js`),
        jsFile,
        'utf-8'
    );
    
    // Create Python main.py
    const pythonMain = `#!/usr/bin/env python3
# filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/${projectName}/python/main.py

import sys
import os
import argparse

def main(input_dir, output_dir):
    """
    Main processing function for ${projectDisplayName}
    
    Args:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
    """
    print(f"Processing started...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Add your processing logic here
    print("Processing logic goes here...")
    
    print("Processing complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="${projectDescription}")
    parser.add_argument("input_dir", type=str, help="Input directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)`;
    
    fs.writeFileSync(
        path.join(projectDir, 'python', 'main.py'),
        pythonMain,
        'utf-8'
    );
    
    // Create placeholder icon
    const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
  <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
  <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"/>
</svg>`;
    
    fs.writeFileSync(
        path.join(projectDir, 'renderer', 'assets', 'icon.svg'),
        iconSvg,
        'utf-8'
    );
    
    console.log(`\n✅ Project ${projectName} created successfully!`);
    console.log(`📁 Location: ${projectDir}`);
    console.log(`\nNext steps:`);
    console.log(`1. Customize the template in renderer/${projectName}.template.html`);
    console.log(`2. Add your processing logic in python/main.py`);
    console.log(`3. Update config.json with specific requirements`);
    console.log(`4. Test your project in the main application`);
}

// Parse command line arguments
if (process.argv.length < 5) {
    console.log('Usage: node create-project.js <project_name> <display_name> <description>');
    console.log('Example: node create-project.js project2 "Image Enhancer" "Enhance image quality using AI algorithms"');
    process.exit(1);
}

const [,, projectName, displayName, description] = process.argv;

// Validate project name
if (!/^[a-z][a-z0-9]*$/.test(projectName)) {
    console.error('Project name must be lowercase letters and numbers only, starting with a letter');
    process.exit(1);
}

createProject(projectName, displayName, description);
