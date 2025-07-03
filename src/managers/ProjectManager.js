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
          
          this.projects.set(projectDir, {
            id: projectDir,
            path: projectPath,
            config: config
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
}

