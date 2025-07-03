import https from 'https';

export async function initializeApp(managers) {
  const { pythonManager, windowManager, logger } = managers;

  let loadingWindow = null;

  try {
    // Mostra la finestra di caricamento
    loadingWindow = windowManager.createLoadingWindow();
    logger.info('Avvio dello starter di configurazione...');

    // Aspetta che il DOM sia pronto
    loadingWindow.webContents.once('dom-ready', async () => {
      try {
        // Controlla la connessione Internet
        const online = await isOnline();
        if (!online) {
          loadingWindow.webContents.send('setup-progress', {
            step: 'error',
            message: 'Nessuna connessione Internet',
            error: 'Connessione Internet non disponibile. Verifica la connessione e riavvia l\'applicazione.',
            percentage: 0,
          });
          return;
        }

        // Controlla se Python è installato
        const pythonInstalled = await pythonManager.checkPythonInstallation();
        if (!pythonInstalled) {
          const pythonPath = pythonManager.getPythonExecutable();
          loadingWindow.webContents.send('setup-progress', {
            step: 'error',
            message: 'Python non trovato',
            error: `Python non trovato nel path: ${pythonPath}. Controllare se il file esiste in questa posizione.`,
            percentage: 0,
          });
          return;
        }

        // Configura l'ambiente Python con aggiornamenti di progresso
        await pythonManager.initialize((progress) => {
          if (loadingWindow && !loadingWindow.isDestroyed()) {
            loadingWindow.webContents.send('setup-progress', progress);
          }
        });

        logger.info('Inizializzazione completata con successo!');

        // Chiudi la finestra di caricamento e crea la finestra principale
        setTimeout(() => {
          windowManager.closeLoadingWindow();
          const mainWindow = windowManager.createMainWindow();
          if (mainWindow) {
            mainWindow.show();
          }
        }, 1000);
      } catch (error) {
        handleInitializationError(error, loadingWindow, logger, windowManager);
      }
    });
  } catch (error) {
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