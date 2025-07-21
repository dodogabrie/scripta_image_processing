const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getAppStatus: () => {
        console.log('Chiamata getAppStatus dal preload');
        return ipcRenderer.invoke('app:getStatus');
    },

    testPythonScript: (scriptName, args) => {
        console.log('Chiamata testPythonScript dal preload:', scriptName, args);
        return ipcRenderer.invoke('python:runScript', scriptName, args);
    },

    installPython: () => {
        console.log('Chiamata installPython dal preload');
        return ipcRenderer.invoke('python:install');
    },

    getProjectIconData: (projectId) => {
        return ipcRenderer.invoke('projects:getIconData', projectId);
    },

    openFile: () => {
        console.log('Open file requested');
        return Promise.resolve(null);
    },
    saveFile: (data) => {
        console.log('Save file requested', data);
        return Promise.resolve();
    },

    getProjects: () => {
        console.log('Chiamata getProjects dal preload');
        return ipcRenderer.invoke('projects:getAll');
    },

    openProject: (projectId) => {
        console.log('Chiamata openProject dal preload:', projectId);
        return ipcRenderer.invoke('projects:open', projectId);
    },

    loadProjectContent: (projectId) => {
        console.log('Chiamata loadProjectContent dal preload:', projectId);
        return ipcRenderer.invoke('projects:loadContent', projectId);
    },

    runProjectScript: (projectId, scriptName, args) => {
        console.log('Chiamata runProjectScript dal preload:', projectId, scriptName, args);
        return ipcRenderer.invoke('projects:runScript', projectId, scriptName, args);
    },

    selectDirectory: () => {
        console.log('Chiamata selectDirectory dal preload');
        return ipcRenderer.invoke('dialog:selectDirectory');
    },

    // Generic file operations
    listThumbs: (thumbsDir) => {
        console.log('Chiamata listThumbs dal preload:', thumbsDir);
        return ipcRenderer.invoke('files:listThumbs', thumbsDir);
    },

    listQualityFiles: (qualityDir) => {
        console.log('Chiamata listQualityFiles dal preload:', qualityDir);
        return ipcRenderer.invoke('files:listQualityFiles', qualityDir);
    },

    readFile: (filePath) => {
        console.log('Chiamata readFile dal preload:', filePath);
        return ipcRenderer.invoke('files:readFile', filePath);
    },

    writeFile: (filePath, content) => {
        console.log('Chiamata writeFile dal preload:', filePath);
        return ipcRenderer.invoke('files:writeFile', filePath, content);
    },

    // Generic process control
    stopPythonProcess: () => {
        console.log('Chiamata stopPythonProcess dal preload');
        return ipcRenderer.invoke('python:stop');
    },

    logToMain: (msg) => {
        console.log('Chiamata logToMain dal preload:', msg);
        ipcRenderer.send('log:fromRenderer', msg);
    },
});

console.log('Main preload script caricato');
