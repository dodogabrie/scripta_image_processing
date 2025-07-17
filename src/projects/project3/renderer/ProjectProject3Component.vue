<template>
      <div class="container py-4">
        <h1>Digiscripta Builder</h1>
        <p class="text-muted">Crea campi di progetto compatibili  il software Digiscripta</p>

        <!-- UI logica qui -->
        <button @click="selectInputDir" class="btn btn-primary mb-2">Input</button>
        <button @click="selectOutputDir" class="btn btn-secondary mb-2">Output</button>

        <div v-if="processing" class="text-muted">Elaborazione...</div>
        <div v-if="elaborazioneCompletata" class="alert alert-success">Completato!</div>
      </div>
    </template>

    <script>
    export default {
      name: 'ProjectProject3Component',
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
          const result = await window.electronAPI.runProjectScript('project3', 'main.py', [this.inputDir, this.outputDir]);
          this.processing = false;
          this.elaborazioneCompletata = result.success;
        },
        goBack() {
          this.$emit('goBack');
        }
      }
    };
    </script>
    