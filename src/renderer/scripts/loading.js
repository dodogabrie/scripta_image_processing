class LoadingManager {
    constructor() {
        this.messageEl = document.getElementById('loadingMessage');
        this.subMessageEl = document.getElementById('loadingSubMessage');
        this.progressEl = document.getElementById('progressFill');
        this.pythonCheckEl = document.getElementById('pythonCheck');
        this.venvCheckEl = document.getElementById('venvCheck');
        this.depsCheckEl = document.getElementById('depsCheck');
        this.logsConsoleEl = document.getElementById('logsConsole');
        this.testSection = document.getElementById('testSection');
        this.testPythonBtn = document.getElementById('testPythonBtn');
        
        this.setupEventListeners();
        this.setupTestButton();
        console.log('LoadingManager inizializzato');
    }

    setupEventListeners() {
        // Check if we have electronAPI
        if (typeof electronAPI !== 'undefined' && electronAPI.onProgress) {
            electronAPI.onProgress((progress) => {
                console.log('Progress received:', progress);
                this.updateProgress(progress);
            });
        } else {
            console.log('electronAPI not available, using fallback');
            // Fallback for when preload doesn't work
            this.simulateProgress();
        }
    }

    setupTestButton() {
        if (this.testPythonBtn) {
            this.testPythonBtn.addEventListener('click', async () => {
                await this.testPythonEnvironment();
            });
        }
    }

    addLogLine(message, type = 'normal') {
        if (!this.logsConsoleEl) return;
        
        const logLine = document.createElement('div');
        logLine.className = `log-line ${type}`;
        logLine.textContent = message;
        
        this.logsConsoleEl.appendChild(logLine);
        
        // Auto-scroll to bottom
        this.logsConsoleEl.scrollTop = this.logsConsoleEl.scrollHeight;
        
        // Keep only last 50 lines
        const lines = this.logsConsoleEl.children;
        if (lines.length > 50) {
            this.logsConsoleEl.removeChild(lines[0]);
        }
    }

    async testPythonEnvironment() {
        if (!window.electronAPI || !window.electronAPI.testPythonScript) {
            this.addLogLine('ERRORE: electronAPI non disponibile', 'error');
            return;
        }

        this.addLogLine('Avvio test ambiente Python...', 'normal');
        this.testPythonBtn.disabled = true;
        this.testPythonBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Test in corso...';

        try {
            const result = await window.electronAPI.testPythonScript('test_script.py', ['arg1', 'arg2']);
            
            if (result.success) {
                this.addLogLine('Test Python completato con successo!', 'success');
                const output = result.output.split('\n');
                output.forEach(line => {
                    if (line.trim()) {
                        this.addLogLine(line.trim(), 'pip');
                    }
                });
            } else {
                this.addLogLine(`Test Python fallito: ${result.error}`, 'error');
            }
        } catch (error) {
            this.addLogLine(`Errore test: ${error.message}`, 'error');
        } finally {
            this.testPythonBtn.disabled = false;
            this.testPythonBtn.innerHTML = '<i class="fas fa-play me-1"></i>Testa Ambiente Python';
        }
    }

    simulateProgress() {
        const steps = [
            { step: 'python-check', message: 'Verifica installazione Python...', percentage: 25 },
            { step: 'venv-setup', message: 'Configurazione ambiente virtuale...', percentage: 50 },
            { step: 'deps-install', message: 'Installazione dipendenze...', percentage: 75 },
            { step: 'complete', message: 'Ambiente Python pronto!', percentage: 100 }
        ];

        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                this.updateProgress(step);
                
                // Simulate some logs
                if (step.step === 'deps-install') {
                    this.addLogLine('pip install Pillow==10.0.1', 'pip');
                    setTimeout(() => this.addLogLine('Installazione completata con successo Pillow-10.0.1', 'success'), 500);
                }
                
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 1500);
    }

    updateProgress(progress) {
        const { step, message, subMessage, percentage, error, logs } = progress;
        
        if (this.messageEl) this.messageEl.textContent = message || 'Caricamento...';
        if (this.subMessageEl) this.subMessageEl.textContent = subMessage || '';
        
        if (percentage !== undefined && this.progressEl) {
            this.progressEl.style.width = `${percentage}%`;
        }

        // Add logs if provided
        if (logs && Array.isArray(logs)) {
            logs.forEach(log => {
                let logType = 'normal';
                if (log.includes('pip')) logType = 'pip';
                if (log.includes('Successfully')) logType = 'success';
                if (log.includes('ERROR') || log.includes('Failed')) logType = 'error';
                
                this.addLogLine(log, logType);
            });
        } else if (logs) {
            this.addLogLine(logs, 'normal');
        }

        // Update status icons based on step
        switch (step) {
            case 'python-check':
                this.addLogLine('Verifica installazione Python...', 'normal');
                this.updateStatusIcon(this.pythonCheckEl, error ? 'error' : 'completed');
                break;
            case 'venv-setup':
                this.addLogLine('Configurazione ambiente virtuale...', 'normal');
                this.updateStatusIcon(this.venvCheckEl, error ? 'error' : 'completed');
                break;
            case 'deps-install':
                this.addLogLine('Installazione dipendenze Python...', 'normal');
                this.updateStatusIcon(this.depsCheckEl, error ? 'error' : 'completed');
                break;
            case 'complete':
                this.addLogLine('Configurazione ambiente completata!', 'success');
                this.updateStatusIcon(this.pythonCheckEl, 'completed');
                this.updateStatusIcon(this.venvCheckEl, 'completed');
                this.updateStatusIcon(this.depsCheckEl, 'completed');
                // Show test button when complete
                if (this.testSection) {
                    this.testSection.classList.remove('d-none');
                }
                break;
        }

        if (error) {
            this.showError(error);
        }
    }

    updateStatusIcon(element, status) {
        if (!element) return;
        
        const icon = element.querySelector('i');
        if (!icon) return;

        element.className = `status-item mb-2 d-flex align-items-center ${status}`;
        
        switch (status) {
            case 'completed':
                icon.className = 'fas fa-check-circle text-success me-2';
                break;
            case 'error':
                icon.className = 'fas fa-times-circle text-danger me-2';
                break;
            default:
                icon.className = 'fas fa-clock text-warning me-2';
        }
    }

    showError(error) {
        if (this.messageEl) {
            this.messageEl.textContent = 'Configurazione Fallita';
            this.messageEl.style.color = '#dc3545';
        }
        if (this.subMessageEl) {
            this.subMessageEl.textContent = error;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM caricato, inizializzazione LoadingManager');
    new LoadingManager();

    const loadingMessage = document.getElementById('loadingMessage');
    const loadingSubMessage = document.getElementById('loadingSubMessage');
    const progressFill = document.getElementById('progressFill');
    const logsConsole = document.getElementById('logsConsole');
    const statusItems = {
        'python-check': document.getElementById('pythonCheck'),
        'venv-setup': document.getElementById('venvCheck'),
        'deps-install': document.getElementById('depsCheck')
    };

    if (window.electronAPI && window.electronAPI.onSetupProgress) {
        window.electronAPI.onSetupProgress((status) => {
            if (status.message) loadingMessage.textContent = status.message;
            if (status.error) loadingSubMessage.textContent = status.error;
            if (status.logs) {
                const div = document.createElement('div');
                div.className = 'log-line';
                div.textContent = status.logs;
                logsConsole.appendChild(div);
                logsConsole.scrollTop = logsConsole.scrollHeight;
            }
            if (typeof status.percentage === 'number') {
                progressFill.style.width = status.percentage + '%';
            }
            if (status.step && statusItems[status.step]) {
                if (status.step === 'error') {
                    statusItems[status.step].classList.add('error');
                    statusItems[status.step].querySelector('i').className = 'fas fa-times-circle text-danger me-2';
                } else {
                    statusItems[status.step].classList.add('completed');
                    statusItems[status.step].querySelector('i').className = 'fas fa-check-circle text-success me-2';
                }
            }
        });
    }

    // Richiedi l'avvio dell'installazione appena la pagina è pronta
    window.electronAPI?.startPythonSetup?.();
});
