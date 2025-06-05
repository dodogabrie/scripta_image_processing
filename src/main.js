const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { net } = require('electron');

// Import managers with error handling for development
let PythonManager, WindowManager, Logger;
try {
  PythonManager = require('./managers/PythonManager');
  WindowManager = require('./managers/WindowManager');
  Logger = require('./utils/Logger');
} catch (error) {
  console.error('Missing dependencies. Creating minimal fallbacks...');
  
  // Minimal fallback classes for development
  PythonManager = class { 
    async initialize(progressCallback) { 
      // Simulate real loading steps with proper callback
      progressCallback({ step: 'python-check', message: 'Checking Python installation...', percentage: 25 });
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      progressCallback({ step: 'venv-setup', message: 'Setting up virtual environment...', percentage: 50 });
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      progressCallback({ step: 'deps-install', message: 'Installing dependencies...', percentage: 75 });
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      progressCallback({ step: 'complete', message: 'Python environment ready!', percentage: 100 });
      return Promise.resolve(); 
    }
    getStatus() { return { ready: true }; }
    installEnvironment() { return Promise.resolve({ success: true }); }
    
    // Add runPythonScript method for testing
    async runPythonScript(scriptPath, args = []) {
      console.log('Fallback: runPythonScript chiamato con:', scriptPath, args);
      
      // Simulate script execution
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Return simulated Python output
      return `Script Python avviato con successo! (simulazione)
Versione Python: 3.11.0
Script eseguito alle: ${new Date().toLocaleString()}
Argomenti ricevuti: ${JSON.stringify(args)}
Versione NumPy: 1.24.3
Versione Pillow: 10.0.1
Versione OpenCV: 4.8.1.78
{"status": "successo", "message": "Ambiente Python funziona correttamente", "timestamp": "${new Date().toISOString()}", "packages_available": true}`;
    }
    
    // Add checkPythonInstallation method for testing
    async checkPythonInstallation() {
      console.log('Fallback: checkPythonInstallation chiamato');
      return true; // Simulate Python is installed
    }
  };
  
  WindowManager = class {
    createLoadingWindow() {
      this.loadingWindow = new BrowserWindow({
        width: 500,
        height: 600,
        frame: false,
        alwaysOnTop: true,
        resizable: false,
        webPreferences: {
          nodeIntegration: true,
          contextIsolation: false,
          preload: path.join(__dirname, 'preload/loading-preload.js')
        }
      });
      
      this.loadingWindow.loadFile(path.join(__dirname, 'renderer/loading.html'));
      
      // Wait for DOM to be ready before sending messages
      this.loadingWindow.webContents.once('dom-ready', () => {
        console.log('Loading window DOM ready');
      });
      
      return this.loadingWindow;
    }
    
    createMainWindow() {
      const win = new BrowserWindow({
        width: 1600,
        height: 1000,
        show: false,
        webPreferences: { 
          nodeIntegration: false, 
          contextIsolation: true,
          preload: path.join(__dirname, 'preload/main-preload.js')
        }
      });
      win.loadFile(path.join(__dirname, 'renderer/main.html'));
      
      // Add debug logging
      win.webContents.once('dom-ready', () => {
        console.log('Main window DOM ready');
      });
      
      return win;
    }
    
    closeLoadingWindow() {
      if (this.loadingWindow) {
        this.loadingWindow.close();
        this.loadingWindow = null;
      }
    }
    
    createErrorWindow(msg) { console.error('Error:', msg); }
  };
  
  Logger = class {
    info(msg) { console.log('[INFO]', msg); }
    error(msg, err) { console.error('[ERROR]', msg, err); }
  };
}

class App {
  constructor() {
    this.pythonManager = new PythonManager();
    this.windowManager = new WindowManager();
    this.logger = new Logger();
    this.isReady = false;
    this.loadingWindow = null;
  }

