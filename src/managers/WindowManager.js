import { BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default class WindowManager {

  constructor() {
    this.mainWindow = null;
    this.loadingWindow = null;
  }

  createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1600,
      height: 1000,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/main-preload.cjs')
      }
    });

    const isDev = process.env.NODE_ENV === 'development';
    
    let rendererPath;
    if (isDev) {
      rendererPath = 'http://localhost:5173';
    } else {
      // In produzione, il renderer è in dist/renderer relative al package root
      // __dirname punta a src/managers/, quindi ../../dist/renderer/index.html
      rendererPath = path.join(__dirname, '../../dist/renderer/index.html');
      
      // Verifica che il file esista (per debug)
      import('fs').then(fs => {
        if (!fs.existsSync(rendererPath)) {
          console.error('Renderer file not found at:', rendererPath);
          console.error('__dirname:', __dirname);
          console.error('Alternative paths to check:');
          console.error('- Current working directory:', process.cwd());
          console.error('- Process resource path:', process.resourcesPath || 'N/A');
        }
        else {
          console.log('Renderer file found at:', rendererPath);
        }
      });
    }
    
    console.log(isDev ? 'Loading renderer in development mode' : `Loading renderer in production mode: ${rendererPath}`);
    if (isDev) {
      this.mainWindow.loadURL(rendererPath);
    } else {
      this.mainWindow.loadFile(rendererPath).catch(err => {
        console.error('Failed to load renderer:', err);
        // Fallback: prova il path diretto se il path calcolato fallisce
        const fallbackPath = path.join(process.resourcesPath, 'app.asar', 'dist', 'renderer', 'index.html');
        console.log('Trying fallback path:', fallbackPath);
        this.mainWindow.loadFile(fallbackPath);
      });
    }

    this.mainWindow.once('ready-to-show', () => {
      if (this.loadingWindow) {
        this.loadingWindow.close();
        this.loadingWindow = null;
      }
      this.mainWindow.show();
      if (isDev) {
        this.mainWindow.webContents.openDevTools({ mode: 'bottom' }); 
      }
    });
    return this.mainWindow;
  }

  createLoadingWindow() {
    this.loadingWindow = new BrowserWindow({
      width: 600,
      height: 800,
      // frame: false,
      alwaysOnTop: true,
      resizable: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/loading-preload.cjs')
      }
    });

    // In produzione, usa il path corretto per l'AppImage
    const isDev = process.env.NODE_ENV === 'development';
    const loadingPath = isDev 
      ? path.join(__dirname, '../renderer/loading.html')
      : path.join(__dirname, '../renderer/loading.html');
    
    this.loadingWindow.loadFile(loadingPath);
    // Wait for DOM to be ready before allowing messages
    this.loadingWindow.webContents.once('dom-ready', () => {
      console.log('Loading window DOM ready');
    });
    return this.loadingWindow;
  }

  closeLoadingWindow() {
    if (this.loadingWindow && !this.loadingWindow.isDestroyed()) {
      this.loadingWindow.close();
      this.loadingWindow = null;
    }
  }

  createErrorWindow(errorMessage) {
    const errorWindow = new BrowserWindow({
      width: 500,
      height: 400,
      resizable: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/error-preload.cjs')
      }
    });

    errorWindow.loadFile(path.join(__dirname, '../renderer/error.html'));
    errorWindow.webContents.once('dom-ready', () => {
      errorWindow.webContents.send('error-message', errorMessage);
    });
  }

  createProjectWindow(projectHtmlPath) {
    const projectWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      show: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/project-preload.cjs')
      }
    });

    projectWindow.loadFile(projectHtmlPath);
    projectWindow.webContents.once('dom-ready', () => {
      console.log('Project window DOM ready');
    });
    return projectWindow;
  }
}

