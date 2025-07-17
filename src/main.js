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

const logger = new Logger();
const managers = initializeManagers(); // Inizializza i manager

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
  setupIPC(managers); // Passa i manager agli handler IPC
  await initializeApp({ ...managers, logger }); 
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
