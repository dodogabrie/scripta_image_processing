<template>
  <div>
    <button @click="exportTreeData" class="btn btn-primary">
      📥 Export Data
    </button>
    <pre v-if="exportedData" class="mt-3 p-3 bg-light border rounded">
      {{ exportedData }}
    </pre>
  </div>
</template>

<script>
import { TreeExporter } from '../TreeNodeUtils';

export default {
  name: 'ExportTreeData',
  props: {
    treeData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      exportedData: null
    };
  },
  methods: {
    exportTreeData() {
      try {
        // Export without values and IDs, with metadata and stats
        const exportedJson = TreeExporter.exportToJSON(this.treeData, {
          includeMetadata: true,
          includeStats: true,
          includeIds: false,
          includeValues: false,
          pretty: true
        });

        this.exportedData = exportedJson;

        // Optional: Download as file
        this.downloadJson(exportedJson);
      } catch (error) {
        console.error('Export failed:', error);
      }
    },

    downloadJson(jsonData) {
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tree-export-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  }
};
</script>
