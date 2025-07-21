<template>
    <div>
        <!-- Input file button -->
        <div class="mb-3">
            <label class="btn btn-outline-primary">
                📂 Seleziona JSON
                <input
                    type="file"
                    accept=".json"
                    class="d-none"
                    @change="handleFileSelect"
                />
            </label>
            <span v-if="selectedFile" class="ms-2 text-muted">
                {{ selectedFile.name }}
            </span>

            <!-- Import button -->
            <button
                @click="importData"
                class="btn btn-success"
                :disabled="!jsonContent || importing"
            >
                <span v-if="!importing">📥 Importa Struttura</span>
                <span v-else>⏳ Importazione...</span>
            </button>
        </div>

        <!-- Error display -->
        <div v-if="error" class="alert alert-danger mt-3">
            <strong>Errore:</strong> {{ error }}
        </div>

        <!-- Success message -->
        <div v-if="importSuccess" class="alert alert-success mt-3">
            Struttura importata con successo!
        </div>
    </div>
</template>

<script>
import { TreeImporter } from "../TreeNodeUtils";

export default {
    name: "ImportTreeData",
    data() {
        return {
            selectedFile: null,
            jsonContent: null,
            importing: false,
            error: null,
            importSuccess: false,
        };
    },
    methods: {
        async handleFileSelect(event) {
            this.error = null;
            this.importSuccess = false;
            this.jsonContent = null;
            const file = event.target.files[0];

            if (!file) return;

            this.selectedFile = file;
            try {
                const content = await this.readFileContent(file);
                this.jsonContent = content;
            } catch (err) {
                this.error = "Errore nella lettura del file: " + err.message;
            }
        },

        readFileContent(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const content = JSON.parse(e.target.result);
                        resolve(content);
                    } catch (err) {
                        reject(new Error("Il file non contiene JSON valido"));
                    }
                };
                reader.onerror = (err) => reject(err);
                reader.readAsText(file);
            });
        },

        async importData() {
            if (!this.jsonContent) return;

            this.importing = true;
            this.error = null;
            this.importSuccess = false;

            try {
                const result = TreeImporter.importFromJSON(this.jsonContent);

                if (!result.success) {
                    throw new Error(result.errors.join("\n"));
                }

                // Emit the imported tree structure
                this.$emit("import-complete", result.tree);
                this.importSuccess = true;

                // Reset file input
                this.selectedFile = null;
                this.jsonContent = null;
            } catch (err) {
                this.error = "Errore durante l'importazione: " + err.message;
            } finally {
                this.importing = false;
            }
        },
    },
};
</script>

<style scoped>
.alert {
    margin-top: 1rem;
}

.alert-danger {
    background-color: #f8d7da;
    border-color: #f5c6cb;
    color: #721c24;
}

.alert-success {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
}

.btn-outline-primary:hover {
    background-color: #0056b3;
}

.text-muted {
    color: #6c757d;
}
</style>
