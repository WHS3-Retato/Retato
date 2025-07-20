const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getDrives: () => ipcRenderer.invoke('get-drives'),
  readFolder: (path) => ipcRenderer.invoke('read-folder', path),
  sendFilePath: (path) => ipcRenderer.send('file-selected', path),

  onDrivesUpdated: (callback) => {
    const listener = (_event, data) => callback(data);
    ipcRenderer.on('drives-updated', listener);
    return () => ipcRenderer.removeListener('drives-updated', listener);
  },

  selectFolder: () => ipcRenderer.invoke('dialog:openDirectory'),
});
