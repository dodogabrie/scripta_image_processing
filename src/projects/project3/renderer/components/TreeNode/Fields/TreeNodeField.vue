<template>
    <div
        class="border-start border-3 ps-3 mb-2 bg-ligh    methods: {
        handleDelete() {
            this.$emit('delete-node', this.node.id);
        },
        handleConfigUpdate(config) {
            // Update config directly on the node
            this.node.config = { ...config };
        }
    },-2"
        :class="getFieldClass"
    >
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div class="d-flex align-items-center">
                <span class="badge me-2" :class="getFieldBadgeClass">
                    {{ getFieldIcon }} {{ node.name }}
                </span>
            </div>
            <button
                @click="handleDelete"
                class="btn btn-sm btn-outline-danger"
                title="Elimina campo"
            >
                🗑️
            </button>
        </div>

        <!-- Field Configuration Components -->
        <FieldChoicesConfig
            v-if="node.fieldType === 'choices'"
            :node="node"
            @update-config="handleConfigUpdate"
        />

        <FieldNumericConfig
            v-if="node.fieldType === 'numeric'"
            :node="node"
            @update-config="handleConfigUpdate"
        />
    </div>
</template>

<script>
import FieldChoicesConfig from './FieldChoicesConfig.vue';
import FieldNumericConfig from './FieldNumericConfig.vue';

export default {
    name: "TreeNodeField",
    components: {
        FieldChoicesConfig,
        FieldNumericConfig
    },
    props: {
        node: { type: Object, required: true }
    },
    computed: {
        getFieldClass() {
            const classes = {
                text: "border-info",
                choices: "border-success",
                numeric: "border-warning",
            };
            return classes[this.node.fieldType] || "border-secondary";
        },
        getFieldBadgeClass() {
            const classes = {
                text: "bg-info",
                choices: "bg-success",
                numeric: "bg-warning text-dark",
            };
            return classes[this.node.fieldType] || "bg-secondary";
        },
        getFieldIcon() {
            const icons = {
                text: "📝",
                choices: "🔘",
                numeric: "🔢",
            };
            return icons[this.node.fieldType] || "🏷️";
        }
    },
    methods: {
        handleDelete() {
            this.$emit('node-action', {
                type: 'delete-node',
                nodeId: this.node.id
            });
        },
        handleConfigUpdate(config) {
            this.$emit('node-action', {
                type: 'update-field-config',
                fieldId: this.node.id,
                config
            });
        }
    }
};
</script>

<style scoped>
.badge {
    font-size: 0.9rem;
}

.btn-sm {
    font-size: 0.8rem;
}
</style>
