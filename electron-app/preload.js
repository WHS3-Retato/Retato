const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getDrives: () => ipcRenderer.invoke('get-drives'),
  readFolder: (path) => ipcRenderer.invoke('read-folder', path),
  onDrivesUpdated: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('drives-updated', handler);

    return () => ipcRenderer.removeListener('drives-updated', handler);
  }
});