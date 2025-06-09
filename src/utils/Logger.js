const fs = require('fs');
const path = require('path');
const { app } = require('electron');

class Logger {
  constructor() {
    this.ensureLogDirectory();
  }

  ensureLogDirectory() {
    try {
      // Use userData directory instead of app path for logs
      const userDataPath = app.getPath('userData');
      this.logDir = path.join(userDataPath, 'logs');
      
      // Create directory recursively if it doesn't exist
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true });
      }
      
      this.logFile = path.join(this.logDir, 'app.log');
    } catch (error) {
      // Fallback: use temp directory if userData fails
      try {
        const tempDir = require('os').tmpdir();
        this.logDir = path.join(tempDir, 'scripta-image-processing');
        
        if (!fs.existsSync(this.logDir)) {
          fs.mkdirSync(this.logDir, { recursive: true });
        }
        
        this.logFile = path.join(this.logDir, 'app.log');
      } catch (fallbackError) {
        // Last resort: disable file logging
        console.warn('Could not create log directory:', error.message);
        this.logFile = null;
      }
    }
  }

  log(level, message, error = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    
    // Always log to console
    if (level === 'error') {
      console.error(logMessage, error || '');
    } else if (level === 'warn') {
      console.warn(logMessage);
    } else {
      console.log(logMessage);
    }
    
    // Log to file if available
    if (this.logFile) {
      try {
        const fileMessage = error ? `${logMessage}\n${error.stack || error}` : logMessage;
        fs.appendFileSync(this.logFile, fileMessage + '\n');
      } catch (writeError) {
        console.warn('Could not write to log file:', writeError.message);
      }
    }
  }

  info(message) {
    this.log('info', message);
  }

  warn(message) {
    this.log('warn', message);
  }

  error(message, error = null) {
    this.log('error', message, error);
  }
}

module.exports = Logger;
