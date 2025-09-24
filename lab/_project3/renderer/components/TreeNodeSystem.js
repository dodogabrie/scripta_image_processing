// TreeNode System Components Export
// Facilitates importing all TreeNode components

import TreeNode from './TreeNode/TreeNode.vue';
import TreeNodeContainer from './TreeNode/TreeNodeContainer.vue';
import TreeNodeField from './TreeNodeField.vue';
import TreeNodeAddControls from './TreeNodeAddControls.vue';
import FieldChoicesConfig from './FieldChoicesConfig.vue';
import FieldNumericConfig from './FieldNumericConfig.vue';

// Also export utility components
import ImportTreeData from './ImportTreeData.vue';
import ExportTreeData from './ExportTreeData.vue';

// Export utilities
import TreeNodeUtils from './TreeNodeUtils.js';

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
 * import TreeNode from './components/TreeNodeSystem';
 * 
 * // Selective import
 * import { TreeNodeContainer, FieldChoicesConfig } from './components/TreeNodeSystem';
 * 
 * // Grouped import
 * import { TreeNodeComponents, TreeDataComponents } from './components/TreeNodeSystem';
 * 
 * // All utilities
 * import { TreeUtilities } from './components/TreeNodeSystem';
 */
