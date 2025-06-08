const createApp = window.Vue ? window.Vue.createApp : createApp;
createApp({
    data() {
        return {
            processing: false,
            inputDir: null,
            outputDir: null,
            consoleLines: [],
            elaborazioneCompletata: false
        };
    },
    methods: {
        addConsoleLine(text, type = 'normal') {
            this.consoleLines.push({ text, type });
            // Keep last 100 lines
            if (this.consoleLines.length > 100) this.consoleLines.shift();
            this.$nextTick(() => {
                const el = document.getElementById('console-output');
                if (el) el.scrollTop = el.scrollHeight;
            });
        },
        async selectInputDir() {
            this.addConsoleLine('Selezione cartella di input...', 'info');
            const dir = await window.electronAPI.selectDirectory();
            if (dir) {
                this.inputDir = dir;
                this.elaborazioneCompletata = false;
                this.addConsoleLine('Cartella input selezionata: ' + dir, 'success');
            } else {
                this.addConsoleLine('Selezione cartella input annullata.', 'warning');
            }
        },
        async selectOutputDir() {
            this.addConsoleLine('Selezione cartella di output...', 'info');
            const dir = await window.electronAPI.selectDirectory();
            if (dir) {
                this.outputDir = dir;
                this.elaborazioneCompletata = false;
                this.addConsoleLine('Cartella output selezionata: ' + dir, 'success');
            } else {
                this.addConsoleLine('Selezione cartella output annullata.', 'warning');
            }
        },
        async processImages() {
            if (!this.inputDir || !this.outputDir) return;
            this.processing = true;
            this.elaborazioneCompletata = false;
            this.addConsoleLine(`Esecuzione script Python: microperspective-corrector/main.py`, 'info');
            this.addConsoleLine(`Input: ${this.inputDir}`, 'info');
            this.addConsoleLine(`Output: ${this.outputDir}`, 'info');
            try {
                const result = await window.electronAPI.runProjectScript(
                    'project1',
                    'microperspective-corrector/main.py',
                    [this.inputDir, this.outputDir]
                );
                if (result.success) {
                    this.addConsoleLine('Elaborazione completata con successo!', 'success');
                    this.elaborazioneCompletata = true;
                    if (result.output) {
                        result.output.toString().split('\n').forEach(line => {
                            if (line.trim()) this.addConsoleLine(line.trim(), 'normal');
                        });
                    }
                } else {
                    this.addConsoleLine('Errore durante l\'elaborazione: ' + result.error, 'error');
                    this.elaborazioneCompletata = false;
                }
            } catch (error) {
                this.addConsoleLine('Errore JS: ' + error.message, 'error');
                this.elaborazioneCompletata = false;
            } finally {
                this.processing = false;
            }
        },
        goBack() {
            window.electronAPI.goBackToMain();
        }
    }
}).mount('#project-app');
