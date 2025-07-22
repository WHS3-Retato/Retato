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

  // E01 파일 선택 다이얼로그
  openE01File: () => ipcRenderer.invoke('dialog:openE01File'),

  // Recovery 시작 요청
  startRecovery: (e01Path) => ipcRenderer.invoke('start-recovery', e01Path),

  // 진행률 이벤트 핸들러 등록
  onProgress: (callback) => {
    const listener = (_event, data) => callback(data);
    ipcRenderer.on('recovery-progress', listener);
    return () => ipcRenderer.removeListener('recovery-progress', listener);
  },

  // 완료 이벤트 핸들러 등록
  onDone: (callback) => {
    const listener = () => callback();
    ipcRenderer.on('recovery-done', listener);
    return () => ipcRenderer.removeListener('recovery-done', listener);
  },

  onResults: (callback) => {
    const listener = (_e, data) => callback(data);
    ipcRenderer.on('recovery-results', listener);
    return () => ipcRenderer.removeListener('results', listener);
  },
});
