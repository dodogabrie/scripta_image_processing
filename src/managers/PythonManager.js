const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const os = require('os');
const Logger = require('../utils/Logger');
const { app } = require('electron');

class PythonManager {
  constructor() {
    this.logger = new Logger();
    this.venvPath = path.join(app.getAppPath(), 'python_env');
    this.pythonExecutable = this.getPythonExecutable();
    this.pipExecutable = this.getPipExecutable();
    this.status = {
      pythonInstalled: false,
      venvExists: false,
      dependenciesInstalled: false
    };
  }

  getPythonExecutable() {
    const isWindows = os.platform() === 'win32';
    
    // Usa l'interprete embedded se presente
    const embedded = path.join(app.getAppPath(), 'python-embed', 'python.exe');
    if (fs.existsSync(embedded)) return embedded;
    
    // fallback: venv o sistema
    return isWindows 
      ? path.join(this.venvPath, 'Scripts', 'python.exe')
      : path.join(this.venvPath, 'bin', 'python');
  }

  getPipExecutable() {
    const isWindows = os.platform() === 'win32';
    return isWindows 
      ? path.join(this.venvPath, 'Scripts', 'pip.exe')
      : path.join(this.venvPath, 'bin', 'pip');
  }

  async initialize(progressCallback = () => {}) {
    this.currentProgressCallback = progressCallback;
    this.logger.info('Initializing Python environment...');
    
    try {
      progressCallback({ step: 'python-check', message: 'Checking Python installation...', percentage: 25 });
      await this.checkPythonInstallation();
      
      progressCallback({ step: 'venv-setup', message: 'Setting up virtual environment...', percentage: 50 });
      await this.checkVirtualEnvironment();
      
      progressCallback({ step: 'deps-install', message: 'Installing dependencies...', percentage: 75 });
      await this.installDependencies();
      
      progressCallback({ step: 'complete', message: 'Python environment ready!', percentage: 100 });
      this.logger.info('Python environment ready');
    } catch (error) {
      progressCallback({ step: 'error', message: 'Setup failed', error: error.message, percentage: 0 });
      this.logger.error('Python environment setup failed:', error);
      throw error;
    } finally {
      this.currentProgressCallback = null;
    }
  }

  async checkPythonInstallation() {
    return new Promise((resolve, reject) => {
      const pythonCommand = os.platform() === 'win32' ? 'python.exe' : 'python';
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'python-check',
          message: 'Verifica installazione Python...',
          logs: `Running: ${pythonCommand} --version`
        });
      }

