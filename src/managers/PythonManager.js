import { spawn, exec } from "child_process";
import fs from "fs/promises";
import fsSync from "fs";
import path from "path";
import os from "os";
import Logger from "../utils/Logger.js";
import { app } from "electron";

export default class PythonManager {
  constructor() {
    this.logger = new Logger();
    this.venvPath = path.join(app.getPath("userData"), "python_env");
    this.pythonExecutable = this.getPythonExecutable();
    this.pipExecutable = this.getPipExecutable();
    this.status = {
      pythonInstalled: false,
      venvExists: false,
      dependenciesInstalled: false,
    };
    this.activeProcess = null; // Track the active Python process
  }

  getPythonExecutable() {
    const isWindows = os.platform() === "win32";
    console.log("PythonManager: Determining Python executable path...");
    console.log("PythonManager: isWindows:", isWindows);
    console.log("PythonManager: venvPath:", this.venvPath);
    console.log("PythonManager: app.getAppPath():", app.getAppPath());
    console.log("PythonManager: app.isPackaged:", app.isPackaged);
    console.log(
      'PythonManager: app.getPath("userData"):',
      app.getPath("userData"),
    );

    // In development mode, use system Python
    if (!app.isPackaged) {
      const systemPython = isWindows ? "python.exe" : ".venv/bin/python";
      this.logger.info("Development mode: Using system Python:", systemPython);
      return systemPython;
    }

    // In production, use embedded Python if available
    if (isWindows) {
      // Il Python embedded ora è nella root dell'app grazie a extraFiles
      const embedded = path.join(
        path.dirname(process.resourcesPath),
        "python-embed",
        "python.exe",
      );
      try {
        if (fsSync.existsSync(embedded)) {
          this.logger.info("Using embedded Python:", embedded);
          return embedded;
        }
      } catch (e) {
        this.logger.warn("Error checking embedded Python:", e.message);
      }
    }

    // Fallback: venv in AppData/Roaming
    return isWindows
      ? path.join(this.venvPath, "Scripts", "python.exe")
      : path.join(this.venvPath, "bin", "python");
  }

  getPipExecutable() {
    const isWindows = os.platform() === "win32";

    if (isWindows) {
      const embeddedPython = path.join(
        path.dirname(app.getAppPath()),
        "python-embed",
        "python.exe",
      );

      try {
        if (fsSync.existsSync(embeddedPython)) {
          // Usa "python -m pip" invece di pip.exe diretto
          this.logger.info("Using embedded Python pip module");
          return embeddedPython; // Ritorna python.exe, userai -m pip
        }
      } catch (e) {
        this.logger.warn("Error checking embedded Python:", e.message);
      }
    }

    return isWindows
      ? path.join(this.venvPath, "Scripts", "pip.exe")
      : path.join(this.venvPath, "bin", "pip");
  }

  async initialize(progressCallback = () => {}) {
    this.currentProgressCallback = progressCallback;
    this.logger.info("Initializing Python environment...");

    try {
      progressCallback({
        step: "python-check",
        message: "Checking Python installation...",
        percentage: 25,
      });
      await this.checkPythonInstallation();

      progressCallback({
        step: "venv-setup",
        message: "Setting up virtual environment...",
        percentage: 50,
      });
      await this.checkVirtualEnvironment();

      progressCallback({
        step: "deps-install",
        message: "Installing dependencies...",
        percentage: 75,
      });
      await this.installDependencies();

      progressCallback({
        step: "complete",
        message: "Python environment ready!",
        percentage: 100,
      });
      this.logger.info("Python environment ready");
    } catch (error) {
      progressCallback({
        step: "error",
        message: "Setup failed",
        error: error.message,
        percentage: 0,
      });
      this.logger.error("Python environment setup failed:", error);
      throw error;
    } finally {
      this.currentProgressCallback = null;
    }
  }

