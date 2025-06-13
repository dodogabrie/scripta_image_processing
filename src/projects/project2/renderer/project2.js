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
                    this.addConsoleLine(`Input: ${this.inputDir}`, 'info');
                    this.addConsoleLine(`Output: ${this.outputDir}`, 'info');
                    try {
                        // Add your processing logic here
                        const result = await window.electronAPI.runProjectScript(
                            'project2',
                            'main.py',
                            [this.inputDir, this.outputDir]
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