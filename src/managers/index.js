import PythonManager from './PythonManager.js';
import WindowManager from './WindowManager.js';
import Logger from '../utils/Logger.js';
import ProjectManager from './ProjectManager.js';

export function initializeManagers() {
  const pythonManager = new PythonManager();
  const windowManager = new WindowManager();
  const logger = new Logger();
  const projectManager = new ProjectManager();

  return { pythonManager, windowManager, logger, projectManager };
}