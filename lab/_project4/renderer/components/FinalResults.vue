<template>
  <div v-if="finalResults" class="card mb-3 animate-fade-in">
    <div class="card-header bg-success text-white">
      <h5 class="mb-0">
        <i class="bi bi-check-circle"></i> Elaborazione Completata!
      </h5>
    </div>
    <div class="card-body">
      <div class="row">
        <div class="col-md-6">
          <ul class="list-unstyled mb-0">
            <li class="result-item">
              <strong>File elaborati:</strong> 
              <span class="result-value">{{ finalResults.files_processed }}</span>
            </li>
            <li class="result-item">
              <strong>File ottimizzati:</strong> 
              <span class="result-value text-success">{{ finalResults.files_optimized }}</span>
            </li>
            <li class="result-item">
              <strong>File saltati:</strong> 
              <span class="result-value text-warning">{{ finalResults.files_skipped }}</span>
            </li>
            <li class="result-item">
              <strong>Errori:</strong> 
              <span class="result-value text-danger">{{ finalResults.errors }}</span>
            </li>
          </ul>
        </div>
        <div class="col-md-6">
          <ul class="list-unstyled mb-0">
            <li class="result-item">
              <strong>Spazio risparmiato:</strong> 
              <span class="result-value text-info">{{ formatBytes(finalResults.total_bytes_saved) }}</span>
            </li>
            <li class="result-item">
              <strong>Riduzione media:</strong> 
              <span class="result-value text-success">{{ finalResults.average_reduction?.toFixed(1) }}%</span>
            </li>
            <li class="result-item">
              <strong>Tempo impiegato:</strong> 
              <span class="result-value">{{ formatDuration(finalResults.duration_seconds) }}</span>
            </li>
            <li class="result-item">
              <strong>Velocità media:</strong> 
              <span class="result-value">{{ calculateSpeed() }}</span>
            </li>
          </ul>
        </div>
      </div>
      
      <!-- Summary Stats Cards -->
      <div class="row mt-4">
        <div class="col-md-3">
          <div class="summary-card text-center bg-light rounded p-3">
            <div class="h3 text-primary mb-1">{{ successRate }}%</div>
            <small class="text-muted">Tasso di successo</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="summary-card text-center bg-light rounded p-3">
            <div class="h3 text-success mb-1">{{ avgReduction }}%</div>
            <small class="text-muted">Riduzione media</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="summary-card text-center bg-light rounded p-3">
            <div class="h3 text-info mb-1">{{ formatBytes(totalSaved) }}</div>
            <small class="text-muted">Spazio totale risparmiato</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="summary-card text-center bg-light rounded p-3">
            <div class="h3 text-warning mb-1">{{ filesPerSecond }}</div>
            <small class="text-muted">File/sec</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * FinalResults Component
 * Visualizza i risultati finali dell'elaborazione con statistiche dettagliate
 */
export default {
  name: 'FinalResults',
  
  props: {
    finalResults: {
      type: Object,
      default: null
    }
  },
  
  computed: {
    /**
     * Calcola il tasso di successo in percentuale
     */
    successRate() {
      if (!this.finalResults || !this.finalResults.files_processed) return 0;
      const processed = this.finalResults.files_processed;
      const errors = this.finalResults.errors || 0;
      return Math.round(((processed - errors) / processed) * 100);
    },
    
    /**
     * Riduzione media formattata
     */
    avgReduction() {
      return this.finalResults?.average_reduction?.toFixed(1) || 0;
    },
    
    /**
     * Spazio totale risparmiato
     */
    totalSaved() {
      return this.finalResults?.total_bytes_saved || 0;
    },
    
    /**
     * File processati per secondo
     */
    filesPerSecond() {
      if (!this.finalResults || !this.finalResults.duration_seconds) return '0';
      const rate = this.finalResults.files_processed / this.finalResults.duration_seconds;
      return rate.toFixed(1);
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
    },
    
    /**
     * Formatta la durata in formato leggibile
     * @param {number} seconds - Durata in secondi
     * @returns {string} Durata formattata
     */
    formatDuration(seconds) {
      if (!seconds) return '0s';
      
      if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
      } else {
        const hours = Math.floor(seconds / 3600);
        const remainingMinutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${remainingMinutes}m`;
      }
    },
    
    /**
     * Calcola e formatta la velocità di elaborazione (file/sec)
     * @returns {string} Velocità formattata
     */
    calculateSpeed() {
      if (!this.finalResults || !this.finalResults.duration_seconds) return 'N/A';
      
      const filesProcessed = this.finalResults.files_processed || 0;
      const duration = this.finalResults.duration_seconds;
      
      if (filesProcessed === 0 || duration === 0) return 'N/A';
      
      const filesPerSecond = filesProcessed / duration;
      return `${filesPerSecond.toFixed(1)} file/sec`;
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

.result-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.result-item:last-child {
  border-bottom: none;
}

.result-value {
  font-weight: 600;
  float: right;
}

.summary-card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.h3 {
  font-weight: 700;
  margin-bottom: 0.5rem;
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

.bg-light {
  background-color: #f8f9fa !important;
}
</style>