  async checkPythonInstallation() {
    return new Promise((resolve, reject) => {
      const pythonCmd = this.pythonExecutable;

      // Se stiamo usando Python embedded su Windows, salta il check della versione
      const isWindows = os.platform() === "win32";
      if (isWindows) {
        const embeddedPath = path.join(
          path.dirname(app.getAppPath()),
          "python-embed",
          "python.exe",
        );
        if (fsSync.existsSync(embeddedPath)) {
          this.logger.info("Using embedded Python, skipping venv creation");
          this.status.pythonInstalled = true;
          return resolve(true);
        }
      }

      exec(`"${pythonCmd}" --version`, (error, stdout, stderr) => {
        if (error) {
          const errorMsg = `Python non trovato: ${error.message}`;
          this.logger.error(errorMsg);
          this.status.pythonInstalled = false;
          return reject(new Error(errorMsg)); // Usa reject invece di resolve(false)
        }

        const versionMatch = (stdout + stderr).match(/Python (\d+)\.(\d+)/);
        if (versionMatch) {
          const major = parseInt(versionMatch[1]);
          const minor = parseInt(versionMatch[2]);

          // Accetta Python 3.8+ invece di richiedere specificamente 3.11
          if (major === 3 && minor >= 8) {
            this.logger.info(`Python ${major}.${minor} found and compatible`);
            this.status.pythonInstalled = true;
            return resolve(true);
          } else {
            const errorMsg = `Python ${major}.${minor} trovato ma richiede Python 3.8+`;
            this.logger.warn(errorMsg);
            this.status.pythonInstalled = false;
            return reject(new Error(errorMsg));
          }
        }

        const errorMsg = "Versione Python non riconosciuta";
        this.logger.error(errorMsg);
        this.status.pythonInstalled = false;
        reject(new Error(errorMsg));
      });
    });
  }

