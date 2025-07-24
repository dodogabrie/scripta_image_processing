<template>
  <div v-if="processing || progressData.total > 0" class="card mb-3 animate-fade-in">
    <div class="card-header">
      <h5 class="mb-0">
        <i class="bi bi-gear-fill"></i> Elaborazione in corso...
      </h5>
    </div>
    <div class="card-body">
      <!-- Overall Progress -->
      <div class="mb-3">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <span class="fw-bold">Progresso Generale</span>
          <span class="badge bg-primary">{{ progressData.current || 0 }}/{{ progressData.total || 0 }}</span>
        </div>
        <div class="progress mb-2" style="height: 8px;">
          <div 
            class="progress-bar progress-bar-striped progress-bar-animated" 
            :style="{ width: (progressData.percentage || 0) + '%' }"
            :class="progressData.percentage === 100 ? 'bg-success' : 'bg-primary'"
          ></div>
        </div>
        <small class="text-muted">{{ (progressData.percentage || 0).toFixed(1) }}% completato</small>
      </div>
      
      <!-- Current File -->
      <div v-if="currentFile" class="mb-3 animate-fade-in">
        <div class="d-flex align-items-center mb-2">
          <i class="bi bi-file-earmark-arrow-down me-2 text-primary"></i>
          <strong>File corrente:</strong>
          <span class="ms-2 text-primary">{{ currentFile.filename }}</span>
          <span class="badge bg-secondary ms-auto">{{ formatBytes(currentFile.size || 0) }}</span>
        </div>
        <div class="progress" style="height: 4px;">
          <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" style="width: 100%"></div>
        </div>
      </div>
      
      <!-- Stats -->
      <div class="row">
        <div class="col-md-3">
          <div class="text-center stats-card">
            <div class="h4 text-success mb-0">{{ progressData.files_optimized || 0 }}</div>
            <small class="text-muted">Ottimizzati</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="text-center stats-card">
            <div class="h4 text-warning mb-0">{{ progressData.files_skipped || 0 }}</div>
            <small class="text-muted">Saltati</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="text-center stats-card">
            <div class="h4 text-danger mb-0">{{ progressData.errors || 0 }}</div>
            <small class="text-muted">Errori</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="text-center stats-card">
            <div class="h4 text-info mb-0">{{ formatBytes(progressData.bytes_saved || 0) }}</div>
            <small class="text-muted">Risparmiati</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * ProgressSection Component
 * Visualizza il progresso dell'elaborazione in tempo reale
 */
export default {
  name: 'ProgressSection',
  
  props: {
    processing: {
      type: Boolean,
      default: false
    },
    progressData: {
      type: Object,
      required: true
    },
    currentFile: {
      type: Object,
      default: null
    }
  },
  
  methods: {
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

.progress {
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar {
  transition: width 0.6s ease;
  border-radius: 10px;
}

.progress-bar-striped {
  background-image: linear-gradient(45deg, rgba(255, 255, 255, .15) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, .15) 50%, rgba(255, 255, 255, .15) 75%, transparent 75%, transparent);
  background-size: 1rem 1rem;
}

.progress-bar-animated {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% { background-position: 1rem 0; }
  100% { background-position: 0 0; }
}

.stats-card {
  padding: 0.5rem;
  transition: transform 0.2s ease-in-out;
}

.stats-card:hover {
  transform: translateY(-2px);
}

.h4 {
  font-weight: 600;
}

.badge {
  border-radius: 20px;
  font-size: 0.75em;
  padding: 0.375rem 0.75rem;
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
.text-info { color: #0dcaf0 !important; }
.text-primary { color: #0d6efd !important; }
</style>
