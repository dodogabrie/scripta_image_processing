<template>
    <div class="card border-primary mb-3">
        <div
            class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
        >
            <div>
                <h5 class="mb-0">📁 {{ node.name }}</h5>
            </div>
            <button
                @click="$emit('delete-node', node.id)"
                class="btn btn-sm btn-outline-light"
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
                    @add-child="(parentId, childName) => $emit('add-child', parentId, childName)"
                    @add-field="(parentId, fieldName, fieldType, fieldConfig) => $emit('add-field', parentId, fieldName, fieldType, fieldConfig)"
                    @delete-node="(nodeId) => $emit('delete-node', nodeId)"
                    @update-config="$emit('update-config', $event)"
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
            this.$emit('add-child', this.node.id, childName);
        },
        handleAddField(fieldName, fieldType, fieldConfig) {
            this.$emit('add-field', this.node.id, fieldName, fieldType, fieldConfig);
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
