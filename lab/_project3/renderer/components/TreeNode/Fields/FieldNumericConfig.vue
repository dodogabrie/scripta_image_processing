<template>
    <div class="mb-2">
        <!-- Min/Max Configuration -->
        <div class="row g-2 mb-2">
            <div class="col-6">
                <input
                    v-model.number="localConfig.min"
                    type="number"
                    placeholder="Valore minimo"
                    class="form-control"
                    @change="updateConfig"
                />
            </div>
            <div class="col-6">
                <input
                    v-model.number="localConfig.max"
                    type="number"
                    placeholder="Valore massimo"
                    class="form-control"
                    @change="updateConfig"
                />
            </div>
        </div>

        <!-- Number-Text Mapping -->
        <div class="d-flex align-items-center mb-2">
            <input
                v-model.number="newMappingKey"
                type="number"
                placeholder="Numero"
                class="form-control me-2"
                @keyup.enter="addMapping"
            />
            <input
                v-model="newMappingValue"
                placeholder="Descrizione"
                class="form-control me-2"
                @keyup.enter="addMapping"
            />
            <button
                @click="addMapping"
                class="btn btn-sm btn-outline-primary"
                :disabled="newMappingKey === null || !newMappingValue.trim()"
            >
                ➕
            </button>
        </div>

        <!-- Display Current Mappings -->
        <div v-if="localConfig?.mapping && Object.keys(localConfig.mapping).length > 0" class="d-flex flex-wrap gap-1 mb-2">
            <span
                v-for="(text, num) in localConfig.mapping"
                :key="num"
                class="badge bg-secondary d-flex align-items-center"
            >
                {{ num }}: {{ text }}
                <button
                    @click="removeMapping(num)"
                    class="btn-close btn-close-white ms-1"
                    :aria-label="`Rimuovi mapping ${num}`"
                ></button>
            </span>
        </div>

        <!-- Validation Info -->
        <div class="small text-muted">
            <div v-if="localConfig.min !== null || localConfig.max !== null">
                <strong>Range:</strong>
                <span v-if="localConfig.min !== null">Min: {{ localConfig.min }}</span>
                <span v-if="localConfig.min !== null && localConfig.max !== null"> • </span>
                <span v-if="localConfig.max !== null">Max: {{ localConfig.max }}</span>
            </div>
            <div v-if="Object.keys(localConfig?.mapping || {}).length > 0">
                <strong>Mappings:</strong> {{ Object.keys(localConfig.mapping).length }} configurati
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: "FieldNumericConfig",
    props: {
        node: { type: Object, required: true }
    },
    data() {
        return {
            newMappingKey: null,
            newMappingValue: "",
            localConfig: {
                min: null,
                max: null,
                mapping: {}
            }
        };
    },
    created() {
        // Initialize local config from node
        this.localConfig = {
            min: this.node.config?.min || null,
            max: this.node.config?.max || null,
            mapping: { ...(this.node.config?.mapping || {}) }
        };
    },
    watch: {
        // Watch for external changes to node config
        'node.config': {
            deep: true,
            handler(newConfig) {
                this.localConfig = {
                    min: newConfig?.min || null,
                    max: newConfig?.max || null,
                    mapping: { ...(newConfig?.mapping || {}) }
                };
            }
        }
    },
    methods: {
        addMapping() {
            if (this.newMappingKey === null || !this.newMappingValue.trim()) return;
            
            if (!this.localConfig.mapping) this.localConfig.mapping = {};
            this.localConfig.mapping[this.newMappingKey] = this.newMappingValue.trim();
            
            this.updateConfig();
            this.newMappingKey = null;
            this.newMappingValue = "";
        },
        removeMapping(key) {
            if (this.localConfig?.mapping) {
                delete this.localConfig.mapping[key];
                this.updateConfig();
            }
        },
        updateConfig() {
            // Update the node's config
            this.node.config = { ...this.localConfig };
            
            // Emit the update event
            this.$emit("update-config", {
                node: this.node,
                config: this.node.config,
            });
        }
    }
};
</script>

<style scoped>
.btn-close {
    font-size: 0.7em;
}

.badge {
    font-size: 0.85rem;
}

.text-muted.small {
    font-size: 0.8rem;
}

.form-control {
    font-size: 0.9rem;
}

.btn-sm {
    font-size: 0.8rem;
}
</style>
