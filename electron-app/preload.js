const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getDrives: () => ipcRenderer.invoke('get-drives'),
  readFolder: (path) => ipcRenderer.invoke('read-folder', path),
  onDrivesUpdated: (callback) => ipcRenderer.on('drives-updated', (event, data) => callback(data))
});