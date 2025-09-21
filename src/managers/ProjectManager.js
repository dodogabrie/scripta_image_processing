import fs from 'fs/promises';
import { app } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import Logger from '../utils/Logger.js';

export default class ProjectManager {
  constructor() {
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    this.logger = new Logger();
    this.projectsPath = path.join(__dirname, '..', 'projects');
    this.projects = new Map();
  }

  async loadProjects() {
    try {
      console.log('ProjectManager: Caricamento progetti da:', this.projectsPath);
      const projectDirs = await fs.readdir(this.projectsPath);
      console.log('ProjectManager: Cartelle trovate:', projectDirs);
      
      for (const projectDir of projectDirs) {
        const projectPath = path.join(this.projectsPath, projectDir);
        const configPath = path.join(projectPath, 'config.json');
        
        console.log('ProjectManager: Controllo config in:', configPath);
        
        try {
          const configData = await fs.readFile(configPath, 'utf8');
          const config = JSON.parse(configData);
          
          // Aggiunta iconUrl se esiste
          const iconUrl = config.icon
            ? `file://${path.join(projectPath, config.icon)}`
            : null;
          
          this.projects.set(projectDir, {
            id: projectDir,
            path: projectPath,
            config: config,
            iconUrl,
          });
          
          console.log('ProjectManager: Caricato progetto:', config.name);
          this.logger.info(`Loaded project: ${config.name}`);
        } catch (error) {
          console.warn('ProjectManager: Errore caricamento config per', projectDir, ':', error.message);
          this.logger.warn(`Failed to load project config for ${projectDir}: ${error.message}`);
        }
      }
      
      console.log('ProjectManager: Progetti totali caricati:', this.projects.size);
    } catch (error) {
      console.error('ProjectManager: Errore caricamento progetti:', error);
      this.logger.error('Failed to load projects:', error);
    }
  }

  getProjects() {
    return Array.from(this.projects.values());
  }

  getProject(projectId) {
    return this.projects.get(projectId);
  }

  getProjectMainHtml(projectId) {
    const project = this.getProject(projectId);
    if (!project) return null;
    
    return path.join(project.path, project.config.main);
  }

  getProjectPythonScript(projectId, scriptName) {
    const project = this.getProject(projectId);
    if (!project) return null;
    let scriptPath;
    if (app.isPackaged) {
      // In production: scripts are in the asar.unpacked directory
      scriptPath = path.join(
          process.resourcesPath,
          'app.asar.unpacked',
          'src',
          'projects',
          projectId,
          'python',
          scriptName
      );
    } else {
      // In development: use normal path
      scriptPath = path.join(project.path, 'python', scriptName);
    }
    return scriptPath;
  }

  // Pipeline-specific methods
  isPipelineProject(projectId) {
    const project = this.getProject(projectId);
    return project && project.config.type === 'pipeline';
  }

  getRegularProjects() {
    return Array.from(this.projects.values()).filter(p => p.config.type !== 'pipeline');
  }

  getPipelineProjects() {
    return Array.from(this.projects.values()).filter(p => p.config.type === 'pipeline');
  }

  validatePipelineConfig(pipelineConfig) {
    if (!pipelineConfig || typeof pipelineConfig !== 'object') {
      return { valid: false, error: 'Pipeline configuration is required' };
    }

    if (!Array.isArray(pipelineConfig.steps) || pipelineConfig.steps.length === 0) {
      return { valid: false, error: 'Pipeline must have at least one step' };
    }

    if (!pipelineConfig.inputDir || !pipelineConfig.outputDir) {
      return { valid: false, error: 'Input and output directories are required' };
    }

    // Validate each step
    for (let i = 0; i < pipelineConfig.steps.length; i++) {
      const step = pipelineConfig.steps[i];
      if (!step.projectId) {
        return { valid: false, error: `Step ${i + 1} is missing projectId` };
      }

      const project = this.getProject(step.projectId);
      if (!project) {
        return { valid: false, error: `Step ${i + 1}: Project '${step.projectId}' not found` };
      }

      if (project.config.type === 'pipeline') {
        return { valid: false, error: `Step ${i + 1}: Cannot include pipeline projects in pipeline` };
      }
    }

    return { valid: true };
  }

  generateTempDirectoryName(pipelineConfig, stepIndex) {
    const timestamp = Date.now();
    return path.join(pipelineConfig.outputDir, `pipeline_temp_step${stepIndex}_${timestamp}`);
  }
}
