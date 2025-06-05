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
    
    installPython: () => ipcRenderer.invoke('python:install'),
    
    // File operations (placeholder for now)
    openFile: () => {
        console.log('Open file requested');
        return Promise.resolve(null);
    },
    saveFile: (data) => {
        console.log('Save file requested', data);
        return Promise.resolve();
    }
});

console.log('Main preload script caricato');
