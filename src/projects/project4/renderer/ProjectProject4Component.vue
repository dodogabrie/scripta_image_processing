<template>
      <div class="container py-4">
        <h1>Leggio Massive Builder</h1>
        <p class="text-muted">Riorganizza i file multimediali di una istanza di Leggio in modo tale da ottimizzarne il caricamento sul server</p>

        <!-- UI logica qui -->
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

        <div class="row mb-3">
          <div class="col">
            <button 
              @click="processData" 
              :disabled="!inputDir || !outputDir || processing" 
              class="btn btn-success me-2"
            >
              <i class="bi bi-play-circle" v-if="!processing"></i>
              <i class="bi bi-hourglass-split" v-if="processing"></i>
              {{ processing ? 'Elaborazione...' : 'Processa' }}
            </button>
            
            <button @click="goBack" class="btn btn-outline-secondary">
              <i class="bi bi-arrow-left"></i> Indietro
            </button>
          </div>
        </div>

        <div v-if="elaborazioneCompletata" class="alert alert-success">
          <i class="bi bi-check-circle"></i> Elaborazione completata con successo!
        </div>
        
        <div v-if="consoleLines.length > 0" class="mt-3">
          <h5>Output:</h5>
          <pre class="bg-light p-3 border rounded" style="max-height: 300px; overflow-y: auto;">{{ consoleLines.join('\n') }}</pre>
        </div>
      </div>
    </template>

    <script>
    export default {
      name: 'ProjectProject4Component',
      data() {
        return {
          inputDir: null,
          outputDir: null,
          processing: false,
          elaborazioneCompletata: false,
          consoleLines: [],
        };
      },
      methods: {
        async selectInputDir() {
          this.inputDir = await window.electronAPI.selectDirectory();
        },
        async selectOutputDir() {
          this.outputDir = await window.electronAPI.selectDirectory();
        },
        async processData() {
          this.processing = true;
          const result = await window.electronAPI.runProjectScript('project4', 'main.py', [this.inputDir, this.outputDir]);
          this.processing = false;
          this.elaborazioneCompletata = result.success;
        },
        goBack() {
          this.$emit('goBack');
        }
      }
    };
    </script>
    