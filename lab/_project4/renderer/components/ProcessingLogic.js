/**
 * Processing Logic Mixin
 * Contiene tutta la logica di elaborazione separata dalla UI
 */
export default {
  data() {
    return {
      // Processing state
      processing: false,
      outputUnsubscribe: null,
      
      // Progress tracking
      progressData: {
        current: 0,
        total: 0,
        percentage: 0,
        files_optimized: 0,
        files_skipped: 0,
        errors: 0,
        bytes_saved: 0
      },
      currentFile: null,
      completedFiles: [],
      finalResults: null
    };
  },
  
  methods: {
    // =======================
    // STATE MANAGEMENT
    // =======================
    
    /**
     * Resetta lo stato dell'elaborazione per una nuova esecuzione
     */
    resetProcessingState() {
      this.progressData = {
        current: 0,
        total: 0,
        percentage: 0,
        files_optimized: 0,
        files_skipped: 0,
        errors: 0,
        bytes_saved: 0
      };
      this.completedFiles = [];
      this.currentFile = null;
      this.finalResults = null;
    },
    
    /**
     * Pulisce la sottoscrizione agli eventi
     */
    cleanupSubscription() {
      if (this.outputUnsubscribe) {
        this.outputUnsubscribe();
        this.outputUnsubscribe = null;
      }
    },
    
    // =======================
    // UTILITY METHODS
    // =======================
    
    /**
     * Estrae il nome del file da un percorso
     * @param {string} path - Percorso completo del file
     * @returns {string} Nome del file
     */
    getFilename(path) {
      if (!path) return '';
      const parts = path.split(/[/\\]/);
      return parts[parts.length - 1];
    },
    
    /**
     * Costruisce gli argomenti per lo script Python
     * @param {string} inputDir - Directory di input
     * @param {string} outputDir - Directory di output
     * @param {Object} options - Opzioni di ottimizzazione
     * @returns {Array} Array di argomenti
     */
    buildScriptArguments(inputDir, outputDir, options) {
      const args = [inputDir, outputDir];
      
      // Aggiungi opzioni solo se diverse dai valori predefiniti
      if (options.quality !== 85) {
        args.push('--quality', options.quality.toString());
      }
      
      // Forza sempre il parametro workers per garantire parallelismo
      args.push('--workers', (options.workers || 4).toString());
      
      if (options.webp) {
        args.push('--webp');
      }
      
      if (options.webp_quality && options.webp_quality !== 80) {
        args.push('--webp-quality', options.webp_quality.toString());
      }
      
      if (options.verbose) {
        args.push('--verbose');
      }
      
      return args;
    },
    
    // =======================
    // DATA PROCESSING HANDLERS
    // =======================
    
    /**
     * Gestisce i dati JSON ricevuti dal processo Python
     * @param {Object} jsonData - Dati JSON ricevuti
     */
    handleJsonData(jsonData) {
      this.$emit('console-message', {
        text: `[${jsonData.type}] ${JSON.stringify(jsonData)}`,
        type: 'normal'
      });
      
      const handlers = {
        start: this.handleStartEvent,
        file_start: this.handleFileStartEvent,
        file_complete: this.handleFileCompleteEvent,
        progress: this.handleProgressEvent,
        complete: this.handleCompleteEvent,
        error: this.handleErrorEvent,
        raw: this.handleRawEvent
      };
      
      const handler = handlers[jsonData.type];
      if (handler) {
        handler.call(this, jsonData);
      } else {
        this.$emit('console-message', {
          text: `Evento sconosciuto: ${jsonData.type}`,
          type: 'error'
        });
      }
    },
    
    /**
     * Gestisce l'evento di inizio elaborazione
     */
    handleStartEvent(jsonData) {
      this.progressData = {
        current: 0,
        total: jsonData.total_files || 0,
        percentage: 0,
        files_optimized: 0,
        files_skipped: 0,
        errors: 0,
        bytes_saved: 0
      };
      this.completedFiles = [];
      this.currentFile = null;
      this.finalResults = null;
    },
    
    /**
     * Gestisce l'evento di inizio elaborazione file
     */
    handleFileStartEvent(jsonData) {
      this.currentFile = {
        filename: this.getFilename(jsonData.path),
        path: jsonData.path,
        size: jsonData.size,
        index: jsonData.index
      };
    },
    
    /**
     * Gestisce l'evento di completamento elaborazione file
     */
    handleFileCompleteEvent(jsonData) {
      const filename = this.getFilename(jsonData.path);
      this.completedFiles.push({
        filename,
        path: jsonData.path,
        original_size: jsonData.original_size,
        optimized_size: jsonData.optimized_size,
        reduction_percent: jsonData.reduction_percent,
        skipped: jsonData.skipped,
        error: jsonData.error
      });
    },
    
    /**
     * Gestisce l'evento di aggiornamento progresso
     */
    handleProgressEvent(jsonData) {
      this.progressData = {
        current: jsonData.current,
        total: jsonData.total,
        percentage: jsonData.percentage,
        files_optimized: jsonData.files_optimized,
        files_skipped: jsonData.files_skipped,
        errors: jsonData.errors,
        bytes_saved: jsonData.bytes_saved
      };
    },
    
    /**
     * Gestisce l'evento di completamento elaborazione
     */
    handleCompleteEvent(jsonData) {
      this.finalResults = jsonData;
      this.currentFile = null;
      this.processing = false;
      this.$emit('processing-complete', true);
      this.playCompletionSound();
    },
    
    /**
     * Gestisce l'evento di errore
     */
    handleErrorEvent(jsonData) {
      this.processing = false;
      this.$emit('processing-complete', false);
      this.$emit('console-message', {
        text: `Errore durante l'elaborazione: ${JSON.stringify(jsonData)}`,
        type: 'error'
      });
    },
    
    /**
     * Gestisce l'evento raw (messaggi non JSON)
     */
    handleRawEvent(jsonData) {
      this.$emit('console-message', {
        text: jsonData.data,
        type: 'normal'
      });
    },
    
    /**
     * Riproduce un suono di completamento
     */
    playCompletionSound() {
      try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmceAT2Y3O/AZSIGLoTM8tiANATbwMH/5K1zKQYyj9n9zHwyBSUzNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmceAT2Y3O/AZSIGLoTM8tiANATbwMH/5K1zKQYyj9n9zHwyBSU=');
        audio.volume = 0.3;
        audio.play().catch(() => {}); // Ignora errori se l'audio fallisce
      } catch (error) {
        console.warn('Impossibile riprodurre il suono di completamento:', error);
      }
    },
    
    // =======================
    // OUTPUT EVENT HANDLERS
    // =======================
    
    /**
     * Gestisce l'output di stdout
     */
    handleStdoutOutput(data) {
      data.data.split('\n').forEach(line => {
        if (line.trim()) {
          try {
            const jsonData = JSON.parse(line.trim());
            this.handleJsonData(jsonData);
          } catch (error) {
            this.$emit('console-message', {
              text: line.trim(),
              type: 'normal'
            });
          }
        }
      });
    },
    
    /**
     * Gestisce l'output di stderr
     */
    handleStderrOutput(data) {
      data.data.split('\n').forEach(line => {
        if (line.trim()) {
          this.$emit('console-message', {
            text: `ERROR: ${line.trim()}`,
            type: 'error'
          });
        }
      });
    },
    
    /**
     * Gestisce il completamento del processo
     */
    handleProcessComplete(data) {
      this.processing = false;
      this.$emit('processing-complete', data.success);
      
      if (!data.success) {
        this.$emit('console-message', {
          text: `❌ Elaborazione fallita (codice: ${data.code})`,
          type: 'error'
        });
      }
      
      this.cleanupSubscription();
    },
    
    /**
     * Gestisce gli errori del processo
     */
    handleProcessError(data) {
      this.processing = false;
      this.$emit('processing-complete', false);
      this.$emit('console-message', {
        text: `❌ Errore: ${data.data}`,
        type: 'error'
      });
      this.cleanupSubscription();
    },
    
    /**
     * Configura il listener per l'output Python
     */
    setupOutputListener() {
      if (!window.electronAPI.onPythonOutput) {
        return false;
      }
      
      this.outputUnsubscribe = window.electronAPI.onPythonOutput((data) => {
        console.log('[Processing] Received python output event:', data.type, new Date().toISOString());
        
        const outputHandlers = {
          stdout: this.handleStdoutOutput,
          stderr: this.handleStderrOutput,
          complete: this.handleProcessComplete,
          error: this.handleProcessError
        };
        
        const handler = outputHandlers[data.type];
        if (handler) {
          handler.call(this, data);
        }
      });
      
      return true;
    },
    
    // =======================
    // MAIN PROCESSING METHODS
    // =======================
    
    /**
     * Avvia l'elaborazione dei dati
     * @param {string} inputDir - Directory di input
     * @param {string} outputDir - Directory di output
     * @param {Object} options - Opzioni di ottimizzazione
     */
    async startProcessing(inputDir, outputDir, options) {
      if (!inputDir || !outputDir) {
        this.$emit('console-message', {
          text: 'Impossibile avviare l\'elaborazione: verificare che le directory siano selezionate',
          type: 'error'
        });
        return;
      }
      
      this.processing = true;
      this.resetProcessingState();
      
      try {
        console.log('[Processing] Avvio processo di ottimizzazione...');
        this.logAvailableAPIs();
        
        // Configura il listener per l'output
        const hasOutputListener = this.setupOutputListener();
        
        // Costruisci gli argomenti
        const args = this.buildScriptArguments(inputDir, outputDir, options);
        console.log('[Processing] Argomenti script:', args);
        console.log('[Processing] Opzioni ricevute:', options);
        
        // Log del comando completo per debug
        const fullCommand = `python rust_optimizer.py ${args.join(' ')}`;
        console.log('[Processing] Comando equivalente:', fullCommand);
        this.$emit('console-message', {
          text: `Comando: python rust_optimizer.py ${args.join(' ')}`,
          type: 'normal'
        });
        
        // Esegui lo script appropriato
        if (window.electronAPI.runProjectScriptStreaming && hasOutputListener) {
          await this.runStreamingProcess(args);
        } else {
          await this.runFallbackProcess(args);
        }
        
      } catch (error) {
        this.handleProcessingError(error);
      }
    },
    
    /**
     * Esegue il processo con streaming in tempo reale
     */
    async runStreamingProcess(args) {
      console.log('[Processing] Utilizzo API streaming');
      const result = await window.electronAPI.runProjectScriptStreaming('project4', 'rust_optimizer.py', args);
      console.log('[Processing] Risultato API streaming:', result);
    },
    
    /**
     * Esegue il processo senza streaming (fallback)
     */
    async runFallbackProcess(args) {
      console.log('[Processing] Utilizzo API fallback non-streaming');
      const result = await window.electronAPI.runProjectScript('project4', 'rust_optimizer.py', args);
      console.log('[Processing] Risultato API non-streaming:', result);
      
      this.processing = false;
      this.$emit('processing-complete', result.success);
      
      this.processScriptOutput(result.output);
      
      if (result.error) {
        this.$emit('console-message', {
          text: `❌ Errore: ${result.error}`,
          type: 'error'
        });
      }
    },
    
    /**
     * Processa l'output dello script
     */
    processScriptOutput(output) {
      if (!output) return;
      
      output.split('\n').forEach(line => {
        if (line.trim()) {
          try {
            const jsonData = JSON.parse(line.trim());
            this.handleJsonData(jsonData);
          } catch (error) {
            this.$emit('console-message', {
              text: line.trim(),
              type: 'normal'
            });
          }
        }
      });
    },
    
    /**
     * Gestisce gli errori durante l'elaborazione
     */
    handleProcessingError(error) {
      this.processing = false;
      this.$emit('processing-complete', false);
      this.$emit('console-message', {
        text: `❌ Errore JavaScript: ${error.message}`,
        type: 'error'
      });
      this.cleanupSubscription();
    },
    
    /**
     * Logga le API disponibili per debug
     */
    logAvailableAPIs() {
      console.log('[Processing] API disponibili:', {
        runProjectScriptStreaming: !!window.electronAPI.runProjectScriptStreaming,
        runProjectScript: !!window.electronAPI.runProjectScript,
        onPythonOutput: !!window.electronAPI.onPythonOutput
      });
    },
    
    /**
     * Ferma l'elaborazione in corso
     */
    async stopProcessing() {
      this.processing = false;
      this.cleanupSubscription();
      
      try {
        // Chiama l'API Electron per fermare il processo Python
        if (window.electronAPI && window.electronAPI.stopPythonProcess) {
          this.$emit('console-message', {
            text: 'Fermando il processo in corso...',
            type: 'normal'
          });
          
          await window.electronAPI.stopPythonProcess();
          
          this.$emit('console-message', {
            text: 'Processo fermato con successo',
            type: 'success'
          });
        } else {
          this.$emit('console-message', {
            text: 'API di stop non disponibile, processo fermato solo lato frontend',
            type: 'error'
          });
        }
      } catch (error) {
        this.$emit('console-message', {
          text: `Errore durante l'arresto del processo: ${error.message}`,
          type: 'error'
        });
      }
      
      this.$emit('console-message', {
        text: 'Elaborazione interrotta dall\'utente',
        type: 'error'
      });
    }
  },
  
  beforeDestroy() {
    this.cleanupSubscription();
  }
};
