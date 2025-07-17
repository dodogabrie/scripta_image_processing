import https from 'https';

export async function initializeApp(managers) {
  const { pythonManager, windowManager, logger } = managers;

  let loadingWindow = null;

  try {
    logger.info('Mostra la finestra di caricamento');
    // Mostra la finestra di caricamento
    loadingWindow = windowManager.createLoadingWindow();
    logger.info('Avvio dello starter di configurazione...');

    // Aspetta che il DOM sia pronto
    loadingWindow.webContents.once('dom-ready', async () => {
      try {
        logger.info('DOM pronto, controllo connessione Internet');
        // Controlla la connessione Internet
        const online = await isOnline();
        if (!online) {
          logger.warn('Nessuna connessione Internet');
          loadingWindow.webContents.send('setup-progress', {
            step: 'error',
            message: 'Nessuna connessione Internet',
            error: 'Connessione Internet non disponibile. Verifica la connessione e riavvia l\'applicazione.',
            percentage: 0,
          });
          return;
        }

        logger.info('Connessione Internet OK, controllo Python');
        // Controlla se Python è installato
        const pythonInstalled = await pythonManager.checkPythonInstallation();
        if (!pythonInstalled) {
          const pythonPath = pythonManager.getPythonExecutable();
          logger.error('Python non trovato', new Error(`Python non trovato nel path: ${pythonPath}`));
          loadingWindow.webContents.send('setup-progress', {
            step: 'error',
            message: 'Python non trovato',
            error: `Python non trovato nel path: ${pythonPath}. Controllare se il file esiste in questa posizione.`,
            percentage: 0,
          });
          return;
        }

        logger.info('Python trovato, inizializzo ambiente Python');
        // Configura l'ambiente Python con aggiornamenti di progresso
        await pythonManager.initialize((progress) => {
          logger.info(`Progresso setup: ${progress.step} - ${progress.message}`);
          if (loadingWindow && !loadingWindow.isDestroyed()) {
            loadingWindow.webContents.send('setup-progress', progress);
          }
        });

        logger.info('Inizializzazione completata con successo!');

        // Chiudi la finestra di caricamento e crea la finestra principale
        setTimeout(() => {
          logger.info('Chiudo loading window e apro main window');
          windowManager.closeLoadingWindow();
          const mainWindow = windowManager.createMainWindow();
          if (mainWindow) {
            mainWindow.show();
            logger.info('Main window mostrata');
          }
        }, 1000);
      } catch (error) {
        logger.error('Errore durante l\'inizializzazione', error);
        handleInitializationError(error, loadingWindow, logger, windowManager);
      }
    });
  } catch (error) {
    logger.error('Errore globale in initializeApp', error);
    handleInitializationError(error, loadingWindow, logger, windowManager);
  }
}

async function isOnline() {
  return new Promise((resolve) => {
    const request = https.request('https://www.google.com', (response) => {
      resolve(response.statusCode === 200);
    });
    request.on('error', () => {
      resolve(false);
    });
    request.end();
  });
}

function handleInitializationError(error, loadingWindow, logger, windowManager) {
  logger.error('Initialization failed:', error);

  if (loadingWindow && !loadingWindow.isDestroyed()) {
    loadingWindow.webContents.send('setup-progress', {
      step: 'error',
      message: 'Setup Failed',
      error: error.message,
      percentage: 0,
    });
  }

  setTimeout(() => {
    windowManager.createErrorWindow(error.message);
  }, 3000);
}