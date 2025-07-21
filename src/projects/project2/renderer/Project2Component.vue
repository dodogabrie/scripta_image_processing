<!-- filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project2/renderer/project2.template.html -->
<template>
    <div class="container-fluid mt-4">
        <div class="container-fluid mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div>
                            <h1>Ritaglio doppia pagina</h1>
                            <p class="text-muted">Ritaglia un doppio foglio A4 sulla piega e aggiorna l'ordine delle pagine generate dal ritaglio</p>
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
                                <label for="imageFormat" class="form-label">Formato immagini da elaborare:</label>
                                <select id="imageFormat" class="form-select" v-model="imageFormat">
                                    <option value="">Tutti i formati</option>
                                    <option value="tiff">TIFF</option>
                                    <option value="jpg">JPG</option>
                                </select>
                            </div>
                            
                            <div class="mt-3">
                                <label for="outputFormat" class="form-label">Formato di output:</label>
                                <select id="outputFormat" class="form-select" v-model="outputFormat">
                                    <option value="">Mantieni originale</option>
                                    <option value="tiff">TIFF</option>
                                    <option value="jpg">JPG</option>
                                    <option value="png">PNG</option>
                                </select>
                            </div>
                            
                            <div class="mt-3">
                                <label for="sideDetection" class="form-label">Rilevamento piega:</label>
                                <select id="sideDetection" class="form-select" v-model="sideDetection">
                                    <option value="">Auto-detect</option>
                                    <option value="left">Sinistra</option>
                                    <option value="right">Destra</option>
                                    <option value="center">Centro</option>
                                </select>
                            </div>
                            
                            <div class="mt-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="applyRotation" v-model="applyRotation">
                                    <label class="form-check-label" for="applyRotation">
                                        Applica rotazione per raddrizzare la piega
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="smartCrop" v-model="smartCrop">
                                    <label class="form-check-label" for="smartCrop">
                                        Crop intelligente (rileva bordi documento)
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enableDebug" v-model="enableDebug">
                                    <label class="form-check-label" for="enableDebug">
                                        Genera file di debug
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enableFileListener" v-model="enableFileListener">
                                    <label class="form-check-label" for="enableFileListener">
                                        Abilita rinominazione automatica file
                                    </label>
                                </div>
                            </div>
                            
                            <div v-if="enableFileListener" class="mt-3">
                                <label for="renameMap" class="form-label">Mappa di rinominazione (JSON):</label>
                                <textarea id="renameMap" class="form-control" rows="6" v-model="renameMapText" 
                                         placeholder='{"_01_right": "_01", "_01_left": "_04", "_02_left": "_02", "_02_right": "_03"}'>
                                </textarea>
                                <small class="form-text text-muted">
                                    Formato: {"pattern_da_sostituire": "sostituzione"}. Lascia vuoto per usare la mappa di default.
                                </small>
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
                                <div v-if="progressInfo" class="mt-4">
                                    <div class="progress mb-3" style="height: 20px;">
                                        <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                                             :style="{width: progressPercentage + '%'}" 
                                             :aria-valuenow="progressInfo.processed" 
                                             :aria-valuemin="0" 
                                             :aria-valuemax="progressInfo.total_images">
                                             {{ progressPercentage }}%
                                        </div>
                                    </div>
                                    <h5 class="text-muted">
                                        {{ progressInfo.processed }} / {{ progressInfo.total_images }} immagini elaborate
                                    </h5>
                                    <div class="small text-muted mt-2">
                                        <div>Formato: {{ progressInfo.primary_format }}</div>
                                        <div>Dimensione totale: {{ progressInfo.total_size_gb }} GB</div>
                                    </div>
                                </div>
                                <div v-else class="text-center">
                                    <div class="spinner-border text-primary mb-3" role="status">
                                        <span class="visually-hidden">Elaborazione...</span>
                                    </div>
                                    <h5 class="text-muted">Avvio elaborazione...</h5>
                                </div>
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
    </div>
</template>

