/*electron 앱 실행 파일*/

const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { getDrivesWithInfo, watchDrives, setMainWindow } = require('./driveload');

let mainWindow;

ipcMain.handle('read-folder', async (event, folderPath) => {
  try {
    const entries = fs.readdirSync(folderPath, { withFileTypes: true });

    return entries.map(entry => {
      return {
        name: entry.name,
        path: path.join(folderPath, entry.name),
        isDirectory: entry.isDirectory(),
        isE01: !entry.isDirectory() && entry.name.toLowerCase().endsWith('.e01')
      };
    });
  } catch (err) {
    console.error('Failed to read folder:', folderPath, err);
    return [];
  }
});

app.whenReady().then(() => {
  mainWindow = new BrowserWindow({
    width: 1160,
    height: 750,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    }
  });

  mainWindow.loadFile('index.html');
  
  setMainWindow(mainWindow);
  watchDrives();
});

ipcMain.handle('get-drives', getDrivesWithInfo);