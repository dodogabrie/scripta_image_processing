// TreeNode System Components Export
// Facilitates importing all TreeNode components

import TreeNode from './TreeNode.vue';
import TreeNodeContainer from './TreeNodeContainer.vue';
import TreeNodeField from './Fields/TreeNodeField.vue';
import TreeNodeAddControls from './AddNode/TreeNodeAddControls.vue/index.jsrols.vue';
import FieldChoicesConfig from './Fields/FieldChoicesConfig.vue';
import FieldNumericConfig from './Fields/FieldNumericConfig.vue';

// Also export utility components
import ImportTreeData from './TreeNodeJson/ImportTreeData.vue';
import ExportTreeData from './TreeNodeJson/ExportTreeData.vue';

// Export utilities
import TreeNodeUtils from '../TreeNodeUtils.js';

// Main component (recommended for most use cases)
export default TreeNode;

// Individual components for advanced usage
export {
    TreeNode,
    TreeNodeContainer,
    TreeNodeField,
    TreeNodeAddControls,
    FieldChoicesConfig,
    FieldNumericConfig,
    ImportTreeData,
    ExportTreeData,
    TreeNodeUtils
};

// Convenience groupings
export const TreeNodeComponents = {
    TreeNode,
    TreeNodeContainer,
    TreeNodeField,
    TreeNodeAddControls,
    FieldChoicesConfig,
    FieldNumericConfig
};

export const TreeDataComponents = {
    ImportTreeData,
    ExportTreeData
};

export const TreeUtilities = TreeNodeUtils;

/**
 * Usage examples:
 * 
 * // Simple import (recommended)
 * import TreeNode from './components/TreeNode/TreeNodeSystem';
 * 
 * // Selective import
 * import { TreeNodeContainer, FieldChoicesConfig } from './components/TreeNode/TreeNodeSystem';
 * 
 * // Grouped import
 * import { TreeNodeComponents, TreeDataComponents } from './components/TreeNode/TreeNodeSystem';
 * 
 * // All utilities
 * import { TreeUtilities } from './components/TreeNode/TreeNodeSystem';
 */
