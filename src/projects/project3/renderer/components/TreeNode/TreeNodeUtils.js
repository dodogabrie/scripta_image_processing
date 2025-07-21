/**
 * TreeNode Utilities
 *
 * Utility functions for TreeNode component operations including:
 * - Data validation
 * - Export/Import functionality
 * - Tree traversal and manipulation
 * - Schema validation
 */

/**
 * Field type definitions and validation schemas
 */
export const FIELD_TYPES = {
    TEXT: 'text',
    CHOICES: 'choices',
    NUMERIC: 'numeric'
};

export const NUMERIC_TYPES = {
    INTEGER: 'integer',
    FLOAT: 'float',
    RANGE: 'range'
};

/**
 * Default configurations for each field type
 */
export const DEFAULT_CONFIGS = {
    [FIELD_TYPES.TEXT]: {},
    [FIELD_TYPES.CHOICES]: {
        options: [],
        multiSelect: false
    },
    [FIELD_TYPES.NUMERIC]: {
        numericType: NUMERIC_TYPES.INTEGER,
        min: null,
        max: null,
        availableNumbers: [],
        allowDecimals: false
    }
};

/**
 * Validation functions for different field types
 */
export const VALIDATORS = {
    [FIELD_TYPES.TEXT]: {
        value: (value, config) => typeof value === 'string',
        config: (config) => true
    },

    [FIELD_TYPES.CHOICES]: {
        value: (value, config) => {
            if (!config.options || !Array.isArray(config.options)) return false;
            return config.options.includes(value);
        },
        config: (config) => {
            return config.options && Array.isArray(config.options) &&
                   typeof config.multiSelect === 'boolean';
        }
    },

    [FIELD_TYPES.NUMERIC]: {
        value: (value, config) => {
            const numValue = Number(value);
            if (isNaN(numValue)) return false;

            switch (config.numericType) {
                case NUMERIC_TYPES.INTEGER:
                    if (!Number.isInteger(numValue)) return false;
                    break;
                case NUMERIC_TYPES.FLOAT:
                    // Any number is valid for float
                    break;
                case NUMERIC_TYPES.RANGE:
                    if (!config.availableNumbers || !config.availableNumbers.includes(numValue)) {
                        return false;
                    }
                    if (!config.allowDecimals && !Number.isInteger(numValue)) {
                        return false;
                    }
                    break;
                default:
                    return false;
            }

            // Check min/max bounds for integer and float
            if (config.numericType !== NUMERIC_TYPES.RANGE) {
                if (config.min !== null && numValue < config.min) return false;
                if (config.max !== null && numValue > config.max) return false;
            }

            return true;
        },
        config: (config) => {
            const validTypes = Object.values(NUMERIC_TYPES);
            if (!validTypes.includes(config.numericType)) return false;

            if (config.numericType === NUMERIC_TYPES.RANGE) {
                return Array.isArray(config.availableNumbers) &&
                       typeof config.allowDecimals === 'boolean';
            }

            return true;
        }
    }
};

/**
 * Tree traversal utilities
 */
export class TreeTraversal {
    /**
     * Find a node by ID in the tree
     */
    static findNodeById(tree, targetId) {
        if (tree.id === targetId) {
            return tree;
        }

        if (tree.children && Array.isArray(tree.children)) {
            for (const child of tree.children) {
                const found = this.findNodeById(child, targetId);
                if (found) return found;
            }
        }

        return null;
    }

    /**
     * Get all nodes of a specific type
     */
    static getNodesByType(tree, type) {
        const results = [];

        if (tree.type === type) {
            results.push(tree);
        }

        if (tree.children && Array.isArray(tree.children)) {
            for (const child of tree.children) {
                results.push(...this.getNodesByType(child, type));
            }
        }

        return results;
    }

    /**
     * Get all fields of a specific field type
     */
    static getFieldsByFieldType(tree, fieldType) {
        const fields = this.getNodesByType(tree, 'field');
        return fields.filter(field => field.fieldType === fieldType);
    }

    /**
     * Get the path to a node (array of node names from root)
     */
    static getNodePath(tree, targetId, currentPath = []) {
        const newPath = [...currentPath, tree.name];

        if (tree.id === targetId) {
            return newPath;
        }

        if (tree.children && Array.isArray(tree.children)) {
            for (const child of tree.children) {
                const foundPath = this.getNodePath(child, targetId, newPath);
                if (foundPath) return foundPath;
            }
        }

        return null;
    }

