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
                    borderPixels: '',
                    imageFormat: 'tif',
                    consoleLines: [],
                    elaborazioneCompletata: false,
                    thumbs: [],
                    thumbsInterval: null,
                    previewThumb: null,
                    lastThumb: null,
                    // Thresholds for quality evaluation
                    threshold_sharpness: 0.1,
                    threshold_entropy: 0.1,
                    threshold_edge_density: 0.1,
                    threshold_residual_skew_angle: 0.1,
                    qualityCheckResults: [],
                    qualityCheckReportPath: null,
                    enableSharpness: true,
                    enableEntropy: true,
                    enableEdgeDensity: true,
                    enableSkew: true,
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
                        // Rimuovi l'ultima miniatura (se presente)
                        if (thumbs.length > 0) {
                            this.thumbs = thumbs.slice(0, -1);
                            this.lastThumb = thumbs[thumbs.length - 1];
                        } else {
                            this.thumbs = [];
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
                async stopProcessing() {
                    // Forza la chiamata all'IPC per inviare SIGTERM al processo Python attivo
                    try {
                        // Preferisci sempre window.electronAPI.stopPythonProcess se esiste
                        if (window.electronAPI && typeof window.electronAPI.stopPythonProcess === 'function') {
                            await window.electronAPI.stopPythonProcess();
                            this.addConsoleLine('Processo Python terminato con segnale di stop.', 'warning');
                        } else if (window.electronAPI && typeof window.electronAPI.invoke === 'function') {
                            // fallback generico per ipcRenderer.invoke
                            await window.electronAPI.invoke('python:stop');
                            this.addConsoleLine('Processo Python terminato con segnale di stop (fallback invoke).', 'warning');
                        } else if (window.ipcRenderer && typeof window.ipcRenderer.invoke === 'function') {
                            // fallback legacy diretto su ipcRenderer globale
                            await window.ipcRenderer.invoke('python:stop');
                            this.addConsoleLine('Processo Python terminato con segnale di stop (ipcRenderer globale).', 'warning');
                        } else {
                            this.addConsoleLine('Nessuna funzione stopPythonProcess disponibile! Verifica preload.js e contextBridge.', 'error');
                        }
                    } catch (e) {
                        this.addConsoleLine('Errore durante lo stop del processo Python: ' + e.message, 'error');
                    }
                    this.processing = false;
                    this.stopThumbsPolling();
                },
                async evaluateQuality() {
                    if (!this.outputDir) {
                        this.addConsoleLine('Seleziona una cartella di output per valutare la qualità.', 'error');
                        return;
                    }
                    const qualityDir = this.outputDir + '/quality';
                    if (!window.electronAPI || !window.electronAPI.listQualityFiles || !window.electronAPI.readFile) {
                        this.addConsoleLine('Funzioni electronAPI per quality non disponibili.', 'error');
                        return;
                    }
                    const files = await window.electronAPI.listQualityFiles(qualityDir);
                    if (!files || files.length === 0) {
                        this.addConsoleLine('Nessun file di qualità trovato.', 'warning');
                        return;
                    }
                    const failed = [];
                    for (const file of files) {
                        try {
                            const content = await window.electronAPI.readFile(file);
                            const data = JSON.parse(content);
                            let fail = false;
                            let reasons = [];
                            let details = [];
                            if (this.enableSharpness && data.sharpness) {
                                const ratio = data.sharpness.processed / data.sharpness.original;
                                if (ratio < this.threshold_sharpness) {
                                    fail = true;
                                    reasons.push('sharpness');
                                    details.push(`sharpness: ${data.sharpness.processed.toFixed(2)} / ${data.sharpness.original.toFixed(2)} = ${ratio.toFixed(3)} < ${this.threshold_sharpness}`);
                                }
                            }
                            if (this.enableEntropy && data.entropy) {
                                const ratio = data.entropy.processed / data.entropy.original;
                                if (ratio < this.threshold_entropy) {
                                    fail = true;
                                    reasons.push('entropy');
                                    details.push(`entropy: ${data.entropy.processed.toFixed(3)} / ${data.entropy.original.toFixed(3)} = ${ratio.toFixed(3)} < ${this.threshold_entropy}`);
                                }
                            }
                            if (this.enableEdgeDensity && data.edge_density) {
                                const ratio = data.edge_density.processed / data.edge_density.original;
                                if (ratio < this.threshold_edge_density) {
                                    fail = true;
                                    reasons.push('edge_density');
                                    details.push(`edge_density: ${data.edge_density.processed.toFixed(4)} / ${data.edge_density.original.toFixed(4)} = ${ratio.toFixed(3)} < ${this.threshold_edge_density}`);
                                }
                            }
                            if (this.enableSkew && data.residual_skew_angle !== undefined) {
                                const absSkew = Math.abs(data.residual_skew_angle);
                                if (absSkew > this.threshold_residual_skew_angle) {
                                    fail = true;
                                    reasons.push('residual_skew_angle');
                                    details.push(`residual_skew_angle: ${absSkew.toFixed(2)} > ${this.threshold_residual_skew_angle}`);
                                }
                            }
                            if (fail) {
                                failed.push({ file, reasons, details });
                            }
                        } catch (e) {
                            this.addConsoleLine(`Errore lettura quality file ${file}: ${e.message}`, 'error');
                        }
                    }
                    this.qualityCheckResults = failed;
                    // Write report
                    const reportPath = qualityDir + '/quality_report.txt';
                    let reportText = '';
                    if (failed.length === 0) {
                        reportText = 'Tutte le immagini rispettano le soglie di qualità.\n';
                        this.addConsoleLine('Tutte le immagini rispettano le soglie di qualità.', 'success');
                    } else {
                        reportText = 'Immagini che NON rispettano le soglie di qualità:\n';
                        failed.forEach(f => {
                            reportText += `${f.file.split('/').pop()}: ${f.reasons.join(', ')}\n`;
                            f.details.forEach(d => {
                                reportText += `    ${d}\n`;
                            });
                            this.addConsoleLine(
                                `Quality FAIL: ${f.file.split('/').pop()} (${f.reasons.join(', ')})\n  ${f.details.join('\n  ')}`,
                                'error'
                            );
                        });
                    }
                    if (window.electronAPI && window.electronAPI.writeFile) {
                        await window.electronAPI.writeFile(reportPath, reportText);
                        this.qualityCheckReportPath = reportPath;
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
                },
            },
            mounted() {
                this.loadThumbs();
            }
        };
    });
