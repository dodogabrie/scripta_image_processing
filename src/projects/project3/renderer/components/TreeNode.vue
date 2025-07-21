<template>
    <!-- Use TreeNodeContainer for nodes -->
    <TreeNodeContainer
        v-if="node.type === 'node'"
        :node="node"
        @add-child="(parentId, childName) => $emit('add-child', parentId, childName)"
        @add-field="(parentId, fieldName, fieldType, fieldConfig) => $emit('add-field', parentId, fieldName, fieldType, fieldConfig)"
        @delete-node="(nodeId) => $emit('delete-node', nodeId)"
        @update-config="$emit('update-config', $event)"
    />

    <!-- Use TreeNodeField for fields -->
    <TreeNodeField
        v-else
        :node="node"
        @delete-node="(nodeId) => $emit('delete-node', nodeId)"
        @update-config="$emit('update-config', $event)"
    />
</template>

<script>
import TreeNodeContainer from './TreeNode/TreeNodeContainer.vue';
import TreeNodeField from './TreeNodeField.vue';

export default {
    name: "TreeNode",
    components: {
        TreeNodeContainer,
        TreeNodeField
    },
    props: {
        node: { type: Object, required: true }
    }
};
</script>

<style scoped>
/* Base styles are now handled by individual components */
</style>