    /**
     * Calculate tree statistics
     */
    static getTreeStats(tree) {
        const stats = {
            totalNodes: 0,
            totalFields: 0,
            fieldTypes: {},
            maxDepth: 0,
            totalValues: 0
        };

        this._calculateStats(tree, stats, 0);
        return stats;
    }

    static _calculateStats(node, stats, depth) {
        stats.maxDepth = Math.max(stats.maxDepth, depth);

        if (node.type === 'field') {
            stats.totalFields++;
            stats.fieldTypes[node.fieldType] = (stats.fieldTypes[node.fieldType] || 0) + 1;
            if (node.values) {
                stats.totalValues += node.values.length;
            }
        } else {
            stats.totalNodes++;
        }

        if (node.children && Array.isArray(node.children)) {
            for (const child of node.children) {
                this._calculateStats(child, stats, depth + 1);
            }
        }
    }
}

/**
 * Validation utilities
 */
export class TreeValidator {
    /**
     * Validate a complete tree structure
     */
    static validateTree(tree) {
        const errors = [];
        this._validateNode(tree, errors, []);
        return {
            isValid: errors.length === 0,
            errors
        };
    }

    static _validateNode(node, errors, path) {
        const currentPath = [...path, node.name || node.id];

        // Basic node validation
        if (!node.id) {
            errors.push(`Node at ${currentPath.join(' > ')} is missing ID`);
        }
        if (!node.name) {
            errors.push(`Node at ${currentPath.join(' > ')} is missing name`);
        }
        if (!node.type) {
            errors.push(`Node at ${currentPath.join(' > ')} is missing type`);
        }

        // Field-specific validation
        if (node.type === 'field') {
            this._validateField(node, errors, currentPath);
        }

        // Validate children
        if (node.children && Array.isArray(node.children)) {
            for (const child of node.children) {
                this._validateNode(child, errors, currentPath);
            }
        }
    }

    static _validateField(field, errors, path) {
        if (!field.fieldType) {
            errors.push(`Field at ${path.join(' > ')} is missing fieldType`);
            return;
        }

        if (!Object.values(FIELD_TYPES).includes(field.fieldType)) {
            errors.push(`Field at ${path.join(' > ')} has invalid fieldType: ${field.fieldType}`);
            return;
        }

        // Validate config
        const configValidator = VALIDATORS[field.fieldType].config;
        if (!configValidator(field.config || {})) {
            errors.push(`Field at ${path.join(' > ')} has invalid configuration`);
        }

        // Validate values
        if (field.values && Array.isArray(field.values)) {
            const valueValidator = VALIDATORS[field.fieldType].value;
            field.values.forEach((value, index) => {
                if (!valueValidator(value, field.config || {})) {
                    errors.push(`Field at ${path.join(' > ')} has invalid value at index ${index}: ${value}`);
                }
            });
        }
    }

    /**
     * Validate a single field value
     */
    static validateFieldValue(fieldType, value, config) {
        if (!VALIDATORS[fieldType]) return false;
        return VALIDATORS[fieldType].value(value, config || {});
    }

    /**
     * Validate field configuration
     */
    static validateFieldConfig(fieldType, config) {
        if (!VALIDATORS[fieldType]) return false;
        return VALIDATORS[fieldType].config(config || {});
    }
}

/**
 * Export utilities
 */
export class TreeExporter {
    /**
     * Export tree to JSON with metadata
     */
    static exportToJSON(tree, options = {}) {
        const {
            includeMetadata = true,
            includeStats = true,
            includeSchema = false,
            includeIds = true,
            includeValues = true,
            pretty = true
        } = options;

        const exportData = {
            version: '1.0',
            exportDate: new Date().toISOString(),
            data: this._cleanTreeForExport(tree, { includeIds, includeValues })
        };

        if (includeMetadata) {
            exportData.metadata = this._generateMetadata(tree);
        }

        if (includeStats) {
            exportData.stats = TreeTraversal.getTreeStats(tree);
        }

        if (includeSchema) {
            exportData.schema = this._generateSchema(tree);
        }

        return pretty ? JSON.stringify(exportData, null, 2) : JSON.stringify(exportData);
    }

    /**
     * Export only data values (without structure metadata)
     */
    static exportDataOnly(tree) {
        return this._extractDataValues(tree);
    }

    /**
     * Export as CSV (flattened structure)
     */
    static exportToCSV(tree) {
        const flatData = this._flattenTreeData(tree);
        if (flatData.length === 0) return '';

        const headers = Object.keys(flatData[0]);
        const csvRows = [
            headers.join(','),
            ...flatData.map(row =>
                headers.map(header =>
                    JSON.stringify(row[header] || '')
                ).join(',')
            )
        ];

        return csvRows.join('\n');
    }

