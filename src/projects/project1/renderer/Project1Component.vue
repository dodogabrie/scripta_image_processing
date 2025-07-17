<template>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h1>Correzione Microrotazioni</h1>
                        <p class="text-muted">Corregge automaticamente le microrotazioni e ritaglia le scansioni di documenti</p>
                    </div>
                </div>
            </div>
        </div>
    
        <div class="row">
            <!-- Input Section -->
            <div class="col-lg-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Seleziona Cartelle</h5>
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
                        <div class="mt-3">
                            <label for="borderPixels" class="form-label">Bordo esterno (pixel, opzionale):</label>
                            <input id="borderPixels" type="number" min="0" class="form-control"
                                   v-model="borderPixels" placeholder="100">
                        </div>
                        <div class="mt-3">
                            <label for="imageFormat" class="form-label">Formato immagini da elaborare:</label>
                            <select id="imageFormat" class="form-select" v-model="imageFormat">
                                <option value="jpg">JPG</option>
                                <option value="tiff">TIF</option>
                            </select>
                        </div>
                        <div class="mt-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="useLzwCompression" v-model="useLzwCompression">
                                <label class="form-check-label" for="useLzwCompression">
                                    Usa compressione LZW per file TIFF
                                </label>
                                <div class="form-text">La compressione LZW riduce la dimensione dei file TIFF senza perdita di qualità</div>
                            </div>
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
                            <p>Seleziona una cartella di input e clicca "Elabora" per processare tutte le immagini</p>
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
                            <strong>Immagini elaborate!</strong><br>
                            <span>Risultati salvati in:</span>
                            <div class="small text-break">{{ outputDir }}</div>
                        </div>

                        <!-- Modal anteprima -->
                        <div v-if="previewThumb" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1000;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;" @click="closePreview">
                            <img :src="previewThumb" style="max-width:90vw;max-height:90vh;border:4px solid #fff;border-radius:8px;box-shadow:0 0 32px #000;">
                        </div>

                        <!-- Ultima anteprima -->
                        <div v-if="processing && lastThumb" class="text-center py-2">
                            <span class="text-muted small">Ultima anteprima:</span><br>
                            <img :src="lastThumb" style="max-width:180px;max-height:120px;border:2px solid #ccc;border-radius:6px;margin-top:6px;">
                        </div>
                    </div>
                    <div class="card-footer" v-if="inputDir && outputDir">
                        <button @click="processImages"
                                :disabled="processing || !inputDir || !outputDir"
                                class="btn btn-primary w-100">
                            <span v-if="processing" class="spinner-border spinner-border-sm me-2"></span>
                            <i v-else class="bi bi-gear"></i>
                            {{ processing ? 'Elaborazione...' : 'Elabora Immagini' }}
                        </button>
                        <!-- Pulsante stop accanto al bottone di elaborazione -->
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

        <!-- Quality Evaluation Section -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Valutazione Qualità Immagini</h5>
                    </div>
                    <div class="card-body">
                        <div class="mt-3">
                            <label class="form-label">Soglie qualità (processed/original &gt; soglia, skew &lt; soglia):</label>
                            <div class="row g-2">
                                <div class="col">
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="checkbox" id="enableSharpness" v-model="enableSharpness">
                                        <label class="form-check-label" for="enableSharpness">Sharpness</label>
                                    </div>
                                    <input type="number" step="0.01" min="0" max="1" class="form-control mt-1"
                                           v-model.number="threshold_sharpness" placeholder="Sharpness" :disabled="!enableSharpness">
                                </div>
                                <div class="col">
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="checkbox" id="enableEntropy" v-model="enableEntropy">
                                        <label class="form-check-label" for="enableEntropy">Entropy</label>
                                    </div>
                                    <input type="number" step="0.01" min="0" max="1" class="form-control mt-1"
                                           v-model.number="threshold_entropy" placeholder="Entropy" :disabled="!enableEntropy">
                                </div>
                                <div class="col">
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="checkbox" id="enableEdgeDensity" v-model="enableEdgeDensity">
                                        <label class="form-check-label" for="enableEdgeDensity">Edge Density</label>
                                    </div>
                                    <input type="number" step="0.01" min="0" max="1" class="form-control mt-1"
                                           v-model.number="threshold_edge_density" placeholder="Edge Density" :disabled="!enableEdgeDensity">
                                </div>
                                <div class="col">
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="checkbox" id="enableSkew" v-model="enableSkew">
                                        <label class="form-check-label" for="enableSkew">Skew (deg)</label>
                                    </div>
                                    <input type="number" step="0.01" min="0" max="10" class="form-control mt-1"
                                           v-model.number="threshold_residual_skew_angle" placeholder="Skew (deg)" :disabled="!enableSkew">
                                </div>
                            </div>
                            <div class="mt-2 d-flex gap-2">
                                <button class="btn btn-outline-secondary" @click="evaluateQuality">
                                    <i class="bi bi-bar-chart"></i> Valuta Qualità
                                </button>
                                <button class="btn btn-outline-danger" @click="stopProcessing" :disabled="!processing">
                                    <i class="bi bi-stop-circle"></i> Stop
                                </button>
                            </div>
                            <div v-if="qualityCheckResults.length > 0" class="mt-2">
                                <div class="alert alert-warning py-2 px-3">
                                    <strong>Immagini che NON rispettano le soglie:</strong>
                                    <ul class="mb-0">
                                        <li v-for="fail in qualityCheckResults" :key="fail.file">
                                            <span style="user-select:text">{{ fail.file.split('/').pop().replace(/\.json$/i, '') }}</span>
                                            <span class="text-danger">({{ fail.reasons.join(', ') }})</span>
                                            <ul class="small text-muted" style="margin-bottom:0;">
                                                <li v-for="d in fail.details" :key="d">{{ d }}</li>
                                            </ul>
                                        </li>
                                    </ul>
                                    <div v-if="qualityCheckReportPath" class="small text-muted mt-1">
                                        Report salvato in: <span style="user-select:text">{{ qualityCheckReportPath }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <!-- Espandibile: immagini già processate -->
                        <div class="accordion mt-4" id="processedAccordion">
                            <div class="accordion-item">
                                <h2 class="accordion-header" id="headingProcessed">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseProcessed" aria-expanded="false" aria-controls="collapseProcessed">
                                        Immagini già processate (anteprima)
                                    </button>
                                </h2>
                                <div id="collapseProcessed" class="accordion-collapse collapse" aria-labelledby="headingProcessed" data-bs-parent="#processedAccordion">
                                    <div class="accordion-body">
                                        <div v-if="thumbs.length > 0" class="d-flex flex-wrap justify-content-start align-items-start gap-2 mt-3">
                                            <div v-for="(thumb, idx) in thumbs" :key="thumb" class="thumbnail" style="margin: 5px;">
                                                <img :src="thumb" :alt="thumb" style="width: 120px; height: auto; border-radius: 4px; border: 1px solid #ccc; cursor: pointer;" @click="showPreview(thumb)">
                                                <div class="small text-break text-center">
                                                    <span style="user-select: text; cursor: text;">{{ getCleanFilename(thumb) }}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div v-else class="text-muted">Nessuna miniatura trovata.</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <!-- Fine espandibile -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Project1',
    data() {
        return {
            processing: false,
            inputDir: null,
            outputDir: null,
            borderPixels: '',
            imageFormat: 'tiff',
            useLzwCompression: true, // Default to true
            consoleLines: [],
            elaborazioneCompletata: false,
            thumbs: [],
            thumbsInterval: null,
            previewThumb: null,
            lastThumb: null,
            // Progress tracking
            progressInfo: null,
            progressInterval: null,
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
                if (thumbs.length > 0) {
                    // Sort thumbnails by modification time or name to get the most recent
                    thumbs.sort();

                    // Always show the last (most recent) thumbnail as lastThumb
                    this.lastThumb = thumbs[thumbs.length - 1];

                    // Keep all thumbnails except the last one for the gallery
                    this.thumbs = thumbs.slice(0, -1);
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
        async processImages() {
            window.electronAPI.logToMain('processImages chiamato dal renderer!');
            this.addConsoleLine(`Inizio a elaborare le immagini...`, 'info');
            if (!this.inputDir || !this.outputDir) return;
            this.processing = true;
            this.elaborazioneCompletata = false;
            this.thumbs = [];
            this.progressInfo = null;
            this.startThumbsPolling();
            this.startProgressPolling();
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
                // Add LZW compression parameter
                if (!this.useLzwCompression) {
                    args.push("--no-compression");
                    this.addConsoleLine(`Compressione LZW disabilitata`, 'info');
                } else {
                    this.addConsoleLine(`Compressione LZW abilitata per file TIFF`, 'info');
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
                this.stopProgressPolling();
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
            this.stopProgressPolling();
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
        getCleanFilename(thumb) {
            // Extract filename from path
            const filename = thumb.split('/').pop();
            // Remove timestamp prefix (pattern: timestamp_filename.jpg)
            const withoutTimestamp = filename.replace(/^\d+_/, '');
            // Remove extension
            const withoutExtension = withoutTimestamp.replace(/\.[^/.]+$/, '');
            return withoutExtension;
        },
    },
    mounted() {
        this.loadThumbs();
    },
    computed: {
        progressPercentage() {
            if (!this.progressInfo || !this.progressInfo.total_images) return 0;
            return Math.round((this.progressInfo.processed / this.progressInfo.total_images) * 100);
        }
    }
}
</script>