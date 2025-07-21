<template>
    <div class="mb-2">
        <div class="d-flex align-items-center mb-2">
            <input
                v-model="newOption"
                placeholder="Nuova opzione"
                class="form-control me-2"
                @keyup.enter="addOption"
            />
            <button
                @click="addOption"
                class="btn btn-sm btn-outline-primary"
                :disabled="!newOption.trim()"
            >
                ➕
            </button>
        </div>
        <div
            v-if="node.config?.options?.length > 0"
            class="d-flex flex-wrap gap-1"
        >
            <span
                v-for="option in node.config.options"
                :key="option"
                class="badge bg-secondary d-flex align-items-center"
            >
                {{ option }}
                <button
                    @click="removeOption(option)"
                    class="btn-close btn-close-white ms-1"
                    :aria-label="`Rimuovi opzione ${option}`"
                ></button>
            </span>
        </div>
        <div v-if="node.config?.options?.length === 0" class="text-muted small">
            Nessuna opzione configurata. Aggiungi delle opzioni per questo campo.
        </div>
    </div>
</template>

<script>
export default {
    name: "FieldChoicesConfig",
    props: {
        node: { type: Object, required: true }
    },
    data() {
        return {
            newOption: ""
        };
    },
    methods: {
        addOption() {
            if (!this.newOption.trim()) return;
            if (!this.node.config) this.node.config = { options: [] };
            if (!this.node.config.options) this.node.config.options = [];
            
            if (!this.node.config.options.includes(this.newOption.trim())) {
                this.node.config.options.push(this.newOption.trim());
                this.updateConfig();
            }
            this.newOption = "";
        },
        removeOption(option) {
            if (this.node.config?.options) {
                this.node.config.options = this.node.config.options.filter(
                    (o) => o !== option
                );
                this.updateConfig();
            }
        },
        updateConfig() {
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
    font-style: italic;
}

.form-control {
    font-size: 0.9rem;
}
</style>