    static _cleanTreeForExport(node, options = {}) {
        const { includeIds = true, includeValues = true } = options;
        
        const cleaned = {
            name: node.name,
            type: node.type
        };

        if (includeIds) {
            cleaned.id = node.id;
        }

        if (node.type === 'field') {
            cleaned.fieldType = node.fieldType;
            cleaned.config = { ...node.config };
            if (includeValues) {
                cleaned.values = [...(node.values || [])];
            }
        }

        if (node.children && node.children.length > 0) {
            cleaned.children = node.children.map(child => this._cleanTreeForExport(child, options));
        }

        return cleaned;
    }

    static _generateMetadata(tree) {
        return {
            rootName: tree.name,
            rootId: tree.id,
            created: new Date().toISOString(),
            structure: 'hierarchical',
            fieldTypes: Object.keys(FIELD_TYPES)
        };
    }

    static _generateSchema(tree) {
        const schema = {
            nodes: [],
            fields: {}
        };

        this._extractSchemaInfo(tree, schema);
        return schema;
    }

    static _extractSchemaInfo(node, schema, path = []) {
        const currentPath = [...path, node.name];

        if (node.type === 'field') {
            const fieldSchema = {
                path: currentPath.join('.'),
                fieldType: node.fieldType,
                config: { ...node.config },
                required: false, // Could be extended
                description: '' // Could be extended
            };

            if (!schema.fields[node.fieldType]) {
                schema.fields[node.fieldType] = [];
            }
            schema.fields[node.fieldType].push(fieldSchema);
        } else {
            schema.nodes.push({
                path: currentPath.join('.'),
                name: node.name,
                childCount: node.children ? node.children.length : 0
            });
        }

        if (node.children) {
            for (const child of node.children) {
                this._extractSchemaInfo(child, schema, currentPath);
            }
        }
    }

    static _extractDataValues(node, result = {}, path = []) {
        const currentPath = [...path, node.name];
        const pathKey = currentPath.join('.');

        if (node.type === 'field' && node.values && node.values.length > 0) {
            result[pathKey] = {
                fieldType: node.fieldType,
                values: [...node.values],
                config: { ...node.config }
            };
        }

        if (node.children) {
            for (const child of node.children) {
                this._extractDataValues(child, result, currentPath);
            }
        }

        return result;
    }

    static _flattenTreeData(tree) {
        const flatData = [];
        this._flattenNode(tree, flatData, {});
        return flatData;
    }

    static _flattenNode(node, results, currentRow, path = []) {
        const currentPath = [...path, node.name];
        const pathKey = currentPath.join('_').replace(/[^a-zA-Z0-9_]/g, '_');

        if (node.type === 'field' && node.values) {
            // For each value, create a row
            if (node.values.length === 0) {
                currentRow[pathKey] = '';
            } else {
                // If multiple values, create multiple rows or join them
                node.values.forEach((value, index) => {
                    const row = { ...currentRow };
                    row[pathKey] = value;
                    row[`${pathKey}_type`] = node.fieldType;
                    if (index === node.values.length - 1) {
                        results.push(row);
                    }
                });
            }
        }

        if (node.children) {
            for (const child of node.children) {
                this._flattenNode(child, results, { ...currentRow }, currentPath);
            }
        }
    }
}

/**
 * Import utilities
 */
export class TreeImporter {
    /**
     * Import from JSON with validation
     */
    static importFromJSON(jsonData) {
        try {
            const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;

            // Handle different import formats
            let treeData;
            if (data.data) {
                // Full export format
                treeData = data.data;
            } else if (data.id && data.name && data.type) {
                // Direct tree format
                treeData = data;
            } else {
                throw new Error('Invalid import format');
            }

            // Validate and clean the imported data
            const cleanedTree = this._cleanImportedTree(treeData);
            const validation = TreeValidator.validateTree(cleanedTree);

            return {
                success: validation.isValid,
                tree: cleanedTree,
                errors: validation.errors,
                metadata: data.metadata || null,
                stats: data.stats || null
            };
        } catch (error) {
            return {
                success: false,
                tree: null,
                errors: [`Import failed: ${error.message}`],
                metadata: null,
                stats: null
            };
        }
    }

