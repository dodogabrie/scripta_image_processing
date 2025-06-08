const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onSetupProgress: (callback) => ipcRenderer.on('setup-progress', (event, data) => callback(data))
});
