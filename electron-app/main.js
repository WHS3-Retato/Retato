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
   try {
    const files = fs.readdirSync(folderPath);

    const result = files.map(name => {
      const fullPath = path.join(folderPath, name);
      let stat;

      try {
        stat = fs.statSync(fullPath);
      } catch (err) {
        // 접근 불가 파일은 건너뜀
        return null;
      }

      return {
        name,
        path: fullPath,
        isDirectory: stat.isDirectory(),
        isE01: name.toLowerCase().endsWith('.e01'),
        size: stat.size,
      };
    }).filter(Boolean); // null 제거

    return result;
  } catch (err) {
    console.error('Error reading folder:', err);
    throw err;
  }
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