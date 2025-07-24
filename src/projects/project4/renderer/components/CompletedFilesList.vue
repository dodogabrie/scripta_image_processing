<template>
  <div v-if="completedFiles.length > 0" class="card mb-3 animate-fade-in">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h6 class="mb-0">
        <i class="bi bi-list-check"></i> File Elaborati
      </h6>
      <div class="d-flex align-items-center gap-2">
        <small class="text-muted">{{ completedFiles.length }} file</small>
        <button 
          @click="toggleExpanded" 
          class="btn btn-sm btn-outline-secondary"
          :title="expanded ? 'Comprimi lista' : 'Espandi lista'"
        >
          <i :class="expanded ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
        </button>
      </div>
    </div>
    <div v-show="expanded" class="card-body files-list">
      <div 
        v-for="file in reversedFiles" 
        :key="file.path" 
        class="file-item d-flex align-items-center mb-2"
      >
        <i v-if="file.error" class="bi bi-x-circle-fill text-danger me-2"></i>
        <i v-else-if="file.skipped" class="bi bi-skip-forward-fill text-warning me-2"></i>
        <i v-else class="bi bi-check-circle-fill text-success me-2"></i>
        
        <div class="flex-grow-1">
          <div class="fw-bold file-name">{{ file.filename }}</div>
          <div v-if="file.error" class="small text-danger">{{ file.error }}</div>
          <div v-else-if="file.skipped" class="small text-warning">File saltato</div>
          <div v-else class="small text-muted">
            {{ formatBytes(file.original_size) }} → {{ formatBytes(file.optimized_size) }}
            <span class="text-success">({{ file.reduction_percent?.toFixed(1) }}% riduzione)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * CompletedFilesList Component
 * Visualizza la lista dei file elaborati con i risultati
 */
export default {
  name: 'CompletedFilesList',
  
  props: {
    completedFiles: {
      type: Array,
      default: () => []
    }
  },
  
  data() {
    return {
      expanded: true
    };
  },
  
  computed: {
    /**
     * File in ordine inverso (più recenti in alto)
     */
    reversedFiles() {
      return [...this.completedFiles].reverse();
    }
  },
  
  methods: {
    /**
     * Toggle della visibilità della lista
     */
    toggleExpanded() {
      this.expanded = !this.expanded;
    },
    
    /**
     * Formatta i bytes in formato leggibile
     * @param {number} bytes - Numero di bytes
     * @returns {string} Stringa formattata
     */
    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      
      const units = ['B', 'KB', 'MB', 'GB', 'TB'];
      const factor = 1024;
      let unitIndex = 0;
      let size = bytes;
      
      while (size >= factor && unitIndex < units.length - 1) {
        size /= factor;
        unitIndex++;
      }
      
      return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
    }
  }
};
</script>

<style scoped>
.card {
  transition: all 0.3s ease-in-out;
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.files-list {
  max-height: 300px;
  overflow-y: auto;
}

.files-list::-webkit-scrollbar {
  width: 6px;
}

.files-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.files-list::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.files-list::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.file-item {
  padding: 0.5rem;
  border-radius: 6px;
  transition: background-color 0.2s ease-in-out;
}

.file-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.file-name {
  word-break: break-word;
  line-height: 1.2;
}

.btn {
  border-radius: 6px;
  transition: all 0.2s ease-in-out;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.text-success { color: #198754 !important; }
.text-warning { color: #ffc107 !important; }
.text-danger { color: #dc3545 !important; }
</style>
