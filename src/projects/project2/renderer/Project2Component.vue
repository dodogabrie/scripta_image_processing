<!-- filepath: /home/edoardo/Work/Projects/scripta_image_processing/src/projects/project2/renderer/project2.template.html -->
<template>
    <div class="container-fluid mt-4">
        <div class="container-fluid mt-4">
            <div class="row">
                <div class="col-12">
                    <div
                        class="d-flex justify-content-between align-items-center mb-4"
                    >
                        <div>
                            <h1>Ritaglio doppia pagina</h1>
                            <p class="text-muted">
                                Ritaglia un doppio foglio A4 sulla piega e
                                aggiorna l'ordine delle pagine generate dal
                                ritaglio
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <!-- Input Section -->
                <div class="col-lg-6">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                Configurazione Input
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <button
                                    @click="selectInputDir"
                                    class="btn btn-primary w-100 mb-2"
                                >
                                    <i class="bi bi-folder2-open"></i> Scegli
                                    cartella di input
                                </button>
                                <div
                                    v-if="inputDir"
                                    class="alert alert-info py-2 px-3 mb-2"
                                >
                                    <strong>Input:</strong>
                                    <div class="small text-break">
                                        {{ inputDir }}
                                    </div>
                                </div>
                                <button
                                    @click="selectOutputDir"
                                    class="btn btn-secondary w-100 mb-2"
                                >
                                    <i class="bi bi-folder2-open"></i> Scegli
                                    cartella di output
                                </button>
                                <div
                                    v-if="outputDir"
                                    class="alert alert-info py-2 px-3"
                                >
                                    <strong>Output:</strong>
                                    <div class="small text-break">
                                        {{ outputDir }}
                                    </div>
                                </div>
                                <div v-if="!inputDir" class="text-muted mt-2">
                                    Nessuna cartella di input selezionata.
                                </div>
                                <div v-if="!outputDir" class="text-muted">
                                    Nessuna cartella di output selezionata.
                                </div>
                            </div>
                            <!-- Processing Parameters -->
                            <div class="mt-3">
                                <label for="contourBorder" class="form-label"
                                    >Border per correzione prospettiva
                                    (pixel):</label
                                >
                                <input
                                    id="contourBorder"
                                    type="number"
                                    class="form-control"
                                    v-model.number="contourBorder"
                                    min="0"
                                    max="500"
                                    placeholder="150"
                                />
                                <small class="form-text text-muted">
                                    Pixels di bordo per la correzione
                                    prospettiva del contorno. Default: 150
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
                            <div
                                v-if="!processing && !elaborazioneCompletata"
                                class="text-center text-muted py-5"
                            >
                                <i class="bi bi-image fs-1"></i>
                                <h5 class="mt-3">
                                    I risultati appariranno qui
                                </h5>
                                <p>
                                    Seleziona le cartelle e clicca "Elabora" per
                                    processare
                                </p>
                            </div>

                            <!-- Enhanced progress display during processing -->
                            <div v-else-if="processing" class="py-4">
                                <!-- Main progress bar -->
                                <div v-if="progressInfo" class="mb-4">
                                    <div
                                        class="d-flex justify-content-between align-items-center mb-2"
                                    >
                                        <h6 class="mb-0">Progresso Generale</h6>
                                        <small class="text-muted"
                                            >{{ progressPercentage }}%</small
                                        >
                                    </div>
                                    <div
                                        class="progress mb-3"
                                        style="height: 24px"
                                    >
                                        <div
                                            class="progress-bar progress-bar-striped progress-bar-animated"
                                            role="progressbar"
                                            :style="{
                                                width: progressPercentage + '%',
                                            }"
                                            :aria-valuenow="
                                                progressInfo.processed
                                            "
                                            :aria-valuemin="0"
                                            :aria-valuemax="
                                                progressInfo.total_images
                                            "
                                        >
                                            {{ progressInfo.processed }} /
                                            {{ progressInfo.total_images }}
                                        </div>
                                    </div>
                                </div>

                                <!-- Current file and stage -->
                                <div
                                    v-if="realTimeProgress.current_file"
                                    class="mb-3"
                                >
                                    <div class="d-flex align-items-center mb-2">
                                        <div
                                            class="spinner-border spinner-border-sm text-primary me-2"
                                            role="status"
                                        ></div>
                                        <strong class="me-2"
                                            >File corrente:</strong
                                        >
                                        <code class="text-primary">{{
                                            realTimeProgress.current_file
                                        }}</code>
                                    </div>
                                    <div
                                        v-if="realTimeProgress.current_stage"
                                        class="small text-muted ms-4"
                                    >
                                        {{ realTimeProgress.current_stage }}
                                    </div>
                                </div>

                                <!-- Processing statistics -->
                                <div class="row text-center mb-3">
                                    <div class="col-md-3">
                                        <div class="small text-muted">
                                            Con Piega
                                        </div>
                                        <div class="h6 text-success">
                                            {{
                                                realTimeProgress.fold_detected_count
                                            }}
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="small text-muted">
                                            Senza Piega
                                        </div>
                                        <div class="h6 text-info">
                                            {{ realTimeProgress.no_fold_count }}
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="small text-muted">
                                            File Salvati
                                        </div>
                                        <div class="h6 text-primary">
                                            {{ realTimeProgress.files_renamed }}
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div
                                            class="small text-muted"
                                            v-if="progressInfo"
                                        >
                                            Dimensione
                                        </div>
                                        <div
                                            class="h6 text-secondary"
                                            v-if="progressInfo"
                                        >
                                            {{ progressInfo.total_size_gb }} GB
                                        </div>
                                    </div>
                                </div>

                                <!-- Speed and time estimates -->
                                <div
                                    v-if="
                                        processingSpeed ||
                                        estimatedTimeRemaining
                                    "
                                    class="text-center"
                                >
                                    <div class="row">
                                        <div
                                            class="col-md-6"
                                            v-if="processingSpeed"
                                        >
                                            <small class="text-muted"
                                                >Velocità:
                                                {{ processingSpeed }}</small
                                            >
                                        </div>
                                        <div
                                            class="col-md-6"
                                            v-if="estimatedTimeRemaining"
                                        >
                                            <small class="text-muted">{{
                                                estimatedTimeRemaining
                                            }}</small>
                                        </div>
                                    </div>
                                </div>

                                <!-- Fallback for initial state -->
                                <div v-else class="text-center">
                                    <div
                                        class="spinner-border text-primary mb-3"
                                        role="status"
                                    >
                                        <span class="visually-hidden"
                                            >Elaborazione...</span
                                        >
                                    </div>
                                    <h5 class="text-muted">
                                        {{
                                            realTimeProgress.current_stage ||
                                            "Avvio elaborazione..."
                                        }}
                                    </h5>
                                </div>
                            </div>

                            <!-- Completion summary with detailed statistics -->
                            <div v-else-if="elaborazioneCompletata" class="">
                                <div class="alert alert-success py-3 px-3 mb-3">
                                    <h5 class="alert-heading mb-2">
                                        <i class="bi bi-check-circle"></i>
                                        Elaborazione Completata!
                                    </h5>
                                    <p class="mb-1">Risultati salvati in:</p>
                                    <div
                                        class="small text-break font-monospace bg-light p-2 rounded"
                                    >
                                        {{ outputDir }}
                                    </div>
                                </div>

                                <!-- Processing summary -->
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">
                                            <i class="bi bi-graph-up"></i>
                                            Resoconto Elaborazione
                                        </h6>
                                    </div>
                                    <div class="card-body">
                                        <!-- Main statistics -->
                                        <div class="row mb-3">
                                            <div
                                                class="col-md-6"
                                                v-if="progressInfo"
                                            >
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Immagini totali:</span
                                                    >
                                                    <strong>{{
                                                        progressInfo.total_images
                                                    }}</strong>
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Elaborate con
                                                        successo:</span
                                                    >
                                                    <strong
                                                        class="text-success"
                                                        >{{
                                                            progressInfo.summary
                                                                ?.processed_successfully ||
                                                            progressInfo.processed
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                    v-if="
                                                        progressInfo.summary
                                                            ?.errors > 0
                                                    "
                                                >
                                                    <span>Errori:</span>
                                                    <strong
                                                        class="text-danger"
                                                        >{{
                                                            progressInfo.summary
                                                                .errors
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                    v-if="
                                                        progressInfo.summary
                                                            ?.success_rate
                                                    "
                                                >
                                                    <span
                                                        >Tasso di
                                                        successo:</span
                                                    >
                                                    <strong
                                                        >{{
                                                            progressInfo.summary
                                                                .success_rate
                                                        }}%</strong
                                                    >
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Con piega
                                                        rilevata:</span
                                                    >
                                                    <strong
                                                        class="text-success"
                                                        >{{
                                                            realTimeProgress.fold_detected_count
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span>Senza piega:</span>
                                                    <strong class="text-info">{{
                                                        realTimeProgress.no_fold_count
                                                    }}</strong>
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >File salvati
                                                        totali:</span
                                                    >
                                                    <strong
                                                        class="text-primary"
                                                        >{{
                                                            realTimeProgress.files_renamed
                                                        }}</strong
                                                    >
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Technical details -->
                                        <div class="row" v-if="progressInfo">
                                            <div class="col-md-6">
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Formato
                                                        principale:</span
                                                    >
                                                    <span
                                                        class="badge bg-secondary"
                                                        >{{
                                                            progressInfo.primary_format
                                                        }}</span
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Dimensione
                                                        totale:</span
                                                    >
                                                    <span
                                                        >{{
                                                            progressInfo.total_size_gb
                                                        }}
                                                        GB</span
                                                    >
                                                </div>
                                            </div>
                                            <div
                                                class="col-md-6"
                                                v-if="
                                                    progressInfo.duration_seconds
                                                "
                                            >
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Tempo di
                                                        elaborazione:</span
                                                    >
                                                    <span>{{
                                                        formatDuration(
                                                            progressInfo.duration_seconds,
                                                        )
                                                    }}</span>
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                    v-if="processingSpeed"
                                                >
                                                    <span>Velocità media:</span>
                                                    <span>{{
                                                        processingSpeed
                                                    }}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Error details if any -->
                                        <div
                                            v-if="
                                                progressInfo?.summary?.errors >
                                                0
                                            "
                                            class="mt-3"
                                        >
                                            <div
                                                class="alert alert-warning py-2"
                                            >
                                                <strong
                                                    ><i
                                                        class="bi bi-exclamation-triangle"
                                                    ></i>
                                                    Attenzione:</strong
                                                >
                                                {{
                                                    progressInfo.summary.errors
                                                }}
                                                immagini non sono state
                                                elaborate correttamente.
                                                Controlla i log nella console
                                                per dettagli.
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer" v-if="inputDir && outputDir">
                            <button
                                @click="processData"
                                :disabled="
                                    processing || !inputDir || !outputDir
                                "
                                class="btn btn-primary w-100"
                            >
                                <span
                                    v-if="processing"
                                    class="spinner-border spinner-border-sm me-2"
                                ></span>
                                <i v-else class="bi bi-gear"></i>
                                {{ processing ? "Elaborazione..." : "Elabora" }}
                            </button>
                            <button
                                class="btn btn-outline-danger w-100 mt-2"
                                @click="stopProcessing"
                                :disabled="!processing"
                            >
                                <i class="bi bi-stop-circle"></i> Stop
                            </button>
                        </div>
                        <!-- Console output -->
                        <div class="mt-3">
                            <h6 class="text-muted mb-1">
                                <i class="bi bi-terminal"></i> Console
                            </h6>
                            <div
                                style="
                                    background: #222;
                                    color: #eee;
                                    padding: 10px;
                                    border-radius: 6px;
                                    min-height: 80px;
                                    max-height: 180px;
                                    overflow: auto;
                                    font-size: 13px;
                                    font-family: monospace;
                                "
                                id="console-output"
                            >
                                <div
                                    v-for="(line, idx) in consoleLines"
                                    :key="idx"
                                    :style="{
                                        color:
                                            line.type === 'error'
                                                ? '#ff6b6b'
                                                : line.type === 'success'
                                                  ? '#51cf66'
                                                  : '#eee',
                                    }"
                                >
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
    name: "project2",
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
            // Enhanced real-time progress tracking
            realTimeProgress: {
                current_file: null,
                current_stage: null,
                fold_detected_count: 0,
                no_fold_count: 0,
                files_renamed: 0,
                processing_start_time: null,
                last_processed_time: null,
            },
            // Processing parameters
            contourBorder: 150, // Default border for contour detection
            // Real-time output
            outputUnsubscribe: null, // Function to unsubscribe from Python output
        };
    },
    computed: {
        progressPercentage() {
            if (!this.progressInfo || !this.progressInfo.total_images) return 0;
            return Math.round(
                (this.progressInfo.processed / this.progressInfo.total_images) *
                    100,
            );
        },
        processingSpeed() {
            if (
                !this.realTimeProgress.processing_start_time ||
                !this.progressInfo ||
                this.progressInfo.processed <= 0
            ) {
                return null;
            }
            const elapsed =
                (Date.now() - this.realTimeProgress.processing_start_time) /
                1000; // seconds
            const speed = (this.progressInfo.processed / elapsed) * 60; // files per minute
            return speed > 1
                ? `${speed.toFixed(1)} file/min`
                : `${(speed * 60).toFixed(1)} file/ora`;
        },
        estimatedTimeRemaining() {
            if (
                !this.realTimeProgress.processing_start_time ||
                !this.progressInfo ||
                this.progressInfo.processed <= 0
            ) {
                return null;
            }
            const elapsed =
                (Date.now() - this.realTimeProgress.processing_start_time) /
                1000;
            const remaining =
                this.progressInfo.total_images - this.progressInfo.processed;
            const avgTimePerFile = elapsed / this.progressInfo.processed;
            const remainingSeconds = remaining * avgTimePerFile;

            if (remainingSeconds < 60)
                return `${Math.round(remainingSeconds)}s rimanenti`;
            if (remainingSeconds < 3600)
                return `${Math.round(remainingSeconds / 60)}min rimanenti`;
            return `${Math.round(remainingSeconds / 3600)}h rimanenti`;
        },
        totalFilesProcessed() {
            return (
                this.realTimeProgress.fold_detected_count +
                this.realTimeProgress.no_fold_count
            );
        },
    },
    methods: {
        addConsoleLine(text, type = "normal") {
            this.consoleLines.push({ text, type });
            if (this.consoleLines.length > 100) this.consoleLines.shift();
            this.$nextTick(() => {
                const el = document.getElementById("console-output");
                if (el) el.scrollTop = el.scrollHeight;
            });
        },
        parseProgressInfo(line) {
            // Parse current file being processed: [4/8] Processing: filename
            const processingMatch = line.match(
                /\[(\d+)\/(\d+)\] Processing: (.+)/,
            );
            if (processingMatch) {
                this.realTimeProgress.current_file = processingMatch[3];
                this.realTimeProgress.current_stage =
                    "Elaborazione immagine...";
                this.realTimeProgress.last_processed_time = Date.now();
                return;
            }

            // Parse front-back couple processing: [1/5] Processing couple: file1.tif + file2.tif
            const coupleMatch = line.match(
                /\[(\d+)\/(\d+)\] Processing couple: (.+) \+ (.+)/,
            );
            if (coupleMatch) {
                this.realTimeProgress.current_file = `${coupleMatch[3]} + ${coupleMatch[4]}`;
                this.realTimeProgress.current_stage =
                    "Elaborazione coppia front-back...";
                this.realTimeProgress.last_processed_time = Date.now();
                return;
            }

            // Parse couple success results - formato: [OK] Couple processed successfully - N files renamed
            const coupleSuccessMatch = line.match(
                /\s*\[OK\] Couple processed successfully - (\d+) files renamed/,
            );
            if (coupleSuccessMatch) {
                const filesRenamed = parseInt(coupleSuccessMatch[1]);
                // Don't update fold_detected_count here - already counted in Phase 1
                this.realTimeProgress.files_renamed += filesRenamed;
                this.realTimeProgress.current_stage = `Coppia completata: ${filesRenamed} file salvati`;
                return;
            }

            // Parse single image success - formato: [OK] Only first image cropped - N files renamed to _4/_1 pattern
            const singleSuccessMatch = line.match(
                /\s*\[OK\] Only first image cropped - (\d+) files renamed to _4\/_1 pattern/,
            );
            if (singleSuccessMatch) {
                const filesRenamed = parseInt(singleSuccessMatch[1]);
                // Don't update fold_detected_count here - already counted in Phase 1
                this.realTimeProgress.files_renamed += filesRenamed;
                this.realTimeProgress.current_stage = `Immagine singola elaborata: ${filesRenamed} file salvati`;
                return;
            }

            // Parse old format fold detection results - formato: [OK] fold_status, N files renamed
            const foldMatch = line.match(
                /\s*\[OK\] (fold detected|no fold), (\d+) files renamed/,
            );
            if (foldMatch) {
                const foldDetected = foldMatch[1] === "fold detected";
                const filesRenamed = parseInt(foldMatch[2]);

                // Update counters in Phase 1 for real-time display
                if (foldDetected) {
                    this.realTimeProgress.fold_detected_count++;
                } else {
                    this.realTimeProgress.no_fold_count++;
                    // Only count files_renamed for "no fold" - fold files will be counted in Phase 3-4
                    this.realTimeProgress.files_renamed += filesRenamed;
                }
                this.realTimeProgress.current_stage = `Completato processing`;
                return;
            }

            // Parse couple validation errors - formato: [ERROR] Couple validation failed - crops undone
            if (line.includes("[ERROR] Couple validation failed")) {
                this.realTimeProgress.current_stage = "Errore validazione coppia";
                return;
            }

            // Parse info messages about second image
            if (line.includes("[INFO] Second image had no fold detection")) {
                this.realTimeProgress.current_stage = "Seconda immagine senza piega";
                return;
            }

            // Parse processing stages
            if (line.includes("Kernel size:")) {
                this.realTimeProgress.current_stage = "Rilevamento contorni...";
            } else if (line.includes("Inclinazione")) {
                this.realTimeProgress.current_stage =
                    "Correzione prospettiva...";
            } else if (line.includes("Successfully saved")) {
                this.realTimeProgress.current_stage = "Salvataggio file...";
            } else if (line.includes("Renamed with metadata")) {
                this.realTimeProgress.current_stage = "Rinominazione ICCD...";
            }
        },
        formatDuration(seconds) {
            if (seconds < 60) return `${seconds.toFixed(1)}s`;
            if (seconds < 3600)
                return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        },
        async selectInputDir() {
            this.addConsoleLine("Selezione cartella di input...", "info");
            if (!window.electronAPI || !window.electronAPI.selectDirectory) {
                this.addConsoleLine(
                    "electronAPI.selectDirectory non disponibile",
                    "error",
                );
                return;
            }
            const dir = await window.electronAPI.selectDirectory();
            if (dir) {
                this.inputDir = dir;
                this.elaborazioneCompletata = false;
                this.addConsoleLine(
                    "Cartella input selezionata: " + dir,
                    "success",
                );
            } else {
                this.addConsoleLine(
                    "Selezione cartella input annullata.",
                    "warning",
                );
            }
        },
        async selectOutputDir() {
            this.addConsoleLine("Selezione cartella di output...", "info");
            if (!window.electronAPI || !window.electronAPI.selectDirectory) {
                this.addConsoleLine(
                    "electronAPI.selectDirectory non disponibile",
                    "error",
                );
                return;
            }
            const dir = await window.electronAPI.selectDirectory();
            if (dir) {
                this.outputDir = dir;
                this.elaborazioneCompletata = false;
                this.addConsoleLine(
                    "Cartella output selezionata: " + dir,
                    "success",
                );
            } else {
                this.addConsoleLine(
                    "Selezione cartella output annullata.",
                    "warning",
                );
            }
        },
        async loadProgress() {
            if (
                window.electronAPI &&
                window.electronAPI.readFile &&
                this.outputDir
            ) {
                try {
                    const infoPath = this.outputDir + "/info.json";
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
            this.addConsoleLine("Inizio elaborazione...", "info");
            if (!this.inputDir || !this.outputDir) return;

            this.processing = true;
            this.elaborazioneCompletata = false;
            this.progressInfo = null;

            // Initialize real-time progress tracking
            this.realTimeProgress = {
                current_file: null,
                current_stage: "Inizializzazione...",
                fold_detected_count: 0,
                no_fold_count: 0,
                files_renamed: 0,
                processing_start_time: Date.now(),
                last_processed_time: null,
            };

            this.startProgressPolling();

            this.addConsoleLine(`Input: ${this.inputDir}`, "info");
            this.addConsoleLine(`Output: ${this.outputDir}`, "info");

            try {
                // Costruisci gli argomenti per lo script Python
                const args = [this.inputDir, this.outputDir];

                // Aggiungi contour_border parameter
                args.push("--contour_border", this.contourBorder.toString());
                this.addConsoleLine(
                    `Border correzione prospettiva: ${this.contourBorder} pixel`,
                    "info",
                );

                // Always enable verbose to capture output
                args.push("--verbose");
                args.push("--front-back-couple");

                this.addConsoleLine(
                    "Utilizzo impostazioni di default per tutti gli altri parametri",
                    "info",
                );

                // Set up real-time output listener with progress parsing
                if (window.electronAPI.onPythonOutput) {
                    this.outputUnsubscribe = window.electronAPI.onPythonOutput(
                        (data) => {
                            if (
                                data.type === "stdout" ||
                                data.type === "stderr"
                            ) {
                                const lines = data.data.toString().split("\n");
                                lines.forEach((line) => {
                                    if (line.trim()) {
                                        this.addConsoleLine(
                                            line.trim(),
                                            data.type === "stderr"
                                                ? "error"
                                                : "normal",
                                        );
                                        this.parseProgressInfo(line.trim());
                                    }
                                });
                            }
                        },
                    );
                }

                const result =
                    await window.electronAPI.runProjectScriptStreaming(
                        "project2",
                        "main.py",
                        args,
                    );

                if (result.success) {
                    this.addConsoleLine(
                        "Elaborazione completata con successo!",
                        "success",
                    );
                    this.elaborazioneCompletata = true;
                } else {
                    this.addConsoleLine(
                        "Errore durante l'elaborazione: " + result.error,
                        "error",
                    );
                    this.elaborazioneCompletata = false;
                }
            } catch (error) {
                this.addConsoleLine("Errore JS: " + error.message, "error");
                this.elaborazioneCompletata = false;
            } finally {
                // Clean up output listener
                if (this.outputUnsubscribe) {
                    this.outputUnsubscribe();
                    this.outputUnsubscribe = null;
                }
                this.processing = false;
                this.stopProgressPolling();
                this.loadProgress();
            }
        },
        async stopProcessing() {
            try {
                if (
                    window.electronAPI &&
                    typeof window.electronAPI.stopPythonProcess === "function"
                ) {
                    await window.electronAPI.stopPythonProcess();
                    this.addConsoleLine("Processo terminato.", "warning");
                }
            } catch (e) {
                this.addConsoleLine(
                    "Errore durante lo stop: " + e.message,
                    "error",
                );
            }
            // Clean up output listener
            if (this.outputUnsubscribe) {
                this.outputUnsubscribe();
                this.outputUnsubscribe = null;
            }
            this.processing = false;
        },
        goBack() {
            this.$emit("goBack");
        },
    },
    mounted() {
        // Initialize component
    },
    beforeUnmount() {
        // Clean up any active listeners
        if (this.outputUnsubscribe) {
            this.outputUnsubscribe();
            this.outputUnsubscribe = null;
        }
    },
};
</script>
