const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getDrives: () => ipcRenderer.invoke('get-drives'),

  readFolder: (path) => ipcRenderer.invoke('read-folder', path),

  onDrivesUpdated: (callback) => {
    const listener = (_event, data) => callback(data);
    ipcRenderer.on('drives-updated', listener);
    return () => ipcRenderer.removeListener('drives-updated', listener);
  },

  sendFilePath: (path) => ipcRenderer.send('file-selected', path),
});