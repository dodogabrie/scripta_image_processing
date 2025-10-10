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

        <div class="row" style="height: 80vh;">
            <!-- Configuration Section -->
            <div class="col-lg-6" style="height: 100%;">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0">Configurazione</h5>
                        <!-- Action Buttons -->
                        <div class="btn-group" role="group">
                            <button
                                @click="processData"
                                :disabled="
                                    processing ||
                                    !selectedCommand ||
                                    !parameterValues.input_directory ||
                                    (selectedCommand &&
                                        availableCommands[selectedCommand] &&
                                        availableCommands[selectedCommand]
                                            .requires_output_dir &&
                                        !parameterValues.output_directory)
                                "
                                class="btn btn-success"
                            >
                                <span
                                    v-if="processing"
                                    class="spinner-border spinner-border-sm me-2"
                                    role="status"
                                ></span>
                                <i v-else class="bi bi-play-fill me-1"></i>
                                {{ processing ? "Elaborazione..." : "Avvia Processo" }}
                            </button>
                            <button
                                @click="stopProcessing"
                                :disabled="!processing"
                                class="btn btn-outline-danger"
                            >
                                <i class="bi bi-stop-circle"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body overflow-auto">

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
                                v-if="selectedCommand && availableCommands[selectedCommand]"
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
                                </div>
                            </div>
                        </div>

                        <!-- Configurable Parameters -->
                        <div
                            v-if="selectedCommand && availableCommands[selectedCommand] && availableCommands[selectedCommand].configurable_params"
                            class="mb-3"
                        >
                            <h6 class="text-muted mb-2">Parametri Configurabili</h6>
                            <div
                                v-for="(param, key) in availableCommands[selectedCommand].configurable_params"
                                :key="key"
                                class="mb-2"
                            >
                                <!-- Boolean parameters as checkboxes -->
                                <div v-if="param.type === 'boolean'" class="form-check">
                                    <input
                                        class="form-check-input"
                                        type="checkbox"
                                        v-model="parameterValues[key]"
                                        :id="'param_' + key"
                                    />
                                    <label
                                        class="form-check-label"
                                        :for="'param_' + key"
                                    >
                                        <strong>{{ param.description }}</strong>
                                        <span v-if="param.required" class="text-danger ms-1">*</span>
                                    </label>
                                </div>

                                <!-- Directory parameters -->
                                <div v-else-if="param.type === 'directory'" class="mb-2">
                                    <label class="form-label">
                                        {{ param.description }}
                                        <span v-if="param.required" class="text-danger">*</span>
                                    </label>
                                    <div class="input-group">
                                        <input
                                            type="text"
                                            class="form-control"
                                            :class="{ 'border-danger': param.required && !parameterValues[key] }"
                                            v-model="parameterValues[key]"
                                            :placeholder="param.default || 'Seleziona directory'"
                                            readonly
                                        />
                                        <button
                                            class="btn btn-outline-secondary"
                                            type="button"
                                            @click="selectParameterDirectory(key)"
                                        >
                                            <i class="bi bi-folder2-open"></i>
                                        </button>
                                    </div>
                                    <div v-if="param.required && !parameterValues[key]" class="form-text text-danger">
                                        <i class="bi bi-exclamation-triangle"></i> Questo campo è obbligatorio
                                    </div>
                                </div>

                                <!-- String parameters -->
                                <div v-else class="mb-2">
                                    <label class="form-label">
                                        {{ param.description }}
                                        <span v-if="param.required" class="text-danger">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        class="form-control"
                                        :class="{ 'border-danger': param.required && !parameterValues[key] }"
                                        v-model="parameterValues[key]"
                                        :placeholder="param.default"
                                    />
                                    <div v-if="param.required && !parameterValues[key]" class="form-text text-danger">
                                        <i class="bi bi-exclamation-triangle"></i> Questo campo è obbligatorio
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Results Section with Tabs -->
            <div class="col-lg-6" style="height: 100%;">
                <div class="card h-100 d-flex flex-column">
                    <div class="card-header">
                        <div
                            class="d-flex justify-content-between align-items-center"
                        >
                            <h5 class="card-title mb-0">Risultati e Output</h5>
                            <!-- Tab Navigation -->
                            <ul class="nav nav-pills nav-sm">
                                <li class="nav-item">
                                    <button
                                        class="nav-link"
                                        :class="{
                                            active: activeTab === 'results',
                                        }"
                                        @click="activeTab = 'results'"
                                    >
                                        <i class="bi bi-graph-up"></i> Risultati
                                    </button>
                                </li>
                                <li class="nav-item">
                                    <button
                                        class="nav-link"
                                        :class="{
                                            active: activeTab === 'console',
                                        }"
                                        @click="activeTab = 'console'"
                                    >
                                        <i class="bi bi-terminal"></i> Console
                                    </button>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!-- Tab Content -->
                    <div
                        class="card-body p-0 position-relative flex-grow-1"
                        style="min-height: 0; overflow: hidden;"
                    >
                        <!-- Tab 1: Results -->
                        <div
                            v-if="activeTab === 'results'"
                            class="p-3 h-100 overflow-auto"
                        >
                            <!-- Idle State -->
                            <div
                                v-if="!processing && !elaborazioneCompletata"
                                class="text-center text-muted py-5"
                            >
                                <i class="bi bi-file-earmark-code fs-1"></i>
                                <h5 class="mt-3">
                                    Risultati dell'elaborazione appariranno qui
                                </h5>
                                <p>
                                    Seleziona cartelle XML e output, poi clicca
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
                                        <div class="small text-muted">
                                            Errori
                                        </div>
                                        <div class="h6 text-danger">
                                            {{ processingSummary.errors }}
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="small text-muted">
                                            Totale
                                        </div>
                                        <div class="h6 text-primary">
                                            {{
                                                processingSummary.totalProcessed
                                            }}
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
                                        Comando eseguito su
                                        {{ xmlFilesFound }} file XML
                                    </p>
                                    <div
                                        v-if="
                                            processingSummary.totalProcessed > 0
                                        "
                                        class="small"
                                    >
                                        Successi:
                                        {{ processingSummary.successful }},
                                        Errori:
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
                                            <i class="bi bi-graph-up"></i>
                                            Resoconto
                                        </h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >File XML trovati:</span
                                                    >
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
                                                    <strong
                                                        class="text-success"
                                                        >{{
                                                            processingSummary.successful
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span>Errori:</span>
                                                    <strong
                                                        class="text-danger"
                                                        >{{
                                                            processingSummary.errors
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span>Avvisi:</span>
                                                    <strong
                                                        class="text-warning"
                                                        >{{
                                                            processingSummary.warnings
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span>Immagini trovate:</span>
                                                    <strong
                                                        class="text-success"
                                                        >{{
                                                            processingSummary.imagesFound
                                                        }}</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span>Immagini non trovate:</span>
                                                    <strong
                                                        class="text-danger"
                                                        >{{
                                                            processingSummary.imagesNotFound
                                                        }}</strong
                                                    >
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Tasso di
                                                        successo:</span
                                                    >
                                                    <strong
                                                        >{{
                                                            successRate
                                                        }}%</strong
                                                    >
                                                </div>
                                                <div
                                                    class="d-flex justify-content-between"
                                                >
                                                    <span
                                                        >Comando eseguito:</span
                                                    >
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

                        <!-- Tab 2: Console -->
                        <div
                            v-else-if="activeTab === 'console'"
                            class="h-100"
                        >
                            <!-- Full Console Area -->
                            <div
                                style="
                                    background: #222;
                                    color: #eee;
                                    padding: 15px;
                                    height: 100%;
                                    overflow-y: auto;
                                    overflow-x: hidden;
                                    font-size: 13px;
                                    font-family: monospace;
                                    white-space: pre-wrap;
                                    word-break: break-word;
                                "
                                id="console-output-full"
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
                                    class="text-muted text-center py-5"
                                >
                                    <i
                                        class="bi bi-terminal fs-1 mb-3 d-block"
                                    ></i>
                                    Console output will appear here...
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
    name: "ProjectProject3Component",
    data() {
        return {
            selectedCommand: "",
            processing: false,
            elaborazioneCompletata: false,
            parameterValues: {}, // Dynamic parameter values from JSON config
            consoleLines: [],
            xmlFilesFound: 0,
            currentProcessingStage: "Inizializzazione...",
            processingSummary: {
                totalProcessed: 0,
                successful: 0,
                errors: 0,
                warnings: 0,
                imagesFound: 0,
                imagesNotFound: 0,
            },
            outputUnsubscribe: null,
            activeTab: "results", // Default to results tab

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
            console.log('[DEBUG] loadCommandsConfig called');
            try {
                // Get commands configuration from Python backend
                if (window.electronAPI && window.electronAPI.runProjectScript) {
                    console.log('[DEBUG] electronAPI available');
                    this.addConsoleLine(
                        "Caricamento configurazione comandi da backend...",
                        "info",
                    );

                    const result = await window.electronAPI.runProjectScript(
                        "project3",
                        "main.py",
                        ["--export-json"],
                    );

                    console.log('[DEBUG] Result from backend:', result);
                    console.log('[DEBUG] result.success:', result.success);
                    console.log('[DEBUG] result.scriptOutput:', result.scriptOutput);
                    console.log('[DEBUG] result.output:', result.output);

                    if (result.success && result.scriptOutput) {
                        console.log('[DEBUG] Attempting to parse JSON...');
                        try {
                            const config = JSON.parse(result.scriptOutput);
                            console.log('[DEBUG] Parsed config:', config);
                            if (config.error) {
                                throw new Error(config.error);
                            }
                            this.availableCommands = config.commands;
                            this.commandsLoaded = true;
                            console.log('[DEBUG] Commands loaded:', this.availableCommands);
                            console.log('[DEBUG] commandsLoaded:', this.commandsLoaded);
                            this.addConsoleLine(
                                `Configurazione caricata dal backend Python`,
                                "success",
                            );
                            this.addConsoleLine(
                                `Trovati ${Object.keys(config.commands).length} comandi disponibili`,
                                "info",
                            );
                        } catch (parseError) {
                            console.error('[DEBUG] JSON parse error:', parseError);
                            throw new Error(
                                `Errore parsing JSON dal backend: ${parseError.message}`,
                            );
                        }
                    } else {
                        console.error('[DEBUG] Backend call failed or no scriptOutput');
                        throw new Error(
                            `Backend error: ${result.error || "Unknown error"}`,
                        );
                    }
                } else {
                    this.addConsoleLine(
                        "electronAPI.runProjectScript non disponibile, uso configurazione predefinita",
                        "warning",
                    );
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
            }
        },
        addConsoleLine(text, type = "normal") {
            this.consoleLines.push({ text, type });
            // Removed 200 line limit - keep all console output
            this.$nextTick(() => {
                const el = document.getElementById("console-output");
                if (el) el.scrollTop = el.scrollHeight;

                // Also scroll the full console if it exists
                const fullEl = document.getElementById("console-output-full");
                if (fullEl) fullEl.scrollTop = fullEl.scrollHeight;
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
                (line.includes("Error processing") ||
                    line.includes("FAILED")) &&
                !line.includes("WARNING")
            ) {
                this.processingSummary.errors++;
                this.processingSummary.totalProcessed++;
            } else if (line.includes("WARNING")) {
                this.processingSummary.warnings++;
            } else if (line.includes("Images found:")) {
                const match = line.match(/Images found: (\d+)/);
                if (match) {
                    this.processingSummary.imagesFound = parseInt(match[1]);
                }
            } else if (line.includes("Images not found:")) {
                const match = line.match(/Images not found: (\d+)/);
                if (match) {
                    this.processingSummary.imagesNotFound = parseInt(match[1]);
                }
            } else if (line.includes("PROCESSING SUMMARY")) {
                this.currentProcessingStage = "Generando resoconto finale...";
            } else if (line.includes("Setup")) {
                this.currentProcessingStage =
                    "Configurazione ambiente maglib...";
            } else if (line.includes("DRY RUN")) {
                this.currentProcessingStage = "Anteprima comandi (Dry Run)...";
            }
        },
        async selectParameterDirectory(paramKey) {
            this.addConsoleLine(`Selezione directory per ${paramKey}...`, "info");
            if (!window.electronAPI || !window.electronAPI.selectDirectory) {
                this.addConsoleLine(
                    "electronAPI.selectDirectory non disponibile",
                    "error",
                );
                return;
            }
            const dir = await window.electronAPI.selectDirectory();
            if (dir) {
                this.parameterValues[paramKey] = dir;
                this.addConsoleLine(
                    `Directory ${paramKey} selezionata: ${dir}`,
                    "success",
                );
            } else {
                this.addConsoleLine(
                    `Selezione directory ${paramKey} annullata.`,
                    "warning",
                );
            }
        },
        initializeParameterValues() {
            if (!this.selectedCommand || !this.availableCommands[this.selectedCommand]) {
                this.parameterValues = {};
                return;
            }

            const command = this.availableCommands[this.selectedCommand];
            const newValues = {};

            if (command.configurable_params) {
                Object.entries(command.configurable_params).forEach(([key, param]) => {
                    // Initialize with default values
                    if (param.type === 'boolean') {
                        newValues[key] = param.default || false;
                    } else {
                        newValues[key] = param.default || '';
                    }
                });
            }

            this.parameterValues = newValues;
        },
        async processData() {
            const inputDir = this.parameterValues.input_directory;
            const outputDir = this.parameterValues.output_directory;

            if (!inputDir || !this.selectedCommand) return;

            const commandInfo = this.availableCommands[this.selectedCommand];

            // Check if output directory is required
            if (commandInfo.requires_output_dir && !outputDir) {
                this.addConsoleLine(
                    "Errore: Il comando selezionato richiede una cartella di output",
                    "error",
                );
                return;
            }

            this.addConsoleLine("Inizio elaborazione MAGLIB...", "info");
            this.processing = true;
            this.elaborazioneCompletata = false;
            this.xmlFilesFound = 0;
            this.currentProcessingStage = "Inizializzazione...";
            this.processingSummary = {
                totalProcessed: 0,
                successful: 0,
                errors: 0,
                warnings: 0,
                imagesFound: 0,
                imagesNotFound: 0,
            };

            try {
                // Build arguments for Python script
                let args = [inputDir, this.selectedCommand];

                // Handle custom params format for commands that need it
                if (commandInfo.use_custom_params_format) {
                    // Build custom-params arguments
                    if (commandInfo.default_params) {
                        Object.entries(commandInfo.default_params).forEach(
                            ([param, value]) => {
                                if (typeof value === "boolean" && value) {
                                    // Boolean parameters like --ignore-missing
                                    args.push("--custom-params=" + param);
                                } else if (typeof value === "string") {
                                    // String parameters with values
                                    args.push("--custom-params=" + param);
                                    if (value === "{input_dir}") {
                                        args.push(
                                            "--custom-params=" + inputDir,
                                        );
                                    } else if (value === "{output_dir}") {
                                        args.push(
                                            "--custom-params=" + outputDir,
                                        );
                                    } else {
                                        args.push("--custom-params=" + value);
                                    }
                                }
                            },
                        );
                    }

                    // Add auto parameters
                    if (commandInfo.auto_params) {
                        commandInfo.auto_params.forEach((param) => {
                            args.push("--custom-params=" + param);
                        });
                    }

                    // Add configurable parameters based on user input
                    if (commandInfo.configurable_params) {
                        Object.entries(commandInfo.configurable_params).forEach(([key, param]) => {
                            const value = this.parameterValues[key];
                            if (param.type === 'boolean') {
                                if (value) {
                                    args.push("--custom-params=" + param.param);
                                }
                            } else if (value && value !== param.default) {
                                // Only add non-default values for non-boolean parameters
                                args.push("--custom-params=" + param.param);
                                args.push("--custom-params=" + value);
                            }
                        });
                    }
                } else {
                    // Standard argument handling for other commands
                    // Add configurable parameters for standard commands
                    if (commandInfo.configurable_params) {
                        Object.entries(commandInfo.configurable_params).forEach(([key, param]) => {
                            const value = this.parameterValues[key];
                            if (param.type === 'boolean' && value) {
                                args.push(param.param);
                            } else if (param.type !== 'boolean' && value && value !== param.default) {
                                args.push(param.param, value);
                            }
                        });
                    }
                }

                // Check for dry-run mode
                const isDryRun = this.parameterValues.dry_run || false;
                if (isDryRun) {
                    this.addConsoleLine(
                        "Modalità DRY RUN attiva - nessuna modifica verrà effettuata",
                        "info",
                    );
                }

                this.addConsoleLine(`Directory XML: ${inputDir}`, "info");
                if (outputDir) {
                    this.addConsoleLine(
                        `Directory Output: ${outputDir}`,
                        "info",
                    );
                }
                this.addConsoleLine(`Comando: ${this.selectedCommand}`, "info");
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
    watch: {
        selectedCommand: {
            handler() {
                this.initializeParameterValues();
            },
            immediate: false, // Don't call immediately since command will be set in mounted()
        },
        availableCommands: {
            handler() {
                // Re-initialize parameters when commands are loaded
                this.initializeParameterValues();
            },
            immediate: false,
        },
    },
    async mounted() {
        // First initialize console
        this.addConsoleLine("MAGLIB XML Processing Tool avvio...", "info");

        // Load commands configuration
        await this.loadCommandsConfig();

        // Set default command to adapt_fs_iccd if it exists
        if (this.commandsLoaded && this.availableCommands["adapt_fs_iccd"]) {
            this.selectedCommand = "adapt_fs_iccd";
            this.addConsoleLine("MAGLIB XML Processing Tool caricato", "info");
            this.addConsoleLine(
                "Comando predefinito: adapt_fs_iccd (Adatta file system per standard ICCD)",
                "info",
            );
        } else {
            this.addConsoleLine("MAGLIB XML Processing Tool caricato", "info");
            if (!this.commandsLoaded) {
                this.addConsoleLine(
                    "Attenzione: impossibile caricare i comandi disponibili",
                    "warning",
                );
            }
        }
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
