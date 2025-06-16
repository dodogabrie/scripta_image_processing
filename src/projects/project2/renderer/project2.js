// filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project2/renderer/project2.js
// Carica il template da file esterno via fetch
fetch('../projects/project2/renderer/project2.template.html')
    .then(response => response.text())
    .then(template => {
        window.project2 = {
            name: 'project2',
            template,
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
        };
    });