const { createApp } = Vue;

createApp({
    data() {
        return {
            appStatus: {
                isReady: false,
                pythonStatus: { ready: false }
            },
            testing: false,
            console: null,
            projects: [],
            projectsLoaded: false,
            currentProject: null
        };
    },
    async mounted() {
        this.console = document.getElementById('console');
        this.addLogEntry('Applicazione caricata - Testing: ' + this.testing, 'info');
        this.testing = false;
        await this.checkAppStatus();
        await this.loadProjects();
        
        // Check status periodically
        setInterval(this.checkAppStatus, 5000);
    },
    methods: {
        resetState() {
            this.testing = false;
            this.addLogEntry('Stato resettato - Testing: ' + this.testing, 'warning');
        },
        async checkAppStatus() {
            try {
                if (window.electronAPI && window.electronAPI.getAppStatus) {
                    this.appStatus = await window.electronAPI.getAppStatus();
                    this.addLogEntry('Stato: ' + (this.appStatus.isReady ? 'Pronto' : 'Inizializzazione'), 'info');
                } else {
                    this.addLogEntry('electronAPI non disponibile', 'warning');
                }
            } catch (error) {
                this.addLogEntry('Errore controllo stato: ' + error.message, 'error');
            }
        },
        async loadProjects() {
            try {
                if (window.electronAPI && window.electronAPI.getProjects) {
                    this.projects = await window.electronAPI.getProjects();
                    this.addLogEntry('Progetti caricati: ' + JSON.stringify(this.projects), 'info');
                } else {
                    this.addLogEntry('getProjects non disponibile', 'warning');
                }
            } catch (error) {
                this.addLogEntry('Errore caricamento progetti: ' + error.message, 'error');
            } finally {
                this.projectsLoaded = true;
            }
        },
        async openProject(projectId) {
            if (!this.appStatus.isReady) {
                alert('Attendere il completamento dell\'inizializzazione');
                return;
            }
            try {
                // Trova il progetto
                const project = this.projects.find(p => p.id === projectId);
                if (!project) {
                    alert('Progetto non trovato');
                    return;
                }
                // Apri il progetto in una nuova finestra Electron
                if (window.electronAPI && window.electronAPI.openProject) {
                    const result = await window.electronAPI.openProject(projectId);
                    if (!result.success) {
                        alert('Errore nell\'apertura del progetto: ' + result.error);
                    }
                } else {
                    alert('Funzione openProject non disponibile');
                }
            } catch (error) {
                alert('Errore nell\'apertura del progetto');
            }
        },
        goBackToHome() {
            this.currentProject = null;
            const container = document.getElementById('project-container');
            if (container) {
                container.innerHTML = '';
            }
        },
        addLogEntry(message, type = 'normal') {
            if (!this.console) return;
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.innerHTML = `<small>[${new Date().toLocaleTimeString()}]</small> ${message}`;
            this.console.appendChild(entry);
            this.console.scrollTop = this.console.scrollHeight;
        },
        clearOutput() {
            if (this.console) {
                this.console.innerHTML = '<div class="log-entry text-muted"><small>Console pulita...</small></div>';
            }
        },
        debugInfo() {
            this.addLogEntry('=== INFO DEBUG ===', 'info');
            this.addLogEntry('Testing state: ' + this.testing, 'info');
            this.addLogEntry('window.electronAPI: ' + (!!window.electronAPI), window.electronAPI ? 'success' : 'error');
            if (window.electronAPI) {
                this.addLogEntry('Metodi disponibili:', 'info');
                Object.keys(window.electronAPI).forEach(key => {
                    this.addLogEntry(`  ${key}: ${typeof window.electronAPI[key]}`, 'normal');
                });
            } else {
                this.addLogEntry('Nessun electronAPI trovato!', 'error');
            }
            this.addLogEntry('App Status: ' + JSON.stringify(this.appStatus), 'info');
        },
        async runPythonTest() {
            this.addLogEntry('=== TENTATIVO AVVIO TEST ===', 'info');
            if (this.testing) {
                this.addLogEntry('Test già in corso, uscita anticipata', 'warning');
                return;
            }
            this.testing = true;
            try {
                if (!window.electronAPI) {
                    throw new Error('electronAPI non disponibile');
                }
                if (!window.electronAPI.testPythonScript) {
                    throw new Error('testPythonScript non disponibile');
                }
                this.addLogEntry('Chiamata a testPythonScript...', 'normal');
                const result = await window.electronAPI.testPythonScript('test_script.py', []);
                this.addLogEntry('Risposta ricevuta: ' + JSON.stringify(result), 'normal');
                if (result && result.success) {
                    this.addLogEntry('Test completato!', 'success');
                    if (result.output) {
                        result.output.split('\n').forEach(line => {
                            if (line.trim()) {
                                let logType = 'normal';
                                if (line.includes('ERROR') || line.includes('Errore')) {
                                    logType = 'error';
                                } else if (line.includes('version') || line.includes('versione') || line.includes('Found') || line.includes('Versione')) {
                                    logType = 'info';
                                } else if (line.includes('successo') || line.includes('Successfully')) {
                                    logType = 'success';
                                }
                                this.addLogEntry(line.trim(), logType);
                            }
                        });
                    } else {
                        this.addLogEntry('Nessun output ricevuto dallo script', 'warning');
                    }
                } else {
                    throw new Error(result ? result.error : 'Nessuna risposta dal server');
                }
            } catch (error) {
                this.addLogEntry('Errore: ' + error.message, 'error');
                console.error('Errore completo:', error);
            } finally {
                this.testing = false;
                this.addLogEntry('Testing state finale: ' + this.testing, 'normal');
            }
        }
    }
}).mount('#app');
