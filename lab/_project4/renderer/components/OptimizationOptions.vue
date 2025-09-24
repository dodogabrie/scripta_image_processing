<template>
  <div class="card mb-3">
    <div class="card-header">
      <h5 class="mb-0">Opzioni di Ottimizzazione</h5>
    </div>
    <div class="card-body">
      <div class="row mb-3">
        <div class="col-md-6">
          <label for="quality" class="form-label">Qualità JPEG (1-100)</label>
          <input 
            type="number" 
            class="form-control" 
            id="quality"
            :value="options.quality"
            @input="updateOption('quality', $event.target.value)"
            min="1" 
            max="100"
          >
        </div>
        <div class="col-md-6">
          <label for="webp_quality" class="form-label">Qualità WebP (1-100)</label>
          <input 
            type="number" 
            class="form-control" 
            id="webp_quality"
            :value="options.webp_quality"
            @input="updateOption('webp_quality', $event.target.value)"
            min="1" 
            max="100"
            :disabled="!options.webp"
          >
          <div class="form-text">Funziona sia per conversione che per ricompressione WebP</div>
        </div>
      </div>
      
      <div class="row mb-3">
        <div class="col-md-6">
          <label for="workers" class="form-label">Workers Paralleli</label>
          <input 
            type="number" 
            class="form-control" 
            id="workers"
            :value="options.workers"
            @input="updateOption('workers', $event.target.value)"
            min="1" 
            max="16"
          >
        </div>
        <div class="col-md-6">
          <!-- Placeholder for future options -->
        </div>
      </div>
      
      <div class="row mb-3">
        <div class="col-md-6">
          <div class="form-check">
            <input 
              class="form-check-input" 
              type="checkbox" 
              id="webp"
              :checked="options.webp"
              @change="updateOption('webp', $event.target.checked)"
            >
            <label class="form-check-label" for="webp">
              Converti in WebP (massima compressione)
            </label>
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-check">
            <input 
              class="form-check-input" 
              type="checkbox" 
              id="verbose"
              :checked="options.verbose"
              @change="updateOption('verbose', $event.target.checked)"
            >
            <label class="form-check-label" for="verbose">
              Output dettagliato
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * OptimizationOptions Component
 * Gestisce le opzioni di ottimizzazione per il processo
 */
export default {
  name: 'OptimizationOptions',
  
  props: {
    options: {
      type: Object,
      required: true,
      validator(value) {
        return typeof value.quality === 'number' &&
               typeof value.workers === 'number' &&
               typeof value.webp === 'boolean' &&
               typeof value.webp_quality === 'number' &&
               typeof value.verbose === 'boolean';
      }
    }
  },
  
  emits: ['update:options'],
  
  methods: {
    /**
     * Aggiorna una specifica opzione
     * @param {string} key - Chiave dell'opzione da aggiornare
     * @param {any} value - Nuovo valore
     */
    updateOption(key, value) {
      const updatedOptions = { ...this.options };
      
      // Converti i valori numerici
      if (key === 'quality' || key === 'workers' || key === 'webp_quality') {
        updatedOptions[key] = parseInt(value, 10);
      } else {
        updatedOptions[key] = value;
      }
      
      this.$emit('update:options', updatedOptions);
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

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}
</style>
