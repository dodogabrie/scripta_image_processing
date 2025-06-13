const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { net, dialog } = require('electron');
const fs = require('fs');

// Import managers with error handling for development
let PythonManager, WindowManager, Logger, ProjectManager;
try {
  PythonManager = require('./managers/PythonManager');
  WindowManager = require('./managers/WindowManager');
  Logger = require('./utils/Logger');
  ProjectManager = require('./managers/ProjectManager');
} catch (error) {
  console.error('Missing dependencies...');
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

      // Wait for DOM to be ready before sending progress
      this.loadingWindow.webContents.once('dom-ready', async () => {
        try {
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

    ipcMain.handle('python:stop', async () => {
      console.log('IPC: python:stop chiamato');
      return this.pythonManager.stopPythonProcess();
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
        
        return await this.pythonManager.runPythonScript(scriptPath, args);
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

    ipcMain.handle('files:listThumbs', async (event, thumbsDir) => {
      try {
          const fs = require('fs');
          const path = require('path');
          // Usa thumbsDir passato dal renderer, fallback su output/thumbs se non fornito
          const dir = thumbsDir || path.join(process.cwd(), 'output', 'thumbs');
          if (!fs.existsSync(dir)) return [];
          const files = fs.readdirSync(dir)
              .filter(f => f.toLowerCase().endsWith('.jpg'))
              .map(f => path.join(dir, f).replace(/\\/g, '/'));
          return files;
      } catch (e) {
          return [];
      }
    });

    ipcMain.handle('files:listQualityFiles', async (event, qualityDir) => {
        try {
            const fs = require('fs');
            const path = require('path');
            if (!fs.existsSync(qualityDir)) return [];
            return fs.readdirSync(qualityDir)
                .filter(f => f.toLowerCase().endsWith('.json'))
                .map(f => path.join(qualityDir, f).replace(/\\/g, '/'));
        } catch (e) {
            return [];
        }
    });

    ipcMain.handle('files:readFile', async (event, filePath) => {
        try {
            const fs = require('fs');
            return fs.readFileSync(filePath, 'utf8');
        } catch (e) {
            return '';
        }
    });

    ipcMain.handle('files:writeFile', async (event, filePath, content) => {
        try {
            const fs = require('fs');
            fs.writeFileSync(filePath, content, 'utf8');
            return true;
        } catch (e) {
            return false;
        }
    });

    // Generic logging handler
    ipcMain.on('log:fromRenderer', (event, msg) => {
        console.log('Log from renderer:', msg);
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
