const { createApp, markRaw } = Vue;

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function mountAppWhenReady() {
    createApp({
        data() {
            return {
                currentProjectComponent: null,
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
                        console.log('Progetti caricati:', this.projects);
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
                this.currentProject = projectId;
                await this.loadProjectScript(projectId);
                
                // Try multiple component name variations
                const compNameCapitalized = capitalize(projectId); // Project2
                const compNameLowercase = projectId; // project2
                
                let component = null;
                let tries = 0;
                
                while (!component && tries < 20) { 
                    // Try capitalized version first (Project2)
                    if (window[compNameCapitalized]) {
                        component = window[compNameCapitalized];
                        break;
                    }
                    // Try lowercase version (project2)
                    if (window[compNameLowercase]) {
                        component = window[compNameLowercase];
                        break;
                    }
                    
                    await new Promise(r => setTimeout(r, 100));
                    tries++;
                }
                
                if (!component) {
                    this.addLogEntry(`Componente non trovato per ${projectId}. Tentati: ${compNameCapitalized}, ${compNameLowercase}`, 'error');
                    this.addLogEntry(`Window objects disponibili: ${Object.keys(window).filter(k => k.includes(projectId) || k.includes(compNameCapitalized)).join(', ')}`, 'info');
                    this.currentProjectComponent = null;
                } else {
                    this.addLogEntry(`Componente ${component.name || projectId} caricato con successo`, 'success');
                    // Usa markRaw per evitare che Vue lo renda reattivo
                    this.currentProjectComponent = markRaw(component);
                }
            },
            goBackToHome() {
                if (this.currentProject) {
                  this.removeProjectScript(this.currentProject);
                }
                this.currentProject = null;
                this.currentProjectComponent = null;
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
            },
            getProjectName(projectId) {
                const p = this.projects.find(p => p.id === projectId);
                return p && p.config ? p.config.name : projectId;
            },
            loadProjectScript(projectId) {
                // Trova il progetto già caricato
                const project = this.projects.find(p => p.id === projectId);
                if (!project || !project.config) {
                    return Promise.reject(new Error(`Config non trovato per il progetto ${projectId}`));
                }
            
                // Usa il campo renderer_script dal config, oppure fallback su convenzione
                const scriptPath = project.config.renderer_script
                    ? `../projects/${projectId}/${project.config.renderer_script}`
                    : `../projects/${projectId}/renderer/${capitalize(projectId)}.js`;
            
                return new Promise((resolve, reject) => {
                    // Evita di caricare due volte lo stesso script
                    if (document.querySelector(`script[src="${scriptPath}"]`)) {
                        resolve();
                        return;
                    }
                    const script = document.createElement('script');
                    script.src = scriptPath;
                    script.onload = resolve;
                    script.onerror = reject;
                    document.body.appendChild(script);
                });
            },
            removeProjectScript(projectId) {
                const project = this.projects.find(p => p.id === projectId);
                if (!project || !project.config) return;
            
                const scriptPath = project.config.renderer_script
                    ? `../projects/${projectId}/${project.config.renderer_script}`
                    : `../projects/${projectId}/renderer/${capitalize(projectId)}.js`;
            
                const script = document.querySelector(`script[src="${scriptPath}"]`);
                if (script) {
                    script.remove();
                }
            }
        }
    }).mount('#app');
} 

mountAppWhenReady();
