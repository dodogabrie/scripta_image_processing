import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
    onSetupProgress: (callback) => ipcRenderer.on('setup-progress', (event, data) => callback(data))
});
