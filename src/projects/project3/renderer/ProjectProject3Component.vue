<template>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <div
                    class="d-flex justify-content-between align-items-center mb-4"
                >
                    <div>
                        <h1>MAGLIB XML Processing Tool</h1>
                        <p class="text-muted">
                            Tool per elaborazione XML MAG con supporto per tutti
                            i comandi disponibili
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Configuration Section -->
            <div class="col-lg-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Configurazione</h5>
                    </div>
                    <div class="card-body">
                        <!-- Directory Selection -->
                        <div class="mb-4">
                            <button
                                @click="selectInputDir"
                                class="btn btn-primary w-100 mb-2"
                            >
                                <i class="bi bi-folder2-open"></i> Scegli
                                cartella XML
                            </button>
                            <div
                                v-if="inputDir"
                                class="alert alert-info py-2 px-3"
                            >
                                <strong>Directory XML:</strong>
                                <div class="small text-break">
                                    {{ inputDir }}
                                </div>
                            </div>
                            <div v-if="!inputDir" class="text-muted mt-2">
                                Seleziona la cartella contenente i file XML da
                                processare.
                            </div>
                        </div>

                        <!-- Command Selection -->
                        <div class="mb-4">
                            <label for="commandSelect" class="form-label">
                                <strong>Comando da eseguire:</strong>
                            </label>
                            <select
                                id="commandSelect"
                                class="form-select mb-3"
                                v-model="selectedCommand"
                            >
                                <option value="">
                                    -- Seleziona un comando --
                                </option>
                                <optgroup
                                    v-for="(
                                        commands, category
                                    ) in groupedCommands"
                                    :key="category"
                                    :label="category"
                                >
                                    <option
                                        v-for="(command, key) in commands"
                                        :key="key"
                                        :value="key"
                                    >
                                        {{
                                            command.name || command.description
                                        }}
                                    </option>
                                </optgroup>
                            </select>

                            <!-- Active Command Display -->
                            <div
                                v-if="selectedCommand"
                                class="card border-success"
                            >
                                <div class="card-header bg-light-success">
                                    <h6 class="mb-0 text-success">
                                        <i class="bi bi-check-circle"></i>
                                        Comando Attivo
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <small class="text-muted"
                                                >Script:</small
                                            >
                                            <div class="fw-bold">
                                                {{
                                                    availableCommands[
                                                        selectedCommand
                                                    ].script
                                                }}
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <small class="text-muted"
                                                >Categoria:</small
                                            >
                                            <span class="badge bg-secondary">{{
                                                availableCommands[
                                                    selectedCommand
                                                ].category
                                            }}</span>
                                        </div>
                                        <div class="col-md-4">
                                            <small class="text-muted"
                                                >Comando:</small
                                            >
                                            <div class="fw-bold text-primary">
                                                {{ selectedCommand }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <small class="text-muted"
                                            >Descrizione:</small
                                        >
                                        <div>
                                            {{
                                                availableCommands[
                                                    selectedCommand
                                                ].description
                                            }}
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <small class="text-muted"
                                            >Parametri:</small
                                        >
                                        <code
                                            class="d-block bg-light p-2 rounded small"
                                        >
                                            {{
                                                formatCommandParams(
                                                    availableCommands[
                                                        selectedCommand
                                                    ],
                                                )
                                            }}
                                        </code>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Options -->
                        <div class="mb-3">
                            <div class="form-check">
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    v-model="dryRun"
                                    id="dryRunCheck"
                                />
                                <label
                                    class="form-check-label"
                                    for="dryRunCheck"
                                >
                                    <strong>Dry Run</strong> - Solo anteprima,
                                    non eseguire
                                </label>
                                <div class="form-text">
                                    Mostra solo cosa verrebbe eseguito senza
                                    effettuare modifiche
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Action Button -->
                    <div class="card-footer">
                        <button
                            @click="processData"
                            :disabled="
                                processing || !inputDir || !selectedCommand
                            "
                            class="btn btn-success w-100"
                        >
                            <span
                                v-if="processing"
                                class="spinner-border spinner-border-sm me-2"
                            ></span>
                            <i v-else class="bi bi-play-circle"></i>
                            {{
                                processing
                                    ? "Elaborazione..."
                                    : dryRun
                                      ? "Anteprima Comandi"
                                      : "Esegui Comando"
                            }}
                        </button>
                        <button
                            class="btn btn-outline-danger w-100 mt-2"
                            @click="stopProcessing"
                            :disabled="!processing"
                        >
                            <i class="bi bi-stop-circle"></i> Stop
                        </button>
                    </div>
                </div>
            </div>

            <!-- Results Section -->
            <div class="col-lg-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Risultati e Output</h5>
                    </div>
                    <div class="card-body position-relative">
                        <!-- Idle State -->
                        <div
                            v-if="!processing && !elaborazioneCompletata"
                            class="text-center text-muted py-5"
                        >
                            <i class="bi bi-file-earmark-code fs-1"></i>
                            <h5 class="mt-3">
                                Output del comando apparirà qui
                            </h5>
                            <p>
                                Seleziona cartella XML e comando, poi clicca
                                "Esegui"
                            </p>
                        </div>

                        <!-- Processing State -->
                        <div v-else-if="processing" class="py-4">
                            <div class="text-center mb-4">
                                <div
                                    class="spinner-border text-primary mb-3"
                                    role="status"
                                >
                                    <span class="visually-hidden"
                                        >Elaborazione...</span
                                    >
                                </div>
                                <h5 class="text-muted">
                                    {{ currentProcessingStage }}
                                </h5>
                                <div
                                    v-if="xmlFilesFound > 0"
                                    class="small text-muted"
                                >
                                    Trovati {{ xmlFilesFound }} file XML da
                                    processare
                                </div>
                            </div>

                            <!-- Progress Summary -->
                            <div
                                v-if="processingSummary.totalProcessed > 0"
                                class="row text-center mb-3"
                            >
                                <div class="col-md-4">
                                    <div class="small text-muted">
                                        Processati
                                    </div>
                                    <div class="h6 text-success">
                                        {{ processingSummary.successful }}
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="small text-muted">Errori</div>
                                    <div class="h6 text-danger">
                                        {{ processingSummary.errors }}
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="small text-muted">Totale</div>
                                    <div class="h6 text-primary">
                                        {{ processingSummary.totalProcessed }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Completion State -->
                        <div v-else-if="elaborazioneCompletata" class="">
                            <div class="alert alert-success py-3 px-3 mb-3">
                                <h5 class="alert-heading mb-2">
                                    <i class="bi bi-check-circle"></i>
                                    Elaborazione Completata!
                                </h5>
                                <p class="mb-1">
                                    Comando eseguito su {{ xmlFilesFound }} file
                                    XML
                                </p>
                                <div
                                    v-if="processingSummary.totalProcessed > 0"
                                    class="small"
                                >
                                    Successi:
                                    {{ processingSummary.successful }}, Errori:
                                    {{ processingSummary.errors }}
                                </div>
                            </div>

                            <!-- Processing Summary Card -->
                            <div
                                class="card"
                                v-if="processingSummary.totalProcessed > 0"
                            >
                                <div class="card-header">
                                    <h6 class="mb-0">
                                        <i class="bi bi-graph-up"></i> Resoconto
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div
                                                class="d-flex justify-content-between"
                                            >
                                                <span>File XML trovati:</span>
                                                <strong>{{
                                                    xmlFilesFound
                                                }}</strong>
                                            </div>
                                            <div
                                                class="d-flex justify-content-between"
                                            >
                                                <span
                                                    >Processati con
                                                    successo:</span
                                                >
                                                <strong class="text-success">{{
                                                    processingSummary.successful
                                                }}</strong>
                                            </div>
                                            <div
                                                class="d-flex justify-content-between"
                                            >
                                                <span>Errori:</span>
                                                <strong class="text-danger">{{
                                                    processingSummary.errors
                                                }}</strong>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div
                                                class="d-flex justify-content-between"
                                            >
                                                <span>Tasso di successo:</span>
                                                <strong
                                                    >{{ successRate }}%</strong
                                                >
                                            </div>
                                            <div
                                                class="d-flex justify-content-between"
                                            >
                                                <span>Comando eseguito:</span>
                                                <code>{{
                                                    selectedCommand
                                                }}</code>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Console Output -->
                    <div class="card-footer">
                        <h6 class="text-muted mb-2">
                            <i class="bi bi-terminal"></i> Console Output
                        </h6>
                        <div
                            style="
                                background: #222;
                                color: #eee;
                                padding: 10px;
                                border-radius: 6px;
                                min-height: 120px;
                                max-height: 300px;
                                overflow: auto;
                                font-size: 12px;
                                font-family: monospace;
                            "
                            id="console-output"
                        >
                            <div
                                v-for="(line, idx) in consoleLines"
                                :key="idx"
                                :style="{ color: getLineColor(line.type) }"
                            >
                                {{ line.text }}
                            </div>
                            <div
                                v-if="consoleLines.length === 0"
                                class="text-muted text-center py-3"
                            >
                                Output dei comandi apparirà qui...
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
    name: "ProjectProject3Component",
    data() {
        return {
            inputDir: null,
            selectedCommand: "",
            processing: false,
            elaborazioneCompletata: false,
            dryRun: false,
            consoleLines: [],
            xmlFilesFound: 0,
            currentProcessingStage: "Inizializzazione...",
            processingSummary: {
                totalProcessed: 0,
                successful: 0,
                errors: 0,
            },
            outputUnsubscribe: null,

            // Available commands (loaded from JSON config)
            availableCommands: {},
            commandsLoaded: false,
        };
    },
    computed: {
        groupedCommands() {
            const groups = {};
            Object.entries(this.availableCommands).forEach(([key, command]) => {
                if (!groups[command.category]) {
                    groups[command.category] = {};
                }
                groups[command.category][key] = command;
            });
            return groups;
        },
        successRate() {
            if (this.processingSummary.totalProcessed === 0) return 0;
            return Math.round(
                (this.processingSummary.successful /
                    this.processingSummary.totalProcessed) *
                    100,
            );
        },
    },
    methods: {
        async loadCommandsConfig() {
            try {
                // Get commands configuration from Python backend
                if (window.electronAPI && window.electronAPI.runProjectScript) {
                    this.addConsoleLine(
                        "Caricamento configurazione comandi da backend...",
                        "info",
                    );

                    const result = await window.electronAPI.runProjectScript(
                        "project3",
                        "main.py",
                        ["--export-json"],
                    );

                    if (result.success && result.output) {
                        try {
                            const config = JSON.parse(result.scriptOutput);
                            if (config.error) {
                                throw new Error(config.error);
                            }
                            this.availableCommands = config.commands;
                            this.commandsLoaded = true;
                            this.addConsoleLine(
                                `Configurazione caricata dal backend Python`,
                                "success",
                            );
                            this.addConsoleLine(
                                `Trovati ${Object.keys(config.commands).length} comandi disponibili`,
                                "info",
                            );
                        } catch (parseError) {
                            throw new Error(
                                `Errore parsing JSON dal backend: ${parseError.message}`,
                            );
                        }
                    } else {
                        throw new Error(
                            `Backend error: ${result.error || "Unknown error"}`,
                        );
                    }
                } else {
                    this.addConsoleLine(
                        "electronAPI.runProjectScript non disponibile, uso configurazione predefinita",
                        "warning",
                    );
                    this.loadFallbackCommands();
                }
            } catch (error) {
                this.addConsoleLine(
                    `Errore caricamento configurazione: ${error.message}`,
                    "error",
                );
                this.addConsoleLine(
                    "Uso configurazione predefinita",
                    "warning",
                );
                this.loadFallbackCommands();
            }
        },
        loadFallbackCommands() {
            // Extended fallback commands if JSON config fails to load
            this.availableCommands = {
                adapt_fs_iccd: {
                    script: "adapt_fs_iccd.py",
                    name: "Adatta FS ICCD",
                    description: "Adatta file system per standard ICCD",
                    category: "File System",
                    base_params: ["-M", "{file}"],
                    required_params: ["--ignore-missing"],
                    configurable_params: {},
                    usage_pattern: "mass_mode",
                },
                adapt_fs_iccu: {
                    script: "adapt_fs_iccu.py",
                    name: "Adatta FS ICCU",
                    description:
                        "Adatta file system per standard ICCU (stile fascicolo)",
                    category: "File System",
                    base_params: ["-M", "{file}"],
                    required_params: [
                        "--path-style=fascicle",
                        "--ignore-missing",
                    ],
                    configurable_params: {},
                    usage_pattern: "mass_mode",
                },
                adapt_fs_salvemini: {
                    script: "adapt_fs_salvemini.py",
                    name: "Adatta FS Salvemini",
                    description: "Adatta file system per archivio Salvemini",
                    category: "File System",
                    base_params: ["-M", "{file}"],
                    required_params: ["--ignore-missing"],
                    configurable_params: {},
                    usage_pattern: "mass_mode",
                },
                add_imgs: {
                    script: "add_imgs.py",
                    name: "Aggiungi immagini standard",
                    description: "Aggiunge riferimenti per immagini standard",
                    category: "Elaborazione Immagini",
                    base_params: ["-i", "{file}", "-o", "{file}"],
                    required_params: [],
                    configurable_params: {},
                    usage_pattern: "standard",
                },
                add_bib_from_csv: {
                    script: "add_bib_from_csv.py",
                    name: "Aggiungi bibliografia da CSV",
                    description: "Aggiunge dati bibliografici da file CSV",
                    category: "Metadati",
                    base_params: ["-i", "{file}", "-o", "{file}"],
                    required_params: ["-I", "-f"],
                    configurable_params: {
                        csv_file: {
                            param: "-I",
                            description: "File CSV con dati bibliografici",
                            default: "C:/opt/abana.csv",
                            type: "file",
                        },
                        identifier_field: {
                            param: "-f",
                            description: "Campo identificatore nel CSV",
                            default: "dirname",
                            type: "string",
                        },
                    },
                    usage_pattern: "standard",
                },
                set_sequence_numbers: {
                    script: "set_sequence_numbers.py",
                    name: "Imposta numeri sequenza",
                    description: "Imposta i numeri di sequenza nei file XML",
                    category: "Sequenziamento",
                    base_params: ["-i", "{file}", "-o", "{file}"],
                    required_params: [],
                    configurable_params: {},
                    usage_pattern: "standard",
                },
            };
            this.commandsLoaded = true;
        },
        formatCommandParams(command) {
            // Format parameters for display based on new JSON structure
            const params = [];

            // Add base parameters
            if (command.base_params) {
                params.push(...command.base_params);
            }

            // Add required parameters
            if (command.required_params) {
                params.push(...command.required_params);
            }

            // Add configurable parameters
            if (command.configurable_params) {
                Object.values(command.configurable_params).forEach((param) => {
                    if (param.default) {
                        if (
                            param.type === "boolean" &&
                            param.default === true
                        ) {
                            params.push(param.param);
                        } else if (param.type !== "boolean") {
                            params.push(param.param, param.default);
                        }
                    }
                });
            }

            return params.join(" ");
        },
        addConsoleLine(text, type = "normal") {
            this.consoleLines.push({ text, type });
            if (this.consoleLines.length > 200) this.consoleLines.shift();
            this.$nextTick(() => {
                const el = document.getElementById("console-output");
                if (el) el.scrollTop = el.scrollHeight;
            });
        },
        getLineColor(type) {
            switch (type) {
                case "error":
                    return "#ff6b6b";
                case "success":
                    return "#51cf66";
                case "info":
                    return "#74c0fc";
                case "warning":
                    return "#ffd43b";
                default:
                    return "#eee";
            }
        },
        parseProgressInfo(line) {
            // Parse various status messages from Python output
            if (line.includes("Found") && line.includes("XML files")) {
                const match = line.match(/Found (\d+) XML files/);
                if (match) {
                    this.xmlFilesFound = parseInt(match[1]);
                    this.currentProcessingStage = `Trovati ${this.xmlFilesFound} file XML`;
                }
            } else if (line.includes("Processing:")) {
                const match = line.match(/\[(\d+)\/(\d+)\] Processing: (.+)/);
                if (match) {
                    this.currentProcessingStage = `Processando ${match[3]} (${match[1]}/${match[2]})`;
                }
            } else if (line.includes("Successfully processed")) {
                this.processingSummary.successful++;
                this.processingSummary.totalProcessed++;
            } else if (
                line.includes("Error processing") ||
                line.includes("FAILED")
            ) {
                this.processingSummary.errors++;
                this.processingSummary.totalProcessed++;
            } else if (line.includes("PROCESSING SUMMARY")) {
                this.currentProcessingStage = "Generando resoconto finale...";
            } else if (line.includes("Setup")) {
                this.currentProcessingStage =
                    "Configurazione ambiente maglib...";
            } else if (line.includes("DRY RUN")) {
                this.currentProcessingStage = "Anteprima comandi (Dry Run)...";
            }
        },
        async selectInputDir() {
            this.addConsoleLine("Selezione cartella XML...", "info");
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
                    "Cartella XML selezionata: " + dir,
                    "success",
                );
            } else {
                this.addConsoleLine("Selezione cartella annullata.", "warning");
            }
        },
        async processData() {
            if (!this.inputDir || !this.selectedCommand) return;

            this.addConsoleLine("Inizio elaborazione MAGLIB...", "info");
            this.processing = true;
            this.elaborazioneCompletata = false;
            this.xmlFilesFound = 0;
            this.currentProcessingStage = "Inizializzazione...";
            this.processingSummary = {
                totalProcessed: 0,
                successful: 0,
                errors: 0,
            };

            try {
                // Build arguments for Python script
                const args = [this.inputDir, this.selectedCommand];

                if (this.dryRun) {
                    args.push("--dry-run");
                    this.addConsoleLine(
                        "Modalità DRY RUN attiva - nessuna modifica verrà effettuata",
                        "info",
                    );
                }

                this.addConsoleLine(`Directory: ${this.inputDir}`, "info");
                this.addConsoleLine(`Comando: ${this.selectedCommand}`, "info");
                const commandInfo =
                    this.availableCommands[this.selectedCommand];
                this.addConsoleLine(
                    `Nome: ${commandInfo.name || commandInfo.script}`,
                    "info",
                );
                this.addConsoleLine(
                    `Descrizione: ${commandInfo.description}`,
                    "info",
                );

                // Set up real-time output listener
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
                                        const lineType =
                                            data.type === "stderr"
                                                ? "error"
                                                : line.includes("[ERROR]")
                                                  ? "error"
                                                  : line.includes("[OK]") ||
                                                      line.includes(
                                                          "Successfully",
                                                      )
                                                    ? "success"
                                                    : line.includes("[INFO]")
                                                      ? "info"
                                                      : "normal";
                                        this.addConsoleLine(
                                            line.trim(),
                                            lineType,
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
                        "project3",
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
                        "Errore durante elaborazione: " + result.error,
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
    async mounted() {
        // First initialize console
        this.addConsoleLine("MAGLIB XML Processing Tool avvio...", "info");

        // Load commands configuration
        await this.loadCommandsConfig();

        // Set default command to adapt_fs_iccd as requested
        this.selectedCommand = "adapt_fs_iccd";
        this.addConsoleLine("MAGLIB XML Processing Tool caricato", "info");
        this.addConsoleLine(
            "Comando predefinito: adapt_fs_iccd (Adatta file system per standard ICCD)",
            "info",
        );
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
