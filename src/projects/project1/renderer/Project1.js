// Carica il template da file esterno via fetch
fetch('../projects/project1/renderer/Project1.template.html')
    .then(response => response.text())
    .then(template => {
        window.Project1 = {
            name: 'Project1',
            template,
            data() {
                return {
                    processing: false,
                    inputDir: null,
                    outputDir: null,
                    borderPixels: '', // campo per il bordo
                    imageFormat: 'tif', // campo per il formato immagine
                    consoleLines: [],
                    elaborazioneCompletata: false,
                    thumbs: [],
                    thumbsInterval: null,
                    previewThumb: null,
                    lastThumb: null
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
                async loadThumbs() {
                    if (window.electronAPI && window.electronAPI.listThumbs && this.outputDir) {
                        const thumbs = await window.electronAPI.listThumbs(this.outputDir + '/thumbs');
                        // Usa direttamente il percorso restituito dal backend
                        this.thumbs = thumbs;
                        if (this.thumbs.length > 0) {
                            this.lastThumb = this.thumbs[this.thumbs.length - 1];
                        } else {
                            this.lastThumb = null;
                        }
                    }
                },
                startThumbsPolling() {
                    this.loadThumbs();
                    if (this.thumbsInterval) clearInterval(this.thumbsInterval);
                    this.thumbsInterval = setInterval(() => {
                        this.loadThumbs();
                    }, 1000);
                },
                stopThumbsPolling() {
                    if (this.thumbsInterval) {
                        clearInterval(this.thumbsInterval);
                        this.thumbsInterval = null;
                    }
                },
                async processImages() {
                    window.electronAPI.logToMain('processImages chiamato dal renderer!');
                    this.addConsoleLine(`Inizio a elaborare le immagini...`, 'info');
                    if (!this.inputDir || !this.outputDir) return;
                    this.processing = true;
                    this.elaborazioneCompletata = false;
                    this.thumbs = [];
                    this.startThumbsPolling();
                    this.addConsoleLine(`Esecuzione script Python: microperspective-corrector/main.py`, 'info');
                    this.addConsoleLine(`Input: ${this.inputDir}`, 'info');
                    this.addConsoleLine(`Output: ${this.outputDir}`, 'info');
                    try {
                        const thumbDirAbs = this.outputDir + '/thumbs';
                        // Costruisci gli argomenti
                        const args = [
                            this.inputDir,
                            this.outputDir,
                            "--output_thumb", thumbDirAbs
                        ];
                        // Se borderPixels è stato inserito e valido, aggiungilo
                        if (this.borderPixels && !isNaN(Number(this.borderPixels))) {
                            args.push("--border", String(this.borderPixels));
                            this.addConsoleLine(`Bordo esterno: ${this.borderPixels} px`, 'info');
                        }
                        if (this.imageFormat) {
                            args.push("--image-input-format", this.imageFormat);
                            this.addConsoleLine(`Formato immagini: ${this.imageFormat.toUpperCase()}`, 'info');
                        }
                        const result = await window.electronAPI.runProjectScript(
                            'project1',
                            'microperspective-corrector/main.py',
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
                        this.stopThumbsPolling();
                        this.loadThumbs();
                    }
                },
                goBack() {
                    this.$emit('goBack');
                },
                showPreview(thumb) {
                    this.previewThumb = thumb;
                },
                closePreview() {
                    this.previewThumb = null;
                }
            },
            mounted() {
                this.loadThumbs();
            }
        };
    });
