<template>
  <div v-if="consoleLines.length > 0" class="card debug-console">
    <div class="card-header">
      <button 
        class="btn btn-sm btn-outline-secondary" 
        type="button" 
        @click="toggleConsole"
        :title="expanded ? 'Nascondi console' : 'Mostra console'"
      >
        <i class="bi bi-terminal"></i> 
        <i :class="expanded ? 'bi-chevron-up' : 'bi-chevron-down'" class="ms-1"></i>
        Debug Output ({{ consoleLines.length }} righe)
        <span v-if="hasErrors" class="badge bg-danger ms-2">{{ errorCount }} errori</span>
      </button>
      
      <div class="console-controls ms-2">
        <button 
          @click="clearConsole" 
          class="btn btn-sm btn-outline-danger"
          title="Pulisci console"
        >
          <i class="bi bi-trash"></i>
        </button>
        <button 
          @click="copyConsole" 
          class="btn btn-sm btn-outline-info ms-1"
          title="Copia console"
        >
          <i class="bi bi-clipboard"></i>
        </button>
      </div>
    </div>
    
    <div v-show="expanded" class="console-body">
      <div class="console-toolbar">
        <div class="btn-group btn-group-sm" role="group">
          <input 
            type="radio" 
            class="btn-check" 
            name="logLevel" 
            id="all" 
            v-model="filterLevel" 
            value="all"
          >
          <label class="btn btn-outline-secondary" for="all">Tutti</label>
          
          <input 
            type="radio" 
            class="btn-check" 
            name="logLevel" 
            id="errors" 
            v-model="filterLevel" 
            value="error"
          >
          <label class="btn btn-outline-danger" for="errors">Errori ({{ errorCount }})</label>
          
          <input 
            type="radio" 
            class="btn-check" 
            name="logLevel" 
            id="success" 
            v-model="filterLevel" 
            value="success"
          >
          <label class="btn btn-outline-success" for="success">Successi</label>
        </div>
        
        <div class="search-box">
          <input 
            type="text" 
            class="form-control form-control-sm" 
            placeholder="Cerca nei log..."
            v-model="searchTerm"
          >
        </div>
      </div>
      
      <div class="card-body p-0">
        <pre 
          class="console-output" 
          ref="consoleOutput"
        >{{ filteredConsoleText }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * DebugConsole Component
 * Console di debug avanzata con filtri, ricerca e controlli
 */
export default {
  name: 'DebugConsole',
  
  props: {
    consoleLines: {
      type: Array,
      default: () => []
    }
  },
  
  emits: ['clear-console'],
  
  data() {
    return {
      expanded: false,
      filterLevel: 'all',
      searchTerm: ''
    };
  },
  
  computed: {
    /**
     * Conta il numero di errori nei log
     */
    errorCount() {
      return this.consoleLines.filter(line => line.includes('❌')).length;
    },
    
    /**
     * Verifica se ci sono errori
     */
    hasErrors() {
      return this.errorCount > 0;
    },
    
    /**
     * Filtra le righe della console in base ai filtri attivi
     */
    filteredLines() {
      let filtered = this.consoleLines;
      
      // Filtra per livello di log
      if (this.filterLevel !== 'all') {
        const icon = this.filterLevel === 'error' ? '❌' : 
                    this.filterLevel === 'success' ? '✅' : 'ℹ️';
        filtered = filtered.filter(line => line.includes(icon));
      }
      
      // Filtra per termine di ricerca
      if (this.searchTerm.trim()) {
        const term = this.searchTerm.toLowerCase();
        filtered = filtered.filter(line => 
          line.toLowerCase().includes(term)
        );
      }
      
      return filtered;
    },
    
    /**
     * Testo della console filtrato
     */
    filteredConsoleText() {
      return this.filteredLines.join('\n');
    }
  },
  
  watch: {
    /**
     * Auto-scroll quando si aggiungono nuove righe
     */
    consoleLines: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      },
      deep: true
    }
  },
  
  methods: {
    /**
     * Toggle della visibilità della console
     */
    toggleConsole() {
      this.expanded = !this.expanded;
      if (this.expanded) {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    
    /**
     * Pulisce la console
     */
    clearConsole() {
      this.$emit('clear-console');
    },
    
    /**
     * Copia il contenuto della console negli appunti
     */
    async copyConsole() {
      try {
        await navigator.clipboard.writeText(this.filteredConsoleText);
        // Mostra feedback visivo (potresti emettere un evento per il parent)
        console.log('Console copiata negli appunti');
      } catch (error) {
        console.error('Errore nella copia:', error);
      }
    },
    
    /**
     * Scrolla automaticamente in fondo alla console
     */
    scrollToBottom() {
      const output = this.$refs.consoleOutput;
      if (output) {
        output.scrollTop = output.scrollHeight;
      }
    }
  }
};
</script>

<style scoped>
.debug-console {
  transition: all 0.3s ease-in-out;
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.debug-console:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.console-controls {
  display: flex;
  align-items: center;
}

.console-toolbar {
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-box {
  width: 200px;
}

.console-body {
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.console-output {
  background-color: #1a1a1a !important;
  color: #e0e0e0 !important;
  border: none !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
  padding: 1rem;
  overflow-y: auto;
  flex-grow: 1;
  max-height: 300px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.console-output::-webkit-scrollbar {
  width: 8px;
}

.console-output::-webkit-scrollbar-track {
  background: #2a2a2a;
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb:hover {
  background: #666;
}

.btn {
  border-radius: 6px;
  transition: all 0.2s ease-in-out;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.badge {
  border-radius: 20px;
  font-size: 0.75em;
  padding: 0.25rem 0.5rem;
}

.btn-group-sm .btn {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}

.form-control-sm {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}
</style>
