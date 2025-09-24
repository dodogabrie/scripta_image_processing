<template>
  <div>
    <!-- Directory Selection -->
    <div class="row mb-3">
      <div class="col">
        <button @click="selectInputDir" class="btn btn-primary me-2">
          <i class="bi bi-folder"></i> Seleziona Input
        </button>
        <span v-if="inputDir" class="text-muted ms-2">{{ inputDir }}</span>
      </div>
    </div>
    
    <div class="row mb-3">
      <div class="col">
        <button @click="selectOutputDir" class="btn btn-secondary me-2">
          <i class="bi bi-folder"></i> Seleziona Output
        </button>
        <span v-if="outputDir" class="text-muted ms-2">{{ outputDir }}</span>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * DirectorySelector Component
 * Gestisce la selezione delle directory di input e output
 */
export default {
  name: 'DirectorySelector',
  
  props: {
    inputDir: {
      type: String,
      default: null
    },
    outputDir: {
      type: String,
      default: null
    }
  },
  
  emits: ['update:inputDir', 'update:outputDir', 'console-message'],
  
  methods: {
    /**
     * Seleziona la directory di input
     */
    async selectInputDir() {
      try {
        const selectedDir = await window.electronAPI.selectDirectory();
        if (selectedDir) {
          this.$emit('update:inputDir', selectedDir);
        }
      } catch (error) {
        this.$emit('console-message', {
          text: `Errore nella selezione della directory di input: ${error.message}`,
          type: 'error'
        });
      }
    },
    
    /**
     * Seleziona la directory di output
     */
    async selectOutputDir() {
      try {
        const selectedDir = await window.electronAPI.selectDirectory();
        if (selectedDir) {
          this.$emit('update:outputDir', selectedDir);
        }
      } catch (error) {
        this.$emit('console-message', {
          text: `Errore nella selezione della directory di output: ${error.message}`,
          type: 'error'
        });
      }
    }
  }
};
</script>

<style scoped>
.btn {
  border-radius: 6px;
  transition: all 0.2s ease-in-out;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
