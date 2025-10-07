import { ipcMain, BrowserWindow, dialog } from 'electron';
import fs from 'fs';
import path from 'path';

export function setupIPC(managers) {
    const { pythonManager, projectManager, windowManager, logger } = managers;
    console.log('Configurazione IPC handlers...');


    ipcMain.handle('projects:getIconData', (event, projectId) => {
      const project = managers.projectManager.getProject(projectId);
      if (!project || !project.config.icon) return null;
    
      const iconPath = path.join(project.path, project.config.icon);
      if (!fs.existsSync(iconPath)) return null;
    
      const ext = path.extname(iconPath).slice(1); // svg, png, etc
      const mime = ext === 'svg' ? 'image/svg+xml' : `image/${ext}`;
      const base64 = fs.readFileSync(iconPath).toString('base64');
      return `data:${mime};base64,${base64}`;
    });

    ipcMain.handle('app:getStatus', () => {
      console.log('IPC: app:getStatus chiamato');
      return {
        isReady: pythonManager.getStatus(),
      };
    });

    ipcMain.handle('python:install', async () => {
      console.log('IPC: python:install chiamato');
      return await pythonManager.installEnvironment();
    });

    ipcMain.handle('python:stop', async () => {
      console.log('IPC: python:stop chiamato');
      return pythonManager.stopPythonProcess();
    });

    ipcMain.handle('projects:getAll', async () => {
      console.log('IPC: projects:getAll chiamato');
      await projectManager.loadProjects();
      return projectManager.getProjects();
    });

    ipcMain.handle('projects:open', async (event, projectId) => {
      console.log('IPC: projects:open chiamato con:', projectId);
      try {
        const project = projectManager.getProject(projectId);
        if (!project) {
          return { success: false, error: 'Project not found' };
        }

        const mainHtmlPath = projectManager.getProjectMainHtml(projectId);
        if (!mainHtmlPath) {
          return { success: false, error: 'Project main HTML not found' };
        }

        console.log('Opening project window with HTML:', mainHtmlPath);
        const projectWindow = windowManager.createProjectWindow(mainHtmlPath);

        return { success: true };
      } catch (error) {
        console.error('Errore apertura progetto:', error);
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('projects:runScript', async (event, projectId, scriptName, args = []) => {
      console.log('IPC: projects:runScript chiamato con:', projectId, scriptName, args);
      console.log('Python executable path:', pythonManager.pythonExecutable);
      try {
        const scriptPath = projectManager.getProjectPythonScript(projectId, scriptName);
        if (!scriptPath) {
          return { success: false, error: 'Script not found' };
        }

        return await pythonManager.runPythonScript(scriptPath, args);
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // New streaming version of runScript
    ipcMain.handle('projects:runScriptStreaming', async (event, projectId, scriptName, args = []) => {
      console.log('IPC: projects:runScriptStreaming chiamato con:', projectId, scriptName, args);
      try {
        const scriptPath = projectManager.getProjectPythonScript(projectId, scriptName);
        if (!scriptPath) {
          return { success: false, error: 'Script not found' };
        }

        // Use the new streaming method that passes the event for real-time updates
        return await pythonManager.runPythonScriptWithStreaming(scriptPath, args, event);
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('projects:loadContent', async (event, projectId) => {
      console.log('IPC: projects:loadContent chiamato con:', projectId);
      try {
        const project = projectManager.getProject(projectId);
        if (!project) {
          return { success: false, error: 'Project not found' };
        }

        const mainHtmlPath = projectManager.getProjectMainHtml(projectId);
        if (!mainHtmlPath) {
          return { success: false, error: 'Project main HTML not found' };
        }

        const content = fs.readFileSync(mainHtmlPath, 'utf8');

        return { success: true, html: content };
      } catch (error) {
        console.error('Errore caricamento contenuto progetto:', error);
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('dialog:selectDirectory', async (event) => {
      const win = BrowserWindow.fromWebContents(event.sender);
      const result = await dialog.showOpenDialog(win, {
        properties: ['openDirectory'],
      });
      if (result.canceled || !result.filePaths.length) return null;
      return result.filePaths[0];
    });

    ipcMain.handle('files:listFiles', async (event, directory) => {
      try {
        if (!fs.existsSync(directory)) return [];
        const files = fs.readdirSync(directory)
          .filter(f => !fs.statSync(path.join(directory, f)).isDirectory());
        return files; // Return just filenames, not full paths
      } catch (e) {
        return [];
      }
    });

    ipcMain.handle('files:readImageAsDataUrl', async (event, filePath) => {
      try {
        if (!fs.existsSync(filePath)) return null;
        const ext = path.extname(filePath).slice(1);
        const mime = `image/${ext}`;
        const base64 = fs.readFileSync(filePath).toString('base64');
        return `data:${mime};base64,${base64}`;
      } catch (e) {
        return null;
      }
    });

    ipcMain.handle('files:listThumbs', async (event, thumbsDir) => {
      try {
        const dir = thumbsDir || path.join(process.cwd(), 'output', 'thumbs');
        if (!fs.existsSync(dir)) return [];
        const files = fs.readdirSync(dir)
          .filter(f => f.toLowerCase().endsWith('.jpg'))
          .map(f => path.join(dir, f).replace(/\\/g, '/'));
        return files;
      } catch (e) {
        return [];
      }
    });

    ipcMain.handle('files:listQualityFiles', async (event, qualityDir) => {
      try {
        if (!fs.existsSync(qualityDir)) return [];
        return fs.readdirSync(qualityDir)
          .filter(f => f.toLowerCase().endsWith('.json'))
          .map(f => path.join(qualityDir, f).replace(/\\/g, '/'));
      } catch (e) {
        return [];
      }
    });

    ipcMain.handle('files:readFile', async (event, filePath) => {
      try {
        return fs.readFileSync(filePath, 'utf8');
      } catch (e) {
        return '';
      }
    });

    ipcMain.handle('files:writeFile', async (event, filePath, content) => {
      try {
        fs.writeFileSync(filePath, content, 'utf8');
        return true;
      } catch (e) {
        return false;
      }
    });

    ipcMain.on('log:fromRenderer', (event, msg) => {
      logger.info('Log from renderer:', msg);
    });

    // Pipeline-specific IPC handlers
    ipcMain.handle('pipeline:validate', async (event, pipelineConfig) => {
      console.log('IPC: pipeline:validate chiamato');
      try {
        const validation = projectManager.validatePipelineConfig(pipelineConfig);
        return validation;
      } catch (error) {
        return { valid: false, error: error.message };
      }
    });

    ipcMain.handle('pipeline:run', async (event, pipelineConfig) => {
      console.log('IPC: pipeline:run chiamato con:', pipelineConfig);
      try {
        // Validate pipeline configuration
        const validation = projectManager.validatePipelineConfig(pipelineConfig);
        if (!validation.valid) {
          return { success: false, error: validation.error };
        }

        // Get pipeline script path
        const scriptPath = projectManager.getProjectPythonScript('pipeline', 'pipeline_orchestrator.py');
        if (!scriptPath) {
          return { success: false, error: 'Pipeline orchestrator script not found' };
        }

        // Execute pipeline
        return await pythonManager.runPythonScript(scriptPath, [JSON.stringify(pipelineConfig)]);
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('pipeline:runStreaming', async (event, pipelineConfig) => {
      console.log('IPC: pipeline:runStreaming chiamato');
      try {
        // Validate pipeline configuration
        const validation = projectManager.validatePipelineConfig(pipelineConfig);
        if (!validation.valid) {
          return { success: false, error: validation.error };
        }

        // Get pipeline script path
        const scriptPath = projectManager.getProjectPythonScript('pipeline', 'pipeline_orchestrator.py');
        if (!scriptPath) {
          return { success: false, error: 'Pipeline orchestrator script not found' };
        }

        // Execute pipeline with streaming
        return await pythonManager.runPythonScriptWithStreaming(scriptPath, [JSON.stringify(pipelineConfig)], event);
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    console.log('IPC handlers configurati');
}