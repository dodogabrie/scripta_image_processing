import { app, BrowserWindow } from 'electron';
import path from 'path';
import { initializeManagers } from './managers/index.js';
import { initializeApp } from './initialize.js';
import { fileURLToPath } from 'url';
import { setupIPC } from './setupIPC.js';

const managers = initializeManagers(); // Inizializza i manager

app.on('ready', async () => {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload', 'main-preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (process.env.NODE_ENV === 'development') {
    console.log('Running in development mode');
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist/renderer/index.html'));
  }

  setupIPC(managers); // Passa i manager agli handler IPC
  await initializeApp(managers); 
});

// Kill any active Python process before the app quits
app.on('before-quit', () => {
  if (managers.pythonManager) {
    managers.pythonManager.killActiveProcess();
  }
});

// existing window-all-closed and activate handlers
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    initializeApp(managers);
  }
});
