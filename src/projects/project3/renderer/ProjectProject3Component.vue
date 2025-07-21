<template>
    <div class="container py-4">
        <h1>Digiscripta Builder</h1>
        <p class="text-muted">
            Crea una struttura gerarchica di modelli (padri/figli)
        </p>

        <!-- Import/Export Controls -->
        <div class="d-flex gap-3 mb-4">
            <ImportTreeData @import-complete="handleImport" />
        </div>

        <div class="mb-4">
            <div class="d-flex align-items-center">
                <input
                    v-model="newRootName"
                    placeholder="Nome elemento radice"
                    class="form-control w-auto me-2"
                />
                <button @click="addRootNode" class="btn btn-primary">
                    Aggiungi elemento radice
                </button>
            </div>
        </div>

        <div v-if="rootNodes.length === 0" class="text-muted">
            Nessun elemento creato.
        </div>
        <div v-for="(node, idx) in rootNodes" :key="node.id" class="mb-3">
            <TreeNode :node="node" />
        </div>

        <!-- Export Button -->
        <div class="mt-4 border-top pt-3">
            <button @click="exportData" class="btn btn-success">
                📥 Esporta Struttura
            </button>
            <div v-if="exportedData" class="mt-3">
                <div class="alert alert-success">
                    Struttura esportata con successo!
                    <button
                        @click="downloadExport"
                        class="btn btn-sm btn-outline-success ms-2"
                    >
                        💾 Scarica JSON
                    </button>
                </div>
            </div>
        </div>

        <div v-if="processing" class="text-muted">Elaborazione...</div>
        <div v-if="elaborazioneCompletata" class="alert alert-success">
            Completato!
        </div>
    </div>
</template>

<script>
import { v4 as uuidv4 } from "uuid";
import TreeNode from "./components/TreeNode/TreeNode.vue";
import ImportTreeData from "./components/TreeNode/TreeNodeJson/ImportTreeData.vue";
import { TreeExporter } from "./components/TreeNode/TreeNodeUtils";

export default {
    name: "ProjectProject3Component",
    components: { TreeNode, ImportTreeData },
    data() {
        return {
            rootNodes: [],
            newRootName: "",
            processing: false,
            elaborazioneCompletata: false,
            exportedData: null,
        };
    },
    methods: {
        addRootNode() {
            if (this.newRootName.trim()) {
                this.rootNodes.push({
                    id: uuidv4(),
                    name: this.newRootName,
                    type: "node",
                    children: [],
                });
                this.newRootName = "";
            }
        },



        exportData() {
            try {
                this.exportedData = TreeExporter.exportToJSON(
                    {
                        id: "root",
                        name: "DigiScripta Structure",
                        type: "node",
                        children: this.rootNodes,
                    },
                    {
                        includeMetadata: true,
                        includeStats: true,
                        includeIds: false,
                        includeValues: false,
                        pretty: true,
                    },
                );
            } catch (error) {
                console.error("Export failed:", error);
            }
        },

        downloadExport() {
            if (!this.exportedData) return;

            const blob = new Blob([this.exportedData], {
                type: "application/json",
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `digiscripta-structure-${new Date().toISOString()}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        },

        async selectInputDir() {
            this.inputDir = await window.electronAPI.selectDirectory();
        },

        async selectOutputDir() {
            this.outputDir = await window.electronAPI.selectDirectory();
        },

        async processData() {
            this.processing = true;
            const result = await window.electronAPI.runProjectScript(
                "project3",
                "main.py",
                [this.inputDir, this.outputDir],
            );
            this.processing = false;
            this.elaborazioneCompletata = result.success;
        },

        goBack() {
            this.$emit("goBack");
        },

        handleImport(importedTree) {
            if (importedTree && importedTree.children) {
                // Reset current tree and add imported nodes
                this.rootNodes = [...importedTree.children];
            }
        },
    },
};
</script>

<style scoped>
.card {
    background: #f8f9fa;
}

.btn-success {
    background-color: #28a745;
    border-color: #28a745;
}

.btn-success:hover {
    background-color: #218838;
    border-color: #1e7e34;
}

.alert-success {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
}
</style>