      exec(`${pythonCommand} --version`, (error, stdout, stderr) => {
        if (error) {
          this.logger.error('Python non trovato in PATH');
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'python-check',
              message: 'Python check failed',
              logs: `ERROR: ${error.message}`
            });
          }
          this.status.pythonInstalled = false;
          resolve(false); // Resolve with false
          return;
        }
        
        this.status.pythonInstalled = true;
        this.logger.info(`Python found: ${stdout.trim()}`);
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'python-check',
            message: 'Python installation verified',
            logs: `Found: ${stdout.trim()}`
          });
        }
        resolve(true); // Resolve with true
      });
    });
  }

  async checkVirtualEnvironment() {
    if (this.currentProgressCallback) {
      this.currentProgressCallback({
        step: 'venv-setup',
        message: 'Checking virtual environment...',
        logs: `Checking path: ${this.venvPath}`
      });
    }

    try {
      await fs.access(this.venvPath);
      await fs.access(this.pythonExecutable);
      this.status.venvExists = true;
      this.logger.info('Virtual environment exists');
      
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'venv-setup',
          message: 'Virtual environment found',
          logs: 'Virtual environment already exists and is ready'
        });
      }
    } catch (error) {
      this.logger.info('Creating virtual environment...');
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'venv-setup',
          message: 'Creating virtual environment...',
          logs: 'Creating new virtual environment...'
        });
      }
      await this.createVirtualEnvironment();
    }
  }

  async createVirtualEnvironment() {
    return new Promise((resolve, reject) => {
      // Use system Python to create venv, not the venv Python itself
      const systemPython = os.platform() === 'win32' ? 'python.exe' : 'python';
      
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'venv-setup',
          message: 'Creating virtual environment...',
          logs: `Running: ${systemPython} -m venv ${this.venvPath}`
        });
      }

      const process = spawn(systemPython, ['-m', 'venv', this.venvPath]);
      
      process.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'Creating virtual environment...',
            logs: output
          });
        }
      });

      process.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'Creating virtual environment...',
            logs: output
          });
        }
      });

      process.on('close', (code) => {
        if (code === 0) {
          this.status.venvExists = true;
          this.logger.info('Virtual environment created successfully');
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'venv-setup',
              message: 'Virtual environment created',
              logs: 'Virtual environment created successfully!'
            });
          }
          
          // Install pip in the venv
          this.installPipInVenv().then(resolve).catch(reject);
          
        } else {
          const errorMsg = `Failed to create virtual environment. Exit code: ${code}`;
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'venv-setup',
              message: 'Virtual environment creation failed',
              logs: `ERROR: ${errorMsg}`
            });
          }
          reject(new Error(errorMsg));
        }
      });

      process.on('error', (error) => {
        const errorMsg = `Failed to create virtual environment: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'Virtual environment creation failed',
            logs: `ERROR: ${errorMsg}`
          });
        }
        reject(new Error(errorMsg));
      });
    });
  }

  async installPipInVenv() {
    return new Promise((resolve, reject) => {
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'venv-setup',
          message: 'Installing pip in virtual environment...',
          logs: `Running: ${this.pythonExecutable} -m ensurepip`
        });
      }

      const process = spawn(this.pythonExecutable, ['-m', 'ensurepip'], {
        cwd: this.venvPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      process.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'Installing pip in virtual environment...',
            logs: output
          });
        }
      });

      process.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'Installing pip in virtual environment...',
            logs: output
          });
        }
      });

      process.on('close', (code) => {
        if (code === 0) {
          this.logger.info('pip installed successfully in virtual environment');
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'venv-setup',
              message: 'pip installed in virtual environment',
              logs: 'pip installed successfully in virtual environment!'
            });
          }
          
          // Update pipExecutable after installation
          this.pipExecutable = this.getPipExecutable();
          resolve();
        } else {
          const errorMsg = `Failed to install pip in virtual environment. Exit code: ${code}`;
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'venv-setup',
              message: 'pip installation failed',
              logs: `ERROR: ${errorMsg}`
            });
          }
          reject(new Error(errorMsg));
        }
      });

      process.on('error', (error) => {
        const errorMsg = `Failed to install pip in virtual environment: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'venv-setup',
            message: 'pip installation failed',
            logs: `ERROR: ${errorMsg}`
          });
        }
        reject(new Error(errorMsg));
      });
    });
  }

  async installDependencies() {
    const requirementsPath = path.join(__dirname, '../requirements.txt');
    
    try {
      await fs.access(requirementsPath);
    } catch (error) {
      this.logger.info('No requirements.txt found, skipping dependency installation');
      this.status.dependenciesInstalled = true;
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'deps-install',
          message: 'No dependencies to install',
          logs: 'No requirements.txt found, skipping dependency installation'
        });
      }
      return;
    }

    if (this.currentProgressCallback) {
      this.currentProgressCallback({
        step: 'deps-install',
        message: 'Installing Python packages...',
        logs: `Running: ${this.pipExecutable} install -r requirements.txt`
      });
    }

    return new Promise((resolve, reject) => {
      const pipPath = this.pipExecutable; // Use the correct pip path
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: 'deps-install',
          message: 'Installing Python packages...',
          logs: `Running: ${pipPath} install -r requirements.txt`
        });
      }

      const process = spawn(pipPath, ['install', '-r', requirementsPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      process.stdout.on('data', (data) => {
        const output = data.toString().trim();
        this.logger.info(`pip stdout: ${output}`);
        
        if (output && this.currentProgressCallback) {
          // Split multi-line output and send each line
          const lines = output.split('\n').filter(line => line.trim());
          lines.forEach(line => {
            this.currentProgressCallback({
              step: 'deps-install',
              message: 'Installing Python packages...',
              logs: line.trim()
      });
      });
        }
      });

      process.stderr.on('data', (data) => {
        const output = data.toString().trim();
        this.logger.warn(`pip stderr: ${output}`);
        
        if (output && this.currentProgressCallback) {
          const lines = output.split('\n').filter(line => line.trim());
          lines.forEach(line => {
            this.currentProgressCallback({
              step: 'deps-install',
              message: 'Installing Python packages...',
              logs: line.trim()
      });
      });
        }
      });

      process.on('close', (code) => {
        if (code === 0) {
          this.status.dependenciesInstalled = true;
          this.logger.info('Dependencies installed successfully');
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'deps-install',
              message: 'Dependencies installed successfully',
              logs: 'All Python packages installed successfully!'
            });
          }
          resolve();
        } else {
          const errorMsg = `Failed to install dependencies. Exit code: ${code}`;
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: 'deps-install',
              message: 'Dependency installation failed',
              logs: `ERROR: ${errorMsg}`
            });
          }
          reject(new Error(errorMsg));
        }
      });

      process.on('error', (error) => {
        const errorMsg = `Failed to install dependencies: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: 'deps-install',
            message: 'Dependency installation failed',
            logs: `ERROR: ${errorMsg}`
          });
        }
        reject(new Error(errorMsg));
      });
    });
  }

  async runPythonScript(scriptPath, args = []) {
    return new Promise((resolve, reject) => {
      const py = spawn(this.pythonExecutable, [scriptPath, ...args]);
      let output = '';
      let error = '';

      py.stdout.on('data', (data) => { output += data.toString(); });
      py.stderr.on('data', (data) => { error += data.toString(); });

      py.on('close', (code) => {
          if (code === 0) {
              resolve({ success: true, output });
          } else {
              resolve({ success: false, error: error || output });
          }
      });
    });
  }

  getStatus() {
    return { 
      ready: this.status.pythonInstalled && this.status.venvExists && this.status.dependenciesInstalled,
      ...this.status 
    };
  }

  async installEnvironment(progressCallback) {
    try {
      await this.initialize(progressCallback);
      return { success: true, message: 'Python environment ready' };
    } catch (error) {
      if (progressCallback) {
        progressCallback({
          step: 'error',
          message: 'Errore durante l\'installazione dell\'ambiente Python',
          logs: error.message
        });
      }
      return { success: false, error: error.message };
    }
  }
}

module.exports = PythonManager;