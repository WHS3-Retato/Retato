const path = require('path');
const drivelist = require('drivelist');
const checkDiskSpace = require('check-disk-space').default;

let mainWindow;
let lastDriveSnapshot = '';
let driveWatcher = null; // 7월 10일 수정

function setMainWindow(win) {
  mainWindow = win;
}

function getVolumeLabel(mount) {
  if (process.platform === 'win32') {
    return `${mount.replace(/\\$/, '')} 드라이브`;
  }
  return `${path.basename(mount)} 드라이브`;
}

async function getDrivesWithInfo() {
  const drives = await drivelist.list();
  const categorized = { internal: [], external: [], portable: [] };

   for (const d of drives) {
    for (const mp of d.mountpoints) {
      const mount = mp.path;
      if (!mount) continue;

      try {
        const { free, size } = await checkDiskSpace(mount);
        const label = getVolumeLabel(mount);

        const driveInfo = { mount, free, size, label };

        const type = d.isSystem
          ? 'internal'
          : d.busType === 'USB'
          ? 'portable'
          : 'external';

        categorized[type].push(driveInfo);
      } catch (err) {
        console.warn(`Failed to read drive ${mount}:`, err.message);
        return null;
      }
    }
  }
  return categorized;
}
/*
function watchDrives() {
  driveWatcher = setInterval(async () => {
    const drives = await drivelist.list();
    const snapshot = JSON.stringify(drives.map(d => d.device + d.mountpoints[0]?.path));

    /*
    if (snapshot !== lastDriveSnapshot) {
      lastDriveSnapshot = snapshot;
      const categorized = await getDrivesWithInfo();
      mainWindow?.webContents.send('drives-updated', categorized);
    }
  }, 1000); // 2초마다 체크
  */
/*
    const categorized = await getDrivesWithInfo();
    if (mainWindow?.webContents) {
      mainWindow?.webContents.send('drives-updated', categorized);
    }
  }, 1000);
}
*/

function watchDrives() {
  driveWatcher = setInterval(async () => {
    try {
      const drives = await drivelist.list();
      const snapshot = JSON.stringify(drives.map(d => d.device + d.mountpoints[0]?.path));

      if (snapshot !== lastDriveSnapshot) {
        lastDriveSnapshot = snapshot;
        const categorized = await getDrivesWithInfo();

        if (
          mainWindow &&
          !mainWindow.isDestroyed() &&
          mainWindow.webContents &&
          !mainWindow.webContents.isDestroyed()
        ) {
          mainWindow.webContents.send('drives-updated', categorized);
        }
      }
    } catch (err) {
      console.error('Drive watch error:', err.message);
    }
  }, 1000);
}

function stopWatchDrives() {
  if (driveWatcher) {
    clearInterval(driveWatcher);
    driveWatcher = null;
  }
}

module.exports = { getDrivesWithInfo, watchDrives, stopWatchDrives, setMainWindow };