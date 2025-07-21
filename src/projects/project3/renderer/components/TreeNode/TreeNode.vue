<template>
    <!-- Use TreeNodeContainer for nodes -->
    <TreeNodeContainer
        v-if="node.type === 'node'"
        :node="node"
        @delete-node="$emit('delete-node', $event)"
    />

    <!-- Use TreeNodeField for fields -->
    <TreeNodeField
        v-else
        :node="node"
        @delete-node="$emit('delete-node', $event)"
    />
</template>

<script>
import TreeNodeContainer from './TreeNodeContainer.vue';
import TreeNodeField from './Fields/TreeNodeField.vue';

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
