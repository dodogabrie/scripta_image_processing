<template>
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <div
                    class="d-flex justify-content-between align-items-center mb-4"
                >
                    <div>
                        <h1>
                            <i class="bi bi-diagram-3"></i> Pipeline Manager
                        </h1>
                        <p class="text-muted">
                            Create and execute sequential image processing
                            workflows by chaining multiple projects together
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pipeline Configuration Section -->
        <div class="row">
            <!-- Available Projects -->
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-collection"></i> Progetti
                            disponibili
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="project-list">
                            <div
                                v-for="project in availableProjects"
                                :key="project.id"
                                class="project-item"
                                draggable="true"
                                @dragstart="onDragStart(project)"
                                @dragend="onDragEnd"
                            >
                                <div class="d-flex align-items-center">
                                    <img
                                        v-if="project.iconDataUrl"
                                        :src="project.iconDataUrl"
                                        alt="Project icon"
                                        class="project-icon me-2"
                                    />
                                    <i v-else class="bi bi-image me-2"></i>
                                    <div>
                                        <div class="fw-bold">
                                            {{ project.config.name }}
                                        </div>
                                        <small class="text-muted">{{
                                            project.id
                                        }}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pipeline Builder -->
            <div class="col-lg-8">
                <div class="card">
                    <div
                        class="card-header d-flex justify-content-between align-items-center"
                    >
                        <h5 class="card-title mb-0">
                            <i class="bi bi-arrow-right"></i> Steps della
                            pipeline
                        </h5>
                        <button
                            class="btn btn-sm btn-outline-danger"
                            @click="clearPipeline"
                            :disabled="pipelineSteps.length === 0"
                        >
                            <i class="bi bi-trash"></i> Clear
                        </button>
                    </div>
                    <div class="card-body">
                        <!-- Drop Zone -->
                        <div
                            class="pipeline-builder"
                            @dragover.prevent
                            @drop="onDrop"
                            :class="{ 'drop-active': isDragActive }"
                        >
                            <div
                                v-if="pipelineSteps.length === 0"
                                class="empty-pipeline"
                            >
                                <i
                                    class="bi bi-arrows-move display-1 text-muted"
                                ></i>
                                <p class="text-muted">
                                     Trascina qui i progetti per costruire la tua pipeline
                                </p>
                            </div>

                            <!-- Pipeline Steps -->
                            <div v-else class="pipeline-steps">
                                <div
                                    v-for="(step, index) in pipelineSteps"
                                    :key="index"
                                    class="pipeline-step"
                                >
                                    <div class="step-card">
                                        <div class="step-header">
                                            <div
                                                class="d-flex align-items-center flex-grow-1"
                                            >
                                                <span class="step-number">{{
                                                    index + 1
                                                }}</span>
                                                <img
                                                    v-if="
                                                        step.project.iconDataUrl
                                                    "
                                                    :src="
                                                        step.project.iconDataUrl
                                                    "
                                                    alt="Project icon"
                                                    class="project-icon me-2"
                                                />
                                                <div>
                                                    <div class="fw-bold">
                                                        {{
                                                            step.project.config
                                                                .name
                                                        }}
                                                    </div>
                                                    <small class="text-muted">{{
                                                        step.project.id
                                                    }}</small>
                                                </div>
                                            </div>
                                            <button
                                                class="btn btn-sm btn-outline-danger"
                                                @click="removeStep(index)"
                                            >
                                                <i class="bi bi-x"></i>
                                            </button>
                                        </div>

                                        <!-- Step Parameters -->
                                        <div class="step-parameters mt-2">
                                            <div
                                                v-for="param in step.parameters"
                                                :key="param.name"
                                                class="mb-2"
                                            >
                                                <label class="form-label">{{
                                                    param.label
                                                }}</label>
                                                <input
                                                    v-if="
                                                        param.type === 'text' ||
                                                        param.type === 'number'
                                                    "
                                                    :type="param.type"
                                                    class="form-control form-control-sm"
                                                    v-model="param.value"
                                                    :placeholder="
                                                        param.placeholder
                                                    "
                                                />
                                                <select
                                                    v-else-if="
                                                        param.type === 'select'
                                                    "
                                                    class="form-select form-select-sm"
                                                    v-model="param.value"
                                                >
                                                    <option
                                                        v-for="option in param.options"
                                                        :key="option.value"
                                                        :value="option.value"
                                                    >
                                                        {{ option.label }}
                                                    </option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Arrow between steps -->
                                    <div
                                        v-if="index < pipelineSteps.length - 1"
                                        class="step-arrow"
                                    >
                                        <i class="bi bi-arrow-down"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Execution Section -->
        <div class="row mt-4" v-if="pipelineSteps.length > 0">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-play-circle"></i> Esecuzione pipeline 
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <button
                                        @click="selectInputDir"
                                        class="btn btn-primary w-100 mb-2"
                                    >
                                        <i class="bi bi-folder2-open"></i>
                                        Seleziona cartella di input
                                    </button>
                                    <div
                                        v-if="inputDir"
                                        class="alert alert-info py-2 px-3"
                                    >
                                        <strong>Input:</strong>
                                        <div class="small text-break">
                                            {{ inputDir }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <button
                                        @click="selectOutputDir"
                                        class="btn btn-secondary w-100 mb-2"
                                    >
                                        <i class="bi bi-folder2-open"></i>
                                        Seleziona cartella di output
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
                                </div>
                            </div>
                        </div>

                        <div class="d-flex gap-2">
                            <button
                                @click="executePipeline"
                                class="btn btn-success"
                                :disabled="!canExecute || processing"
                            >
                                <i class="bi bi-play"></i>
                                {{
                                    processing
                                        ? "Elaborazione..."
                                        : "Esegui Pipeline"
                                }}
                            </button>
                            <button
                                v-if="processing"
                                @click="stopPipeline"
                                class="btn btn-danger"
                            >
                                <i class="bi bi-stop"></i> Stop
                            </button>
                            <button
                                @click="savePipeline"
                                class="btn btn-outline-primary"
                                :disabled="pipelineSteps.length === 0"
                            >
                                <i class="bi bi-save"></i> Salva Pipeline
                            </button>
                            <button
                                @click="loadPipeline"
                                class="btn btn-outline-secondary"
                            >
                                <i class="bi bi-upload"></i> Carica Pipeline
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Progress and Output Section -->
        <div class="row mt-4" v-if="processing || executionResult">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-terminal"></i> Progresso di esecuzione
                        </h5>
                    </div>
                    <div class="card-body">
                        <!-- Progress Bar -->
                        <div v-if="processing" class="mb-3">
                            <div
                                class="d-flex justify-content-between align-items-center mb-2"
                            >
                                <span>{{ currentStepMessage }}</span>
                                <span
                                    >{{ Math.round(executionProgress) }}%</span
                                >
                            </div>
                            <div class="progress">
                                <div
                                    class="progress-bar"
                                    role="progressbar"
                                    :style="{ width: executionProgress + '%' }"
                                ></div>
                            </div>
                        </div>

                        <!-- Console Output -->
                        <div class="console-output">
                            <div
                                v-for="(line, index) in consoleLines"
                                :key="index"
                                class="console-line"
                                :class="line.type"
                            >
                                {{ line.text }}
                            </div>
                        </div>

                        <!-- Result -->
                        <div v-if="executionResult" class="mt-3">
                            <div
                                class="alert"
                                :class="
                                    executionResult.success
                                        ? 'alert-success'
                                        : 'alert-danger'
                                "
                            >
                                <i
                                    :class="
                                        executionResult.success
                                            ? 'bi bi-check-circle'
                                            : 'bi bi-x-circle'
                                    "
                                ></i>
                                {{ executionResult.message }}
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
    name: "ProjectPipelineComponent",
    data() {
        return {
            availableProjects: [],
            pipelineSteps: [],
            inputDir: null,
            outputDir: null,
            processing: false,
            isDragActive: false,
            executionProgress: 0,
            currentStepMessage: "",
            consoleLines: [],
            executionResult: null,
            draggedProject: null,
        };
    },
    computed: {
        canExecute() {
            return (
                this.inputDir &&
                this.outputDir &&
                this.pipelineSteps.length > 0 &&
                !this.processing
            );
        },
    },
    methods: {
        async loadAvailableProjects() {
            try {
                const projects = await window.electronAPI.getProjects();
                // Filter out pipeline projects from available projects
                this.availableProjects = projects.filter(
                    (p) => p.config.type !== "pipeline",
                );

                // Load icons
                for (const project of this.availableProjects) {
                    const dataUrl = await window.electronAPI.getProjectIconData(
                        project.id,
                    );
                    project.iconDataUrl = dataUrl;
                }
            } catch (error) {
                console.error("Error loading projects:", error);
            }
        },

        onDragStart(project) {
            this.draggedProject = project;
            this.isDragActive = true;
        },

        onDragEnd() {
            this.isDragActive = false;
            this.draggedProject = null;
        },

        onDrop(event) {
            event.preventDefault();
            this.isDragActive = false;

            if (this.draggedProject) {
                this.addStep(this.draggedProject);
                this.draggedProject = null;
            }
        },

        addStep(project) {
            const step = {
                project: project,
                parameters: this.getProjectParameters(project),
            };
            this.pipelineSteps.push(step);
        },

        removeStep(index) {
            this.pipelineSteps.splice(index, 1);
        },

        clearPipeline() {
            this.pipelineSteps = [];
            this.executionResult = null;
            this.consoleLines = [];
        },

        getProjectParameters(project) {
            // Define common parameters for different project types
            const commonParams = [];

            // Add project-specific parameters based on project ID
            if (project.id === "project1") {
                commonParams.push(
                    {
                        name: "borderPixels",
                        label: "Border Pixels",
                        type: "number",
                        value: "100",
                        placeholder: "100",
                    },
                    {
                        name: "imageFormat",
                        label: "Image Format",
                        type: "select",
                        value: "",
                        options: [
                            { value: "", label: "All formats" },
                            { value: "jpg", label: "JPG" },
                            { value: "png", label: "PNG" },
                            { value: "tiff", label: "TIFF" },
                        ],
                    },
                );
            } else if (project.id === "project2") {
                commonParams.push({
                    name: "imageFormat",
                    label: "Image Format",
                    type: "select",
                    value: "",
                    options: [
                        { value: "", label: "All formats" },
                        { value: "jpg", label: "JPG" },
                        { value: "png", label: "PNG" },
                        { value: "tiff", label: "TIFF" },
                    ],
                });
            }

            return commonParams;
        },

        async selectInputDir() {
            this.inputDir = await window.electronAPI.selectDirectory();
        },

        async selectOutputDir() {
            this.outputDir = await window.electronAPI.selectDirectory();
        },

        async executePipeline() {
            if (!this.canExecute) return;

            this.processing = true;
            this.executionProgress = 0;
            this.currentStepMessage = "Inizializzando la pipeline...";
            this.consoleLines = [];
            this.executionResult = null;

            try {
                // Prepare pipeline configuration
                const pipelineConfig = {
                    steps: this.pipelineSteps.map((step) => ({
                        projectId: step.project.id,
                        parameters: step.parameters.reduce((acc, param) => {
                            acc[param.name] = param.value;
                            return acc;
                        }, {}),
                    })),
                    inputDir: this.inputDir,
                    outputDir: this.outputDir,
                };

                this.addConsoleLines("Starting pipeline execution...", "info");
                this.addConsoleLines(
                    `Input: ${pipelineConfig.inputDir}`,
                    "info",
                );
                this.addConsoleLines(
                    `Output: ${pipelineConfig.outputDir}`,
                    "info",
                );
                this.addConsoleLines(
                    `Steps: ${pipelineConfig.steps.length}`,
                    "info",
                );

                // Execute pipeline through IPC
                const result = await window.electronAPI.runProjectScript(
                    "pipeline",
                    "pipeline_orchestrator.py",
                    [JSON.stringify(pipelineConfig)],
                );

                this.executionResult = {
                    success: result.success,
                    message: result.success
                        ? "Pipeline executed successfully!"
                        : result.error,
                };

                // Process output like Project1 does
                if (result.success) {
                    this.addConsoleLines(
                        "Pipeline completed successfully!",
                        "success",
                    );
                    if (result.output) {
                        result.output
                            .toString()
                            .split("\n")
                            .forEach((line) => {
                                if (line.trim())
                                    this.addConsoleLines(line.trim(), "stdout");
                            });
                    }
                } else {
                    this.addConsoleLines(
                        "Pipeline execution failed: " + result.error,
                        "error",
                    );
                    if (result.output) {
                        result.output
                            .toString()
                            .split("\n")
                            .forEach((line) => {
                                if (line.trim())
                                    this.addConsoleLines(line.trim(), "stdout");
                            });
                    }
                }
            } catch (error) {
                this.executionResult = {
                    success: false,
                    message: "Pipeline execution failed: " + error.message,
                };
                this.addConsoleLines(error.message, "stderr");
            } finally {
                this.processing = false;
                this.executionProgress = 100;
                this.currentStepMessage = "Pipeline execution completed";
            }
        },

        async stopPipeline() {
            try {
                await window.electronAPI.stopPythonProcess();
                this.processing = false;
                this.currentStepMessage = "Pipeline execution stopped";
                this.addConsoleLines(
                    "Pipeline execution stopped by user",
                    "info",
                );
            } catch (error) {
                console.error("Error stopping pipeline:", error);
            }
        },

        addConsoleLines(text, type = "stdout") {
            this.consoleLines.push({
                text: text,
                type: type,
            });
            if (this.consoleLines.length > 1000) this.consoleLines.shift();
            // Auto-scroll to bottom
            this.$nextTick(() => {
                const consoleEl = document.querySelector(".console-output");
                if (consoleEl) consoleEl.scrollTop = consoleEl.scrollHeight;
            });
        },

        savePipeline() {
            const pipelineData = {
                name: prompt("Enter pipeline name:"),
                steps: this.pipelineSteps.map((step) => ({
                    projectId: step.project.id,
                    parameters: step.parameters,
                })),
            };

            if (pipelineData.name) {
                localStorage.setItem(
                    `pipeline_${pipelineData.name}`,
                    JSON.stringify(pipelineData),
                );
                alert("Pipeline saved successfully!");
            }
        },

        loadPipeline() {
            const pipelineName = prompt("Enter pipeline name to load:");
            if (pipelineName) {
                const savedPipeline = localStorage.getItem(
                    `pipeline_${pipelineName}`,
                );
                if (savedPipeline) {
                    const pipelineData = JSON.parse(savedPipeline);
                    this.loadPipelineFromData(pipelineData);
                    alert("Pipeline loaded successfully!");
                } else {
                    alert("Pipeline not found!");
                }
            }
        },

        async loadPipelineFromData(pipelineData) {
            this.pipelineSteps = [];
            for (const stepData of pipelineData.steps) {
                const project = this.availableProjects.find(
                    (p) => p.id === stepData.projectId,
                );
                if (project) {
                    const step = {
                        project: project,
                        parameters: stepData.parameters,
                    };
                    this.pipelineSteps.push(step);
                }
            }
        },

        goBack() {
            this.$emit("goBack");
        },
    },

    async mounted() {
        await this.loadAvailableProjects();

        // Listen for pipeline execution progress (if streaming is implemented)
        if (window.electronAPI.onPipelineProgress) {
            window.electronAPI.onPipelineProgress((data) => {
                this.executionProgress = data.progress;
                this.currentStepMessage = data.message;
                if (data.output) {
                    this.addConsoleLines(data.output, data.type || "stdout");
                }
            });
        }
    },
};
</script>