    static _cleanImportedTree(node) {
        const cleaned = {
            id: node.id || `imported_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            name: node.name || 'Unnamed',
            type: node.type || 'node'
        };

        if (node.type === 'field') {
            cleaned.fieldType = node.fieldType || FIELD_TYPES.TEXT;
            cleaned.config = {
                ...DEFAULT_CONFIGS[cleaned.fieldType],
                ...(node.config || {})
            };
            // Initialize values array even if not imported
            cleaned.values = Array.isArray(node.values) ? [...node.values] : [];
        }

        if (node.children && Array.isArray(node.children)) {
            cleaned.children = node.children.map(child => this._cleanImportedTree(child));
        } else {
            cleaned.children = [];
        }

        return cleaned;
    }
}

/**
 * Tree manipulation utilities
 */
export class TreeManipulator {
    /**
     * Deep clone a tree structure
     */
    static cloneTree(tree) {
        return JSON.parse(JSON.stringify(tree));
    }

    /**
     * Add a node to a parent
     */
    static addNode(tree, parentId, newNode) {
        const parent = TreeTraversal.findNodeById(tree, parentId);
        if (parent) {
            if (!parent.children) parent.children = [];
            parent.children.push(newNode);
            return true;
        }
        return false;
    }

    /**
     * Remove a node by ID
     */
    static removeNode(tree, nodeId) {
        return this._removeNodeRecursive(tree, nodeId);
    }

    static _removeNodeRecursive(node, targetId) {
        if (node.children) {
            for (let i = 0; i < node.children.length; i++) {
                if (node.children[i].id === targetId) {
                    node.children.splice(i, 1);
                    return true;
                }
                if (this._removeNodeRecursive(node.children[i], targetId)) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Move a node to a new parent
     */
    static moveNode(tree, nodeId, newParentId) {
        const nodeToMove = TreeTraversal.findNodeById(tree, nodeId);
        if (!nodeToMove) return false;

        // Clone the node before removing
        const clonedNode = this.cloneTree(nodeToMove);

        // Remove from current location
        if (this.removeNode(tree, nodeId)) {
            // Add to new location
            return this.addNode(tree, newParentId, clonedNode);
        }

        return false;
    }

    /**
     * Update node properties
     */
    static updateNode(tree, nodeId, updates) {
        const node = TreeTraversal.findNodeById(tree, nodeId);
        if (node) {
            Object.assign(node, updates);
            return true;
        }
        return false;
    }

    /**
     * Merge two trees
     */
    static mergeTrees(tree1, tree2, mergeStrategy = 'append') {
        const merged = this.cloneTree(tree1);

        switch (mergeStrategy) {
            case 'append':
                if (!merged.children) merged.children = [];
                merged.children.push(...(tree2.children || []));
                break;
            case 'replace':
                merged.children = tree2.children || [];
                break;
            default:
                throw new Error(`Unknown merge strategy: ${mergeStrategy}`);
        }

        return merged;
    }
}

/**
 * Helper functions for common operations
 */
export const TreeHelpers = {
    /**
     * Generate a unique ID
     */
    generateId: (prefix = 'node') => `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,

    /**
     * Create a new node template
     */
    createNode: (name, type = 'node') => ({
        id: TreeHelpers.generateId(type),
        name,
        type,
        children: []
    }),

    /**
     * Create a new field template
     */
    createField: (name, fieldType = FIELD_TYPES.TEXT) => ({
        id: TreeHelpers.generateId('field'),
        name,
        type: 'field',
        fieldType,
        config: { ...DEFAULT_CONFIGS[fieldType] },
        values: [],
        children: []
    }),

    /**
     * Check if a node is a field
     */
    isField: (node) => node && node.type === 'field',

    /**
     * Check if a node is a container node
     */
    isNode: (node) => node && node.type !== 'field',

    /**
     * Get field type icon
     */
    getFieldIcon: (fieldType) => {
        const icons = {
            [FIELD_TYPES.TEXT]: '📝',
            [FIELD_TYPES.CHOICES]: '🔘',
            [FIELD_TYPES.NUMERIC]: '🔢'
        };
        return icons[fieldType] || '🏷️';
    },

    /**
     * Format field value for display
     */
    formatFieldValue: (value, fieldType) => {
        switch (fieldType) {
            case FIELD_TYPES.NUMERIC:
                return Number(value).toString();
            case FIELD_TYPES.TEXT:
            case FIELD_TYPES.CHOICES:
            default:
                return String(value);
        }
    }
};

// Export everything as default for easier imports
export default {
    FIELD_TYPES,
    NUMERIC_TYPES,
    DEFAULT_CONFIGS,
    VALIDATORS,
    TreeTraversal,
    TreeValidator,
    TreeExporter,
    TreeImporter,
    TreeManipulator,
    TreeHelpers
};
