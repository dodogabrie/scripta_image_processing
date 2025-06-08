const { BrowserWindow } = require('electron');
const path = require('path');

class WindowManager {
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
        preload: path.join(__dirname, '../preload/main-preload.js')
      }
    });

    this.mainWindow.loadFile(path.join(__dirname, '../renderer/main.html'));

    this.mainWindow.once('ready-to-show', () => {
      if (this.loadingWindow) {
        this.loadingWindow.close();
        this.loadingWindow = null;
      }
      this.mainWindow.show();
    });

    if (process.argv.includes('--dev')) {
      this.mainWindow.webContents.openDevTools();
    }

    return this.mainWindow;
  }

  createLoadingWindow() {
    this.loadingWindow = new BrowserWindow({
      width: 500,
      height: 600,
      // frame: false,
      alwaysOnTop: true,
      resizable: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/loading-preload.js')
      }
    });

    this.loadingWindow.loadFile(path.join(__dirname, '../renderer/loading.html'));
    
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
        preload: path.join(__dirname, '../preload/error-preload.js')
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
        preload: path.join(__dirname, '../preload/project-preload.js')
      }
    });

    projectWindow.loadFile(projectHtmlPath);
    
    projectWindow.webContents.once('dom-ready', () => {
      console.log('Project window DOM ready');
    });

    return projectWindow;
  }
}

module.exports = WindowManager;