<style scoped>
.project-list {
    max-height: 400px;
    overflow-y: auto;
}

.project-item {
    padding: 10px;
    margin-bottom: 8px;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    cursor: grab;
    transition: all 0.2s;
}

.project-item:hover {
    background-color: #f8f9fa;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.project-item:active {
    cursor: grabbing;
}

.project-icon {
    width: 24px;
    height: 24px;
    object-fit: contain;
}

.pipeline-builder {
    min-height: 300px;
    border: 2px dashed #dee2e6;
    border-radius: 8px;
    padding: 20px;
    transition: all 0.3s;
}

.pipeline-builder.drop-active {
    border-color: #007bff;
    background-color: #f8f9fa;
}

.empty-pipeline {
    text-align: center;
    padding: 60px 20px;
}

.pipeline-steps {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.pipeline-step {
    position: relative;
}

.step-card {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    background: white;
}

.step-header {
    display: flex;
    justify-content: between;
    align-items: center;
}

.step-number {
    background: #007bff;
    color: white;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 10px;
}

.step-arrow {
    text-align: center;
    color: #6c757d;
    font-size: 1.2em;
    margin: 5px 0;
}

.step-parameters {
    border-top: 1px solid #f0f0f0;
    padding-top: 10px;
}

.console-output {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 10px;
    max-height: 300px;
    overflow-y: auto;
    font-family: "Courier New", monospace;
    font-size: 0.9em;
}

.console-line {
    margin-bottom: 2px;
}

.console-line.stderr {
    color: #dc3545;
}

.console-line.error {
    color: #dc3545;
    font-weight: bold;
}

.console-line.info {
    color: #0dcaf0;
}

.console-line.success {
    color: #198754;
    font-weight: bold;
}

.console-line.warning {
    color: #fd7e14;
}

.console-line.stdout {
    color: #212529;
}

.console-line.normal {
    color: #212529;
}
</style>
