const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    runProjectScript: (projectId, scriptName, args) => {
        console.log('Chiamata runProjectScript dal preload:', projectId, scriptName, args);
        return ipcRenderer.invoke('projects:runScript', projectId, scriptName, args);
    },
    
    saveImageToTemp: (file) => {
        console.log('Chiamata saveImageToTemp dal preload');
        return ipcRenderer.invoke('file:saveImageToTemp', file);
    },
    
    loadImageAsBase64: (imagePath) => {
        console.log('Chiamata loadImageAsBase64 dal preload:', imagePath);
        return ipcRenderer.invoke('file:loadImageAsBase64', imagePath);
    },
    
    goBackToMain: () => {
        console.log('Chiamata goBackToMain dal preload');
        window.close();
    },
    
    selectDirectory: () => {
        return ipcRenderer.invoke('dialog:selectDirectory');
    },
    
    logToMain: (msg) => {
        ipcRenderer.send('log:fromProject1', msg);
    },
    
    listThumbs: (thumbsDir) => {
        console.log('Chiamata listThumbs dal preload:', thumbsDir);
        return ipcRenderer.invoke('project1:listThumbs', thumbsDir);
    }
});

console.log('Project preload script caricato');
