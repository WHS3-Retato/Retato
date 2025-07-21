const { app, BrowserWindow, ipcMain, dialog } = require('electron'); // ✅ 한 줄에 다 합침
const path = require('path');
const { spawn } = require('child_process');
const readline = require('readline');
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
  console.log('선택된 E01 파일 경로:', filePath);
});

ipcMain.handle('start-recovery', (_event, e01FilePath) => {
  console.log('▶ start-recovery called with', e01FilePath);

  return new Promise((resolve, reject) => {
    const scriptPath = path.join(
      __dirname, 'python_engine', 'core', 'image_loader', 'e01_parser.py'
    );
    const env = { ...process.env, PYTHONPATH: __dirname };
    const python = spawn('python', [scriptPath, e01FilePath], {
      cwd: __dirname,
      shell: true,
      env,
    });

    console.log('--- Python spawned, waiting for stdout lines ---');

    const rl = readline.createInterface({ input: python.stdout });
    rl.on('line', line => {
      console.log('⭸ raw line:', line);
      try {
        const { processed, total } = JSON.parse(line);
        console.log('✔ parsed:', processed, total);
        mainWindow.webContents.send('recovery-progress', { processed, total });
      } catch (e) {
        console.log('⚠️ not JSON:', line);
      }
    });

    python.stderr.on('data', buf => {
      console.error('Python stderr:', buf.toString());
      mainWindow.webContents.send('recovery-error', buf.toString());
    });

    python.on('close', code => {
      console.log('🔚 python exited with code', code);
      rl.close();
      mainWindow.webContents.send('recovery-done');
      code === 0 ? resolve() : reject(new Error(`exit ${code}`));
    });
  });
});

ipcMain.handle('dialog:openDirectory', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']  
  });
  return result;
});

ipcMain.handle('dialog:openE01File', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'E01 파일 선택',
    filters: [{ name: 'E01 files', extensions: ['e01'] }],
    properties: ['openFile']
  });
  // 선택 취소 시 []
  return result.canceled ? null : result.filePaths[0];
});
