const fs = require('fs');
const path = require('path');

class Logger {
  constructor() {
    this.logDir = path.join(__dirname, '..', '..', 'logs');
    this.logFile = path.join(this.logDir, 'app.log');
    this.ensureLogDirectory();
  }

  ensureLogDirectory() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  formatMessage(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    
    if (data) {
      return `${logMessage}\n${JSON.stringify(data, null, 2)}`;
    }
    
    return logMessage;
  }

  writeToFile(message) {
    try {
      fs.appendFileSync(this.logFile, message + '\n');
    } catch (error) {
      console.error('Failed to write to log file:', error);
    }
  }

  info(message, data = null) {
    const logMessage = this.formatMessage('info', message, data);
    console.log(logMessage);
    this.writeToFile(logMessage);
  }

  warn(message, data = null) {
    const logMessage = this.formatMessage('warn', message, data);
    console.warn(logMessage);
    this.writeToFile(logMessage);
  }

  error(message, data = null) {
    const logMessage = this.formatMessage('error', message, data);
    console.error(logMessage);
    this.writeToFile(logMessage);
  }

  debug(message, data = null) {
    if (process.argv.includes('--dev')) {
      const logMessage = this.formatMessage('debug', message, data);
      console.log(logMessage);
      this.writeToFile(logMessage);
    }
  }
}

module.exports = Logger;