  async checkVirtualEnvironment() {
    // If using embedded Python on Windows, skip venv creation
    const isWindows = os.platform() === "win32";
    if (isWindows) {
      const embedded = path.join(
        path.dirname(app.getAppPath()),
        "python-embed",
        "python.exe",
      );
      if (fsSync.existsSync(embedded)) {
        this.status.venvExists = true;
        this.logger.info("Using embedded Python, skipping venv setup");
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Using embedded Python environment",
            logs: "Embedded Python found, skipping virtual environment creation",
          });
        }
        return;
      }
    }

    if (this.currentProgressCallback) {
      this.currentProgressCallback({
        step: "venv-setup",
        message: "Checking virtual environment...",
        logs: `Checking path: ${this.venvPath}`,
      });
    }

    try {
      await fs.access(this.venvPath);
      await fs.access(this.pythonExecutable);
      this.status.venvExists = true;
      this.logger.info("Virtual environment exists");

      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: "venv-setup",
          message: "Virtual environment found",
          logs: "Virtual environment already exists and is ready",
        });
      }
    } catch (error) {
      this.logger.info("Creating virtual environment...");
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: "venv-setup",
          message: "Creating virtual environment...",
          logs: "Creating new virtual environment...",
        });
      }
      await this.createVirtualEnvironment();
    }
  }

  async createVirtualEnvironment() {
    return new Promise((resolve, reject) => {
      // Use system Python to create venv, not the venv Python itself
      const systemPython = os.platform() === "win32" ? "python.exe" : "python";

      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: "venv-setup",
          message: "Creating virtual environment...",
          logs: `Running: ${systemPython} -m venv ${this.venvPath}`,
        });
      }

      const process = spawn(systemPython, ["-m", "venv", this.venvPath], {
        windowsHide: true  // Hide console window on Windows
      });

      process.stdout.on("data", (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Creating virtual environment...",
            logs: output,
          });
        }
      });

      process.stderr.on("data", (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Creating virtual environment...",
            logs: output,
          });
        }
      });

      process.on("close", (code) => {
        if (code === 0) {
          this.status.venvExists = true;
          this.logger.info("Virtual environment created successfully");
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "venv-setup",
              message: "Virtual environment created",
              logs: "Virtual environment created successfully!",
            });
          }

          // Install pip in the venv
          this.installPipInVenv().then(resolve).catch(reject);
        } else {
          const errorMsg = `Failed to create virtual environment. Exit code: ${code}`;
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "venv-setup",
              message: "Virtual environment creation failed",
              logs: `ERROR: ${errorMsg}`,
            });
          }
          reject(new Error(errorMsg));
        }
      });

      process.on("error", (error) => {
        const errorMsg = `Failed to create virtual environment: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Virtual environment creation failed",
            logs: `ERROR: ${errorMsg}`,
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
          step: "venv-setup",
          message: "Installing pip in virtual environment...",
          logs: `Running: ${this.pythonExecutable} -m ensurepip`,
        });
      }

      const process = spawn(this.pythonExecutable, ["-m", "ensurepip"], {
        cwd: this.venvPath,
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true  // Hide console window on Windows
      });

      process.stdout.on("data", (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Installing pip in virtual environment...",
            logs: output,
          });
        }
      });

      process.stderr.on("data", (data) => {
        const output = data.toString().trim();
        if (output && this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "Installing pip in virtual environment...",
            logs: output,
          });
        }
      });

      process.on("close", (code) => {
        if (code === 0) {
          this.logger.info("pip installed successfully in virtual environment");
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "venv-setup",
              message: "pip installed in virtual environment",
              logs: "pip installed successfully in virtual environment!",
            });
          }

          // Update pipExecutable after installation
          this.pipExecutable = this.getPipExecutable();
          resolve();
        } else {
          const errorMsg = `Failed to install pip in virtual environment. Exit code: ${code}`;
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "venv-setup",
              message: "pip installation failed",
              logs: `ERROR: ${errorMsg}`,
            });
          }
          reject(new Error(errorMsg));
        }
      });

      process.on("error", (error) => {
        const errorMsg = `Failed to install pip in virtual environment: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "venv-setup",
            message: "pip installation failed",
            logs: `ERROR: ${errorMsg}`,
          });
        }
        reject(new Error(errorMsg));
      });
    });
  }

  async installDependencies() {
    const collectedStderr = [];

    let requirementsPath;
    if (app.isPackaged) {
      requirementsPath = path.join(
        process.resourcesPath,
        "app.asar.unpacked",
        "requirements.txt",
      );
    } else {
      requirementsPath = path.join(app.getAppPath(), "requirements.txt");
    }

    try {
      await fs.access(requirementsPath);
    } catch (error) {
      this.logger.info(
        "No requirements.txt found, skipping dependency installation",
      );
      this.status.dependenciesInstalled = true;
      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: "deps-install",
          message: "No dependencies to install",
          logs: "No requirements.txt found, skipping dependency installation",
        });
      }
      return;
    }

    return new Promise((resolve, reject) => {
      const isWindows = os.platform() === "win32";
      const embeddedPython = path.join(
        path.dirname(app.getAppPath()),
        "python-embed",
        "python.exe",
      );

      let pipProcess; // ← RINOMINA da 'process' a 'pipProcess'

      if (isWindows && fsSync.existsSync(embeddedPython)) {
        // Usa python -m pip per embedded
        pipProcess = spawn(
          embeddedPython,
          ["-m", "pip", "install", "-r", requirementsPath],
          {
            stdio: ["pipe", "pipe", "pipe"],
            env: process.env,
            windowsHide: true  // Hide console window on Windows
          },
        );
      } else {
        // Usa pip normale per venv
        pipProcess = spawn(
          this.pipExecutable,
          ["install", "-r", requirementsPath],
          {
            stdio: ["pipe", "pipe", "pipe"],
            env: process.env,
            windowsHide: true  // Hide console window on Windows
          },
        );
      }

      if (this.currentProgressCallback) {
        this.currentProgressCallback({
          step: "deps-install",
          message: "Installing Python packages...",
          logs: `Running pip install...`,
        });
      }

      pipProcess.stdout.on("data", (data) => {
        const output = data.toString().trim();
        this.logger.info(`pip stdout: ${output}`);

        if (output && this.currentProgressCallback) {
          const lines = output.split("\n").filter((line) => line.trim());
          lines.forEach((line) => {
            this.currentProgressCallback({
              step: "deps-install",
              message: "Installing Python packages...",
              logs: line.trim(),
            });
          });
        }
      });

      pipProcess.stderr.on("data", (data) => {
        const output = data.toString().trim();
        collectedStderr.push(output);
        this.logger.warn(`pip stderr: ${output}`);

        if (output && this.currentProgressCallback) {
          const lines = output.split("\n").filter((line) => line.trim());
          lines.forEach((line) => {
            this.currentProgressCallback({
              step: "deps-install",
              message: "Installing Python packages...",
              logs: line.trim(),
            });
          });
        }
      });

      pipProcess.on("close", (code) => {
        if (code === 0) {
          this.status.dependenciesInstalled = true;
          this.logger.info("Dependencies installed successfully");
          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "deps-install",
              message: "Dependencies installed successfully",
              logs: "All Python packages installed successfully!",
            });
          }
          resolve();
        } else {
          const stderrCombined = collectedStderr.join("\n");
          const errorMsg = `❌ Failed to install dependencies (exit code ${code})\n\nDetails:\n${stderrCombined}`;

          if (this.currentProgressCallback) {
            this.currentProgressCallback({
              step: "deps-install",
              message: "Dependency installation failed",
              logs: `ERROR:\n${errorMsg}`,
            });
          }
          reject(new Error(errorMsg));
        }
      });

      pipProcess.on("error", (error) => {
        const errorMsg = `Failed to install dependencies: ${error.message}`;
        if (this.currentProgressCallback) {
          this.currentProgressCallback({
            step: "deps-install",
            message: "Dependency installation failed",
            logs: `ERROR: ${errorMsg}`,
          });
        }
        reject(new Error(errorMsg));
      });
    });
  }

  async runPythonScript(scriptPath, args = []) {
    return new Promise((resolve, reject) => {
      let finished = false;
      let output = "";
      let error = "";

      // Log del path Python usato
      this.logger.info(`🐍 Executing Python at: ${this.pythonExecutable}`);
      this.logger.info(`📜 Script path: ${scriptPath}`);
      this.logger.info(`📋 Arguments: ${JSON.stringify(args)}`);

      // Costruisci il path delle DLL di vips
      const isWindows = process.platform === "win32";
      let vipsBinDir = null;
      if (isWindows) {
        // In produzione: cerca in app.asar.unpacked
        let baseDir;
        if (app.isPackaged) {
          baseDir = path.join(
            process.resourcesPath,
            "app.asar.unpacked",
            "src",
            "python-embed",
            "vips-bin",
            "vips-dev-8.17",
            "bin",
          );
        } else {
          // In sviluppo: path relativo al progetto
          baseDir = path.join(
            __dirname,
            "..",
            "..",
            "python-embed",
            "vips-bin",
            "vips-dev-8.17",
            "bin",
          );
        }
        vipsBinDir = baseDir;
      }

      // Prepara l'env per il processo Python
      const env = { ...process.env };
      if (isWindows && vipsBinDir) {
        env.PATH = vipsBinDir + ";" + env.PATH;
      }

      let py;
      try {
        py = spawn(this.pythonExecutable, [scriptPath, ...args], {
          env,
          windowsHide: true  // Hide console window on Windows
        });
        this.activeProcess = py; // Track the active process
      } catch (spawnErr) {
        return resolve({
          success: false,
          error: `Failed to start Python: ${spawnErr.message}`,
        });
      }

      py.stdout.on("data", (data) => {
        output += data.toString();
      });
      py.stderr.on("data", (data) => {
        error += data.toString();
      });

      // Aggiungi info sul Python usato all'inizio dell'output
      let debugInfo = `🐍 Python executable: ${this.pythonExecutable}\n`;

      if (isWindows) {
        const appDir = path.dirname(app.getAppPath());
        const embeddedPath = path.join(appDir, "python-embed", "python.exe");
        debugInfo += `📁 App directory: ${appDir}\n`;
        debugInfo += `🔍 Looking for embedded at: ${embeddedPath}\n`;
        debugInfo += `✅ Embedded exists: ${fsSync.existsSync(embeddedPath)}\n`;
      }

      debugInfo += `📜 Script: ${path.basename(scriptPath)}\n\n`;
      output = debugInfo;

      py.on("close", (code) => {
        if (finished) return;
        finished = true;
        this.activeProcess = null; // Clear on exit
        if (code === 0) {
          resolve({ success: true, output });
        } else {
          resolve({
            success: false,
            error: error || output || `Python exited with code ${code}`,
          });
        }
      });

      py.on("error", (err) => {
        if (finished) return;
        finished = true;
        this.activeProcess = null;
        resolve({
          success: false,
          error: `Failed to run Python: ${err.message}`,
        });
      });
    });
  }

  async runPythonScriptWithStreaming(scriptPath, args = [], event = null) {
    return new Promise((resolve, reject) => {
      let finished = false;
      let output = "";
      let error = "";

      // Costruisci il path delle DLL di vips
      const isWindows = process.platform === "win32";
      let vipsBinDir = null;
      if (isWindows) {
        // In produzione: cerca in app.asar.unpacked
        let baseDir;
        if (app.isPackaged) {
          baseDir = path.join(
            process.resourcesPath,
            "app.asar.unpacked",
            "src",
            "python-embed",
            "vips-bin",
            "vips-dev-8.17",
            "bin",
          );
        } else {
          // In sviluppo: path relativo al progetto
          baseDir = path.join(
            __dirname,
            "..",
            "..",
            "python-embed",
            "vips-bin",
            "vips-dev-8.17",
            "bin",
          );
        }
        vipsBinDir = baseDir;
      }

      // Prepara l'env per il processo Python
      const env = { ...process.env };
      if (isWindows && vipsBinDir) {
        env.PATH = vipsBinDir + ";" + env.PATH;
      }

      let py;
      try {
        py = spawn(this.pythonExecutable, ["-u", scriptPath, ...args], {
          env,
          stdio: ["inherit", "pipe", "pipe"], // Unbuffered stdio
          windowsHide: true  // Hide console window on Windows
        });
        this.activeProcess = py; // Track the active process
      } catch (spawnErr) {
        return resolve({
          success: false,
          error: `Failed to start Python: ${spawnErr.message}`,
        });
      }

      // Stream stdout data in real-time
      py.stdout.on("data", (data) => {
        const chunk = data.toString();
        output += chunk;

        // Split by lines and send each line immediately
        const lines = chunk.split("\n");
        lines.forEach((line) => {
          if (line.trim() && event && event.sender) {
            // Send each non-empty line immediately
            setImmediate(() => {
              event.sender.send("python:output", {
                type: "stdout",
                data: line + "\n",
              });
            });
          }
        });
      });

      // Stream stderr data in real-time
      py.stderr.on("data", (data) => {
        const chunk = data.toString();
        error += chunk;
        // Send real-time error to frontend if event is available
        if (event && event.sender) {
          event.sender.send("python:output", { type: "stderr", data: chunk });
        }
      });

      py.on("close", (code) => {
        if (finished) return;
        finished = true;
        this.activeProcess = null; // Clear on exit

        // Send completion signal to frontend
        if (event && event.sender) {
          event.sender.send("python:output", {
            type: "complete",
            success: code === 0,
            code: code,
          });
        }

        if (code === 0) {
          resolve({ success: true, output });
        } else {
          resolve({
            success: false,
            error: error || output || `Python exited with code ${code}`,
          });
        }
      });

      py.on("error", (err) => {
        if (finished) return;
        finished = true;
        this.activeProcess = null;

        // Send error signal to frontend
        if (event && event.sender) {
          event.sender.send("python:output", {
            type: "error",
            data: err.message,
          });
        }

        resolve({
          success: false,
          error: `Failed to run Python: ${err.message}`,
        });
      });
    });
  }

  stopPythonProcess() {
    if (this.activeProcess) {
      this.activeProcess.kill("SIGTERM");
      this.activeProcess = null;
      this.logger.info("Python process stopped by user.");
      return true;
    }
    return false;
  }

  killActiveProcess() {
    if (this.activeProcess) {
      this.activeProcess.kill("SIGTERM");
      this.activeProcess = null;
    }
  }

  getStatus() {
    return {
      ready:
        this.status.pythonInstalled &&
        this.status.venvExists &&
        this.status.dependenciesInstalled,
      ...this.status,
    };
  }

  async installEnvironment(progressCallback) {
    try {
      await this.initialize(progressCallback);
      return { success: true, message: "Python environment ready" };
    } catch (error) {
      if (progressCallback) {
        progressCallback({
          step: "error",
          message: "Errore durante l'installazione dell'ambiente Python",
          logs: error.message,
        });
      }
      return { success: false, error: error.message };
    }
  }
}