  async isOnline() {
    return new Promise(resolve => {
      const request = net.request('https://www.google.com');
      request.on('response', (response) => {
        resolve(response.statusCode === 200);
      });
      request.on('error', () => {
        resolve(false);
      });
      request.end();
    });
  }

  async initialize() {
    try {
      // Show loading window first
      this.loadingWindow = this.windowManager.createLoadingWindow();
      
      this.logger.info('Avvio dello starter di configurazione...');
      
      // Check internet connection
      const online = await this.isOnline();
      if (!online) {
        this.loadingWindow.webContents.send('setup-progress', {
          step: 'error',
          message: 'Nessuna connessione Internet',
          error: 'Connessione Internet non disponibile. Verifica la connessione e riavvia l\'applicazione.',
          percentage: 0
        });
        return;
      }
      
      // Wait for DOM to be ready before sending progress
      this.loadingWindow.webContents.once('dom-ready', async () => {
        try {
          // Check if Python is installed
          const pythonInstalled = await this.pythonManager.checkPythonInstallation();
          if (!pythonInstalled) {
            this.loadingWindow.webContents.send('setup-progress', {
              step: 'error',
              message: 'Python non trovato',
              error: 'Python non è installato o non è nel PATH. Installare Python 3.11 e riavviare l\'applicazione.',
              percentage: 0
            });
            return;
          }
          
          // Setup Python environment with progress updates
          await this.pythonManager.initialize((progress) => {
            if (this.loadingWindow && !this.loadingWindow.isDestroyed()) {
              console.log('Sending progress:', progress);
              this.loadingWindow.webContents.send('setup-progress', progress);
            }
          });
          
          this.isReady = true;
          this.logger.info('Inizializzazione completata con successo!');
          
          // Close loading window and create main window
          setTimeout(() => {
            this.windowManager.closeLoadingWindow();
            const mainWindow = this.windowManager.createMainWindow();
            if (mainWindow) {
              mainWindow.show();
            }
          }, 1000);
          
        } catch (error) {
          this.handleInitializationError(error);
        }
      });
      
    } catch (error) {
      this.handleInitializationError(error);
    }
  }

  handleInitializationError(error) {
    this.logger.error('Initialization failed:', error);
    
    if (this.loadingWindow && !this.loadingWindow.isDestroyed()) {
      this.loadingWindow.webContents.send('setup-progress', {
        step: 'error',
        message: 'Setup Failed',
        error: error.message,
        percentage: 0
      });
    }
    
    setTimeout(() => {
      this.windowManager.createErrorWindow(error.message);
    }, 3000);
  }

  setupIPC() {
    console.log('Configurazione IPC handlers...');
    
    ipcMain.handle('app:getStatus', () => {
      console.log('IPC: app:getStatus chiamato');
      return {
        isReady: this.isReady,
        pythonStatus: this.pythonManager.getStatus()
      };
    });

    ipcMain.handle('python:install', async () => {
      console.log('IPC: python:install chiamato');
      return await this.pythonManager.installEnvironment();
    });

    // Add Python script execution handler
    ipcMain.handle('python:runScript', async (event, scriptName, args = []) => {
      console.log('IPC: python:runScript chiamato con:', scriptName, args);
      try {
        const scriptPath = path.join(__dirname, 'python_scripts', scriptName);
        console.log('Percorso script:', scriptPath);
        
        // Check if PythonManager has the method
        if (!this.pythonManager.runPythonScript) {
          console.error('runPythonScript method not available');
          return { success: false, error: 'runPythonScript method not available' };
        }
        
        const result = await this.pythonManager.runPythonScript(scriptPath, args);
        console.log('Risultato script:', result);
        return { success: true, output: result };
      } catch (error) {
        console.error('Errore esecuzione script:', error);
        return { success: false, error: error.message };
      }
    });
    
    console.log('IPC handlers configurati');
  }
}

const appInstance = new App();

app.whenReady().then(() => {
  appInstance.setupIPC();
  appInstance.initialize();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    appInstance.initialize();
  }
});
