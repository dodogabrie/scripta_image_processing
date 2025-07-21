<template>
    <div class="card border-primary mb-3">
        <div
            class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
        >
            <div>
                <h5 class="mb-0">📁 {{ node.name }}</h5>
            </div>
            <button
                @click="handleDelete"
                class="btn btn-sm btn-outline-light"
                title="Elimina nodo"
            >
                🗑️
            </button>
        </div>
        <div class="card-body">
            <!-- Add Controls Component -->
            <TreeNodeAddControls
                @add-child="handleAddChild"
                @add-field="handleAddField"
            />

            <!-- Children -->
            <div v-if="node.children?.length > 0">
                <component
                    :is="TreeNodeComponent"
                    v-for="child in node.children"
                    :key="child.id"
                    :node="child"
                    @delete-node="handleChildDelete"
                />
            </div>
        </div>
    </div>
</template>

<script>
import { markRaw } from 'vue';
import TreeNodeAddControls from './AddNode/TreeNodeAddControls.vue';

export default {
    name: "TreeNodeContainer",
    components: {
        TreeNodeAddControls
    },
    props: {
        node: { type: Object, required: true }
    },
    data() {
        return {
            TreeNodeComponent: null
        };
    },
    async created() {
        // Load TreeNode dynamically to avoid circular dependency
        try {
            const { default: TreeNode } = await import('./TreeNode.vue');
            // Use markRaw to prevent Vue from making the component reactive
            this.TreeNodeComponent = markRaw(TreeNode);
        } catch (error) {
            console.error("Failed to load TreeNode component:", error);
        }
    },
    methods: {
        handleAddChild(childName) {
            // Add child directly to this node
            this.node.children.push({
                id: this.generateId(),
                name: childName,
                type: "node",
                children: [],
            });
        },
        handleAddField(fieldName, fieldType, fieldConfig) {
            // Add field directly to this node
            this.node.children.push({
                id: this.generateId(),
                name: fieldName,
                type: "field",
                fieldType: fieldType,
                config: fieldConfig,
                values: [],
                children: [],
            });
        },
        handleDelete() {
            // Emit delete event to parent to remove this node
            this.$emit('delete-node', this.node.id);
        },
        handleChildDelete(childId) {
            // Handle deletion of child nodes
            const index = this.node.children.findIndex(child => child.id === childId);
            if (index !== -1) {
                this.node.children.splice(index, 1);
            }
        },
        generateId() {
            return 'node_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
    }
};
</script>

<style scoped>
.card {
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header.bg-primary {
    background: linear-gradient(135deg, #007bff, #0056b3) !important;
}

.btn-sm {
    font-size: 0.8rem;
}
</style>
