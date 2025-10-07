import { app, BrowserWindow } from 'electron';
import path from 'path';
import { initializeManagers } from './managers/index.js';
import { initializeApp } from './initialize.js';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { setupIPC } from './setupIPC.js';
import Logger from './utils/Logger.js';

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { autoUpdater } = require('./updater.cjs');

const logger = new Logger();
const managers = initializeManagers(); // Inizializza i manager

// Configure auto-updater
autoUpdater.logger = logger;
autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

// Auto-updater event handlers
autoUpdater.on('checking-for-update', () => {
  logger.info('Checking for updates...');
});

autoUpdater.on('update-available', (info) => {
  logger.info('Update available:', info.version);
});

autoUpdater.on('update-not-available', (info) => {
  logger.info('Update not available. Current version:', info.version);
});

autoUpdater.on('error', (err) => {
  logger.error('Error in auto-updater:', err);
});

autoUpdater.on('download-progress', (progressObj) => {
  logger.info(`Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`);
});

autoUpdater.on('update-downloaded', (info) => {
  logger.info('Update downloaded. Version:', info.version);
  // Notify all windows that update is ready
  BrowserWindow.getAllWindows().forEach(win => {
    win.webContents.send('update:downloaded', info);
  });
});

logger.info('App avviata, managers inizializzati');

app.on('ready', async () => {

  if (process.env.NODE_ENV === 'development') {
    const { default: installExtension, VUEJS_DEVTOOLS } = require('electron-devtools-installer');
    try {
      const name = await installExtension(VUEJS_DEVTOOLS);
      logger.info(`Vue Devtools installati: ${name}`);
    } catch (err) {
      logger.error('Errore installazione Vue Devtools:', err);
    }
  }


  logger.info('App ready event');
  setupIPC(managers, autoUpdater); // Passa i manager e autoUpdater agli handler IPC
  await initializeApp({ ...managers, logger });

  // Check for updates only in production
  if (process.env.NODE_ENV !== 'development') {
    logger.info('Checking for updates...');
    autoUpdater.checkForUpdatesAndNotify();
  }
});

// Kill any active Python process before the app quits
app.on('before-quit', () => {
  logger.info('App before-quit event');

  if (managers.pythonManager) {
    managers.pythonManager.killActiveProcess();
    logger.info('Python process killed');
  }

  if (process.env.NODE_ENV === 'development') {
    try {
      execSync(`pkill -f vite`, { stdio: 'ignore' });
      logger.info('Processo Vite terminato');
    } catch (e) {
      logger.warn('Nessun processo Vite da terminare');
    }
  }
});

// existing window-all-closed and activate handlers
app.on('window-all-closed', () => {
  logger.info('window-all-closed event');
  if (process.platform !== 'darwin') {
    app.quit();
    logger.info('App quit');
  }
});

app.on('activate', () => {
  logger.info('App activate event');
  if (BrowserWindow.getAllWindows().length === 0) {
    initializeApp({ ...managers, logger });
    logger.info('App re-initialized');
  }
});
