const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const drivelist = require('drivelist');
const checkDiskSpace = require('check-disk-space').default;
const fs = require('fs').promises;
const fssync = require('fs');

let mainWindow = null;

// Classify drive type
function classifyDrive(drive) {
  if (drive.isUSB || drive.isCard || drive.isRemovable) return 'removable';
  if (drive.isSystem) return 'internal';
  return 'external';
}

// Label formatting
function makeDriveLabel(drive, mountPath) {
  const letterMatch = mountPath.match(/^([A-Z]):/i);
  if (letterMatch) {
    const letter = letterMatch[1].toUpperCase();
    return `${letter}: Drive`;
  }
  return drive.description || mountPath;
}

// Get detailed drive list
async function getDrivesWithInfo() {
  const drives = await drivelist.list();

  const mapped = await Promise.all(
    drives.flatMap((drive, driveIdx) =>
      drive.mountpoints.map(async (mp, mpIdx) => {
        const mountPath = mp.path;
        if (!mountPath) return null;

        let size = 0;
        let free = 0;
        try {
          const space = await checkDiskSpace(mountPath);
          size = space.size ?? 0;
          free = space.free ?? 0;
        } catch {
          size = 0;
          free = 0;
        }

        return {
          id: `${driveIdx}-${mpIdx}`,
          label: makeDriveLabel(drive, mountPath),
          mount: mountPath,
          size,
          free,
          kind: classifyDrive(drive),
          raw: {
            description: drive.description,
            device: drive.device,
            busType: drive.busType,
          },
        };
      })
    )
  );

  return mapped.filter(Boolean);
}

// Push drive list to renderer
function broadcastDrives() {
  if (!mainWindow) return;
  getDrivesWithInfo()
    .then((info) => {
      mainWindow.webContents.send('drives-updated', info);
    })
    .catch((err) => {
      console.error('Failed to broadcast drives:', err);
      mainWindow.webContents.send('drives-updated', []);
    });
}

// Start polling drive status
function startDrivePolling() {
  broadcastDrives(); // once on start
  setInterval(broadcastDrives, 5000); // then every 5s
}

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    resizable: false,
    fullscreenable: false,
    backgroundColor: '#ecf2f8',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'dist/index.html'));
  startDrivePolling();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// IPC: get-drives
ipcMain.handle('get-drives', async () => {
  return await getDrivesWithInfo();
});

// IPC: read-folder
ipcMain.handle('read-folder', async (_event, folderPath) => {
  try {
    const dirents = await fs.readdir(folderPath, { withFileTypes: true });
    dirents.sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));

    const items = [];
    for (const e of dirents) {
      const full = path.join(folderPath, e.name);
      let size = 0;
      if (!e.isDirectory()) {
        try {
          size = (await fs.stat(full)).size;
        } catch {
          try { size = fssync.statSync(full).size; } catch {}
        }
      }
      items.push({
        name: e.name,
        path: full,
        isDirectory: e.isDirectory(),
        isE01: e.name.toLowerCase().endsWith('.e01'),
        size,
      });
    }
    return items;
  } catch (err) {
    console.error('read-folder error:', err);
    return [];
  }
});

ipcMain.on('file-selected', (_event, filePath) => {
  console.log('📂 선택된 E01 파일 경로:', filePath);

  // TODO: 이후 분석기로 넘기거나 상태 저장, 전역 변수 할당 등 추가 가능
});