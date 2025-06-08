const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { net, dialog } = require('electron');

// Import managers with error handling for development
let PythonManager, WindowManager, Logger, ProjectManager;
try {
  PythonManager = require('./managers/PythonManager');
  WindowManager = require('./managers/WindowManager');
  Logger = require('./utils/Logger');
  ProjectManager = require('./managers/ProjectManager');
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
      return Promise.reject(new Error('Python non trovato (simulazione)')); 
    }
    getStatus() { return { ready: false }; }
    installEnvironment() { return Promise.resolve({ success: true }); }
    
    // Add runPythonScript method for testing
    async runPythonScript(scriptPath, args = []) {
      console.log('Fallback: runPythonScript chiamato con:', scriptPath, args);
      
      // Simulate script execution
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return `Script Python non si esegue. Percorso: ${scriptPath}, Argomenti: ${args.join(', ')}`;
    }
    
    // Add checkPythonInstallation method for testing
    async checkPythonInstallation() {
      console.log('Fallback: checkPythonInstallation chiamato');
      return false; // Simulate Python is NOT installed
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
          preload: path.join(__dirname, 'preload', 'main-preload.js')
        }
      });
      win.loadFile(path.join(__dirname, 'renderer', 'main.html'));
      
      // Add debug logging
      win.webContents.once('dom-ready', () => {
        console.log('Main window DOM ready');
      });
      
      return win;
    }
    
    createProjectWindow(projectHtmlPath) {
      console.log('Fallback: createProjectWindow chiamato con:', projectHtmlPath);
      const projectWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        show: true,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          preload: path.join(__dirname, 'preload', 'project-preload.js')
        }
      });

      projectWindow.loadFile(projectHtmlPath);

      projectWindow.webContents.once('dom-ready', () => {
        console.log('Project window DOM ready (fallback)');
      });

      return projectWindow;
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
  
  ProjectManager = class {
    constructor() {
      this.projects = new Map();
    }
    async loadProjects() { 
      // Simulate loading projects
      this.projects.set('project1', {
        id: 'project1',
        config: {
          name: 'Progetto Demo',
          description: 'Progetto di esempio per test',
          version: '1.0.0'
        }
      });
    }
    getProjects() { 
      return Array.from(this.projects.values()); 
    }
    getProject(id) { 
      return this.projects.get(id); 
    }
  };
}

class App {
  constructor() {
    this.pythonManager = new PythonManager();
    this.windowManager = new WindowManager();
    this.projectManager = new ProjectManager();
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

    // Project management handlers
    ipcMain.handle('projects:getAll', async () => {
      console.log('IPC: projects:getAll chiamato');
      await this.projectManager.loadProjects();
      return this.projectManager.getProjects();
    });

    ipcMain.handle('projects:open', async (event, projectId) => {
      console.log('IPC: projects:open chiamato con:', projectId);
      try {
        const project = this.projectManager.getProject(projectId);
        if (!project) {
          return { success: false, error: 'Project not found' };
        }
        
        const mainHtmlPath = this.projectManager.getProjectMainHtml(projectId);
        if (!mainHtmlPath) {
          return { success: false, error: 'Project main HTML not found' };
        }
        
        console.log('Opening project window with HTML:', mainHtmlPath);
        const projectWindow = this.windowManager.createProjectWindow(mainHtmlPath);
        
        return { success: true };
      } catch (error) {
        console.error('Errore apertura progetto:', error);
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('projects:runScript', async (event, projectId, scriptName, args = []) => {
      console.log('IPC: projects:runScript chiamato con:', projectId, scriptName, args);
      try {
        const scriptPath = this.projectManager.getProjectPythonScript(projectId, scriptName);
        if (!scriptPath) {
          return { success: false, error: 'Script not found' };
        }
        
        const result = await this.pythonManager.runPythonScript(scriptPath, args);
        return { success: true, output: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    ipcMain.handle('projects:loadContent', async (event, projectId) => {
      console.log('IPC: projects:loadContent chiamato con:', projectId);
      try {
        const project = this.projectManager.getProject(projectId);
        if (!project) {
          return { success: false, error: 'Project not found' };
        }
        
        const mainHtmlPath = this.projectManager.getProjectMainHtml(projectId);
        if (!mainHtmlPath) {
          return { success: false, error: 'Project main HTML not found' };
        }
        
        const fs = require('fs');
        const htmlContent = fs.readFileSync(mainHtmlPath, 'utf8');
        
        return { success: true, html: htmlContent };
      } catch (error) {
        console.error('Errore caricamento contenuto progetto:', error);
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('dialog:selectDirectory', async (event) => {
      const win = BrowserWindow.fromWebContents(event.sender);
      const result = await dialog.showOpenDialog(win, {
        properties: ['openDirectory']
      });
      if (result.canceled || !result.filePaths.length) return null;
      return result.filePaths[0];
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
