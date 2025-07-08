const path = require('path');
const drivelist = require('drivelist');
const checkDiskSpace = require('check-disk-space').default;

let mainWindow;
let lastDriveSnapshot = '';

function setMainWindow(win) {
  mainWindow = win;
}

async function getDrivesWithInfo() {
  const drives = await drivelist.list();
  const categorized = { internal: [], external: [], portable: [] };

  for (const d of drives) {
    const mount = d.mountpoints[0]?.path || '';
    if (!mount) continue;

    try {
      const { free, size } = await checkDiskSpace(mount);

      let volumeLabel = '';
      if (process.platform === 'win32') {
        const driveLetter = mount.replace(/\\$/, '');
        volumeLabel = `${driveLetter} 드라이브`;
        
      } else if (process.platform === 'darwin' || process.platform === 'linux') {
        const name = path.basename(mount); // /Volumes/USB → USB
        volumeLabel = `${name} 드라이브`;
      }

      const usage = {
        mount,
        free,
        size,
        label: volumeLabel || d.description
      };

      if (d.isSystem) {
        categorized.internal.push(usage);
      } else if (d.busType === 'USB') {
        categorized.portable.push(usage);
      } else {
        categorized.external.push(usage);
      }
    } catch (err) {
      console.warn(`Failed to read drive ${mount}`, err.message);
    }
  }

  return categorized;
}

function watchDrives() {
  setInterval(async () => {
    const drives = await drivelist.list();
    const snapshot = JSON.stringify(drives.map(d => d.device + d.mountpoints[0]?.path));

    if (snapshot !== lastDriveSnapshot) {
      lastDriveSnapshot = snapshot;
      const categorized = await getDrivesWithInfo();
      mainWindow?.webContents.send('drives-updated', categorized);
    }
  }, 1000); // 2초마다 체크
}

module.exports = { getDrivesWithInfo, watchDrives, setMainWindow };