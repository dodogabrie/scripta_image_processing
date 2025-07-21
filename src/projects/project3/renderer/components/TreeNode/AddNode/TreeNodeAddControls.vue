<template>
    <div class="row g-2 mb-3">
        <div class="col-md-6">
            <input
                v-model="newChildName"
                placeholder="Nome nodo figlio"
                class="form-control"
                @keyup.enter="addChild"
            />
            <button
                @click="addChild"
                class="btn btn-success mt-1 w-100"
                :disabled="!newChildName.trim()"
            >
                ➕ Aggiungi Nodo
            </button>
        </div>
        <div class="col-md-6">
            <input
                v-model="newFieldName"
                placeholder="Nome campo"
                class="form-control"
                @keyup.enter="addField"
            />
            <select v-model="newFieldType" class="form-select mt-1">
                <option value="text">📝 Testo</option>
                <option value="choices">🔘 Scelte</option>
                <option value="numeric">🔢 Numerico</option>
            </select>
            <button
                @click="addField"
                class="btn btn-warning mt-1 w-100"
                :disabled="!newFieldName.trim()"
            >
                🏷️ Aggiungi Campo
            </button>
        </div>
    </div>
</template>

<script>
export default {
    name: "TreeNodeAddControls",
    data() {
        return {
            newChildName: "",
            newFieldName: "",
            newFieldType: "text"
        };
    },
    methods: {
        addChild() {
            if (!this.newChildName.trim()) return;
            this.$emit("add-child", this.newChildName);
            this.newChildName = "";
        },
        addField() {
            if (!this.newFieldName.trim()) return;
            const fieldConfig = this.getDefaultConfig(this.newFieldType);
            this.$emit("add-field", this.newFieldName, this.newFieldType, fieldConfig);
            this.newFieldName = "";
        },
        getDefaultConfig(fieldType) {
            switch (fieldType) {
                case "choices":
                    return { options: [] };
                case "numeric":
                    return { min: null, max: null, mapping: {} };
                default:
                    return {};
            }
        }
    }
};
</script>

<style scoped>
.form-control,
.form-select {
    font-size: 0.9rem;
}

.btn {
    font-size: 0.9rem;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
