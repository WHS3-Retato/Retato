/*electron 앱 실행 파일*/

const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { getDrivesWithInfo, watchDrives, setMainWindow } = require('./driveManager');

function readFolder(folderPath) {
  try {
    const entries = fs.readdirSync(folderPath, { withFileTypes: true });

    return entries.map(entry => ({
      name: entry.name,
      path: path.join(folderPath, entry.name),
      isDirectory: entry.isDirectory(),
      isE01: !entry.isDirectory() && entry.name.toLowerCase().endsWith('.e01')
    }));
  } catch (err) {
    console.error(`[read-folder] Failed to read: ${folderPath}`, err.message);
    return [];
  }
}

ipcMain.handle('read-folder', async (event, folderPath) => {
  const files = await fs.promises.readdir(folderPath, { withFileTypes: true });
  return files.map(file => {
    const fullPath = path.join(folderPath, file.name);
    const isE01 = path.extname(file.name).toLowerCase() === '.e01';
    const stat = fs.statSync(fullPath);

    return {
      name: file.name,
      path: fullPath,
      isDirectory: file.isDirectory(),
      isE01: isE01,
      size: isE01 ? stat.size : undefined // ✅ 이 부분이 핵심
    };
  });
});

function createMainWindow() {
  const mainWindow = new BrowserWindow({
    width: 1160,
    height: 750,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    }
  });

  mainWindow.loadFile('index.html');

  setMainWindow(mainWindow);
  watchDrives();
}

app.whenReady().then(createMainWindow);

ipcMain.handle('get-drives', getDrivesWithInfo);