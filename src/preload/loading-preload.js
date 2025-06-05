const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onProgress: (callback) => {
        ipcRenderer.on('setup-progress', (event, progress) => {
            callback(progress);
        });
    },
    
    // Test method for running Python scripts
    testPythonScript: (scriptName, args) => {
        return ipcRenderer.invoke('python:runScript', scriptName, args);
    }
});