<script>
export default {
    name: 'project2',
    data() {
        return {
            processing: false,
            inputDir: null,
            outputDir: null,
            consoleLines: [],
            elaborazioneCompletata: false,
            // Progress tracking
            progressInfo: null,
            progressInterval: null,
            // Processing parameters
            imageFormat: '',
            outputFormat: '',
            sideDetection: '',
            applyRotation: false,
            smartCrop: true,  // Default enabled
            enableDebug: false,
            enableFileListener: true,  // Default enabled
            renameMapText: '{"_01_right": "_01", "_01_left": "_04", "_02_left": "_02", "_02_right": "_03"}',
        };
    },
    computed: {
        progressPercentage() {
            if (!this.progressInfo || !this.progressInfo.total_images) return 0;
            return Math.round((this.progressInfo.processed / this.progressInfo.total_images) * 100);
        }
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
        async loadProgress() {
            if (window.electronAPI && window.electronAPI.readFile && this.outputDir) {
                try {
                    const infoPath = this.outputDir + '/info.json';
                    const content = await window.electronAPI.readFile(infoPath);
                    this.progressInfo = JSON.parse(content);
                } catch (error) {
                    // File doesn't exist yet or can't be read
                    this.progressInfo = null;
                }
            }
        },
        startProgressPolling() {
            this.loadProgress();
            if (this.progressInterval) clearInterval(this.progressInterval);
            this.progressInterval = setInterval(() => {
                this.loadProgress();
            }, 1000);
        },
        stopProgressPolling() {
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
                this.progressInterval = null;
            }
        },
        async processData() {
            this.addConsoleLine('Inizio elaborazione...', 'info');
            if (!this.inputDir || !this.outputDir) return;

            this.processing = true;
            this.elaborazioneCompletata = false;
            this.progressInfo = null;
            this.startProgressPolling();

            this.addConsoleLine(`Input: ${this.inputDir}`, 'info');
            this.addConsoleLine(`Output: ${this.outputDir}`, 'info');

            try {
                // Costruisci gli argomenti per lo script Python
                const args = [this.inputDir, this.outputDir];

                // Aggiungi parametri opzionali
                if (this.sideDetection) {
                    args.push('--side', this.sideDetection);
                    this.addConsoleLine(`Lato piega: ${this.sideDetection}`, 'info');
                }

                if (this.outputFormat) {
                    args.push('--output_format', this.outputFormat);
                    this.addConsoleLine(`Formato output: ${this.outputFormat.toUpperCase()}`, 'info');
                }

                if (this.imageFormat) {
                    args.push('--image_input_format', this.imageFormat);
                    this.addConsoleLine(`Formato input: ${this.imageFormat.toUpperCase()}`, 'info');
                }

                if (this.applyRotation) {
                    args.push('--rotate');
                    this.addConsoleLine('Rotazione abilitata', 'info');
                }

                if (this.smartCrop) {
                    args.push('--smart_crop');
                    this.addConsoleLine('Crop intelligente abilitato', 'info');
                }

                if (this.enableDebug) {
                    args.push('--debug');
                    this.addConsoleLine('Debug abilitato', 'info');
                }
                
                if (this.enableFileListener) {
                    args.push('--enable_file_listener');
                    this.addConsoleLine('File listener abilitato', 'info');
                    
                    // Valida e salva la mappa di rinominazione se fornita
                    if (this.renameMapText.trim()) {
                        try {
                            const renameMap = JSON.parse(this.renameMapText);
                            
                            // Salva la mappa in un file temporaneo
                            const mapPath = this.outputDir + '/rename_map.json';
                            if (window.electronAPI && window.electronAPI.writeFile) {
                                await window.electronAPI.writeFile(mapPath, this.renameMapText);
                                args.push('--rename_map_file', mapPath);
                                this.addConsoleLine(`Mappa di rinominazione: ${JSON.stringify(renameMap)}`, 'info');
                            }
                        } catch (e) {
                            this.addConsoleLine('Errore nel parsing della mappa di rinominazione, uso default', 'warning');
                        }
                    }
                }
                
                args.push('--verbose');

                const result = await window.electronAPI.runProjectScript(
                    'project2',
                    'main.py',
                    args
                );

                if (result.success) {
                    this.addConsoleLine('Elaborazione completata con successo!', 'success');
                    this.elaborazioneCompletata = true;
                    if (result.output) {
                        result.output.toString().split('\n').forEach(line => {
                            if (line.trim()) this.addConsoleLine(line.trim(), 'normal');
                        });
                    }
                } else {
                    this.addConsoleLine('Errore durante l\'elaborazione: ' + result.error, 'error');
                    this.elaborazioneCompletata = false;
                }
            } catch (error) {
                this.addConsoleLine('Errore JS: ' + error.message, 'error');
                this.elaborazioneCompletata = false;
            } finally {
                this.processing = false;
                this.stopProgressPolling();
                this.loadProgress();
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
}
</script>