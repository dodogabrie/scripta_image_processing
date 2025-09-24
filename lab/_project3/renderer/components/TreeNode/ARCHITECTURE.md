# TreeNode Architecture Refactor

## Problem Addressed

The original TreeNode components were violating the **Separation of Concerns** principle by:
1. Handling business logic within presentational components
2. Being tightly coupled to Project3's specific needs
3. Making the components non-reusable
4. Creating complex event bubbling chains

## New Architecture

### 1. Unified Action System
All TreeNode components now emit a single `node-action` event with a structured payload:
```javascript
{
    type: 'add-child' | 'add-field' | 'delete-node' | 'update-field-config' | 'add-value' | 'remove-value',
    // Action-specific data...
}
```

### 2. Actions Configuration
TreeNode components receive an `actions` prop that defines what operations are allowed:
```javascript
treeActions: {
    allowAddChild: true,
    allowAddField: true,
    allowDelete: true,
    allowEdit: true
}
```

### 3. Business Logic Centralization
All business logic is now handled in the ProjectProject3Component:
- `handleNodeAction()` - Central dispatcher for all tree operations
- Individual methods for each operation (addChildNode, deleteNode, etc.)

## Benefits

1. **Reusability**: TreeNode components can now be used in any project with different action configurations
2. **Maintainability**: Business logic is centralized in one place
3. **Testability**: Each component has a single responsibility
4. **Flexibility**: Easy to add/remove actions or change behavior per project

## Component Responsibilities

### TreeNode.vue
- **Purpose**: Routing component that decides between Container/Field
- **Responsibility**: Pass props and forward events
- **Business Logic**: None

### TreeNodeContainer.vue
- **Purpose**: Display node containers with children
- **Responsibility**: Render UI and emit actions
- **Business Logic**: None (only UI state)

### TreeNodeField.vue
- **Purpose**: Display field nodes with configurations
- **Responsibility**: Render field UI and emit actions
- **Business Logic**: None (only UI state)

### TreeNodeAddControls.vue
- **Purpose**: Form controls for adding children/fields
- **Responsibility**: Form validation and emit add actions
- **Business Logic**: Only form validation

### ProjectProject3Component.vue
- **Purpose**: Business logic and data management
- **Responsibility**: Handle all tree operations, data persistence, export/import
- **Business Logic**: All tree manipulation logic

## Migration Notes

Projects using TreeNode components should:
1. Define an `actions` configuration object
2. Handle the `node-action` event instead of individual events
3. Implement business logic in the parent component
4. Pass the `actions` prop to TreeNode components
