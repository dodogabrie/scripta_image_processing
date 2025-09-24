<template>
      <div class="container py-4">
        <h1>Leggio Massive Builder</h1>
        <p class="text-muted">Riorganizza i file multimediali di una istanza di Leggio in modo tale da ottimizzarne il caricamento sul server</p>
        <p class="text-info">
          <i class="bi bi-info-circle"></i>
          Utilizza il potente Space Media Optimizer (Rust) per ottimizzare immagini e video
        </p>

        <!-- Directory Selection Component -->
        <DirectorySelector
          :inputDir="inputDir"
          :outputDir="outputDir"
          @update:inputDir="inputDir = $event"
          @update:outputDir="outputDir = $event"
          @console-message="addConsoleLine($event.text, $event.type)"
        />

        <!-- Optimization Options Component -->
        <OptimizationOptions
          :options="options"
          @update:options="options = $event"
        />

        <!-- Action Buttons -->
        <div class="row mb-3">
          <div class="col">
            <button 
              @click="processData" 
              :disabled="!canProcess" 
              class="btn btn-success me-2"
            >
              <i :class="`bi ${processButtonIcon}`"></i>
              {{ processButtonText }}
            </button>
            
            <button 
              v-if="processing" 
              @click="stopProcess" 
              class="btn btn-danger me-2"
            >
              <i class="bi bi-stop-circle"></i>
              Ferma
            </button>
            
            <button @click="goBack" class="btn btn-outline-secondary">
              <i class="bi bi-arrow-left"></i> Indietro
            </button>
          </div>
        </div>

        <div v-if="elaborazioneCompletata" class="alert alert-success">
          <i class="bi bi-check-circle"></i> Elaborazione completata con successo!
        </div>
        
        <!-- Progress Section Component -->
        <ProgressSection
          v-if="processing"
          :processing="processing"
          :progressData="progressData"
          :currentFile="currentFile"
          :formatBytes="formatBytes"
        />
        
        <!-- Completed Files List Component -->
        <CompletedFilesList
          v-if="completedFiles.length > 0"
          :completedFiles="completedFiles"
          :formatBytes="formatBytes"
        />
        
        <!-- Final Results Component -->
        <FinalResults
          v-if="finalResults"
          :finalResults="finalResults"
          :formatBytes="formatBytes"
        />
        
        <!-- Debug Console Component -->
        <DebugConsole
          v-if="consoleLines.length > 0"
          :consoleLines="consoleLines"
          @clear-console="clearConsole"
        />
      </div>
    </template>

    <script>
    // Import components
    import DirectorySelector from './components/DirectorySelector.vue';
    import OptimizationOptions from './components/OptimizationOptions.vue';
    import ProgressSection from './components/ProgressSection.vue';
    import CompletedFilesList from './components/CompletedFilesList.vue';
    import FinalResults from './components/FinalResults.vue';
    import DebugConsole from './components/DebugConsole.vue';
    import ProcessingLogic from './components/ProcessingLogic.js';

    /**
     * Leggio Massive Builder Component
     * Gestisce l'ottimizzazione dei file multimediali utilizzando Space Media Optimizer (Rust)
     */
    export default {
      name: 'ProjectProject4Component',
      
      components: {
        DirectorySelector,
        OptimizationOptions,
        ProgressSection,
        CompletedFilesList,
        FinalResults,
        DebugConsole
      },
      
      mixins: [ProcessingLogic],
      
      data() {
        return {
          // Directory paths
          inputDir: null,
          outputDir: null,
          
          // State management
          elaborazioneCompletata: false,
          
          // Console and logging
          consoleLines: [],
          
          // Optimization settings
          options: {
            quality: 85,
            workers: 4,
            webp: false,
            webp_quality: 80,
            verbose: false
          }
        };
      },
      
      computed: {
        /**
         * Verifica se è possibile avviare l'elaborazione
         */
        canProcess() {
          return this.inputDir && this.outputDir && !this.processing;
        },
        
        /**
         * Testo del pulsante di elaborazione
         */
        processButtonText() {
          return this.processing ? 'Elaborazione...' : 'Processa';
        },
        
        /**
         * Icona del pulsante di elaborazione
         */
        processButtonIcon() {
          return this.processing ? 'bi-hourglass-split' : 'bi-play-circle';
        }
      },
      
      methods: {
        // =======================
        // EVENT HANDLERS FROM MIXIN
        // =======================
        
        /**
         * Override del metodo $emit per intercettare gli eventi del mixin
         */
        $emit(eventName, data) {
          if (eventName === 'console-message') {
            this.addConsoleLine(data.text, data.type);
          } else if (eventName === 'processing-complete') {
            this.elaborazioneCompletata = data;
          }
          // Chiama il metodo originale se esiste
          if (this.$parent && this.$parent.$emit) {
            this.$parent.$emit(eventName, data);
          }
        },
        
        // =======================
        // UTILITY METHODS
        // =======================
        
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
        
        // =======================
        // CONSOLE MANAGEMENT
        // =======================
        
        /**
         * Aggiunge una riga alla console di debug
         * @param {string} text - Testo da aggiungere
         * @param {string} type - Tipo di messaggio (normale, errore, etc.)
         */
        addConsoleLine(text, type = 'normal') {
          const timestamp = new Date().toLocaleTimeString();
          const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
          this.consoleLines.push(`[${timestamp}] ${prefix} ${text}`);
          
          // Mantieni solo le ultime 1000 righe per evitare problemi di memoria
          if (this.consoleLines.length > 1000) {
            this.consoleLines = this.consoleLines.slice(-1000);
          }
        },
        
        /**
         * Pulisce la console di debug
         */
        clearConsole() {
          this.consoleLines = [];
        },
        
        // =======================
        // MAIN PROCESSING METHOD
        // =======================
        
        /**
         * Avvia l'elaborazione dei dati
         */
        async processData() {
          if (!this.canProcess) {
            this.addConsoleLine('Impossibile avviare l\'elaborazione: verificare che le directory siano selezionate', 'error');
            return;
          }
          
          // Reset state
          this.elaborazioneCompletata = false;
          this.consoleLines = [];
          
          // Utilizza il mixin per avviare il processo
          console.log(this.options);
          await this.startProcessing(this.inputDir, this.outputDir, this.options);
        },
        
        /**
         * Ferma l'elaborazione in corso
         */
        stopProcess() {
          if (this.processing) {
            this.addConsoleLine('Richiesta interruzione processo...', 'normal');
            this.stopProcessing();
          }
        },
        
        // =======================
        // NAVIGATION
        // =======================
        
        /**
         * Torna alla schermata precedente
         */
        goBack() {
          this.cleanupSubscription();
          this.$emit('goBack');
        }
      },
      
      // =======================
      // LIFECYCLE HOOKS
      // =======================
      
      beforeDestroy() {
        this.cleanupSubscription();
      }
    };
    </script>

    <style scoped>
    /* ===============================
       ANIMATIONS
       =============================== */
    .animate-fade-in {
      animation: fadeIn 0.5s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* ===============================
       BUTTONS
       =============================== */
    .btn {
      border-radius: 6px;
      transition: all 0.2s ease-in-out;
    }

    .btn:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    </style>
