function createDriveCard(drive) {
  const used = drive.size - drive.free;
  const usedPercent = Math.round((used / drive.size) * 100);

  const el = document.createElement('div');
  el.className = 'drive-card';

  el.innerHTML = `
    <div class="info">
      <div class="drive-title">
        <img src="icon_drive.svg" alt="드라이브 아이콘" class="drive_icon">
        <strong>${drive.label || drive.mount}</strong></div>
      <div>
      <div>${(used / (1024 ** 3)).toFixed(1)} GB / ${(drive.size / (1024 ** 3)).toFixed(1)} GB</div>
      <div class="bar">
        <div class="bar-fill" style="width: 0%;"></div>
      </div>
    </div>
  `;

  requestAnimationFrame(() => {
    const fillBar = el.querySelector('.bar-fill');
    fillBar.style.width = `${usedPercent}%`;
  });

  el.onclick = () => {
    const encodedPath = encodeURIComponent(drive.mount);
    window.location.href = `drive_folder.html?mount=${encodedPath}`;
  };

  return el;
}

const listEls = {
  internal: document.getElementById('internal-list'),
  external: document.getElementById('external-list'),
  portable: document.getElementById('portable-list')
}

function renderDrives(categorized) {
    Object.keys(listEls).forEach(key => listEls[key].innerHTML = '');

    categorized.internal.forEach(d => listEls.internal.appendChild(createDriveCard(d)));
    categorized.external.forEach(d => listEls.external.appendChild(createDriveCard(d)));
    categorized.portable.forEach(d => listEls.portable.appendChild(createDriveCard(d)));
}

window.api.getDrives().then(renderDrives);

// 실시간 변경 감지
window.api.onDrivesUpdated((newDrives) => {
    renderDrives(newDrives);
});

const explorerDiv = document.getElementById('explorer');

function createExplorerItem(entry) {
  const item = document.createElement('div');
  item.textContent = entry.name;

  if (entry.isDirectory) {
    item.style.fontWeight = 'bold';
    item.style.cursor = 'pointer';
    item.onclick = () => loadFolder(entry.path);
  } else if (entry.isE01) {
    item.style.color = 'blue';
  }

  return item;
}

async function loadFolder(folderPath) {
  const entries = await window.api.readFolder(folderPath);
  explorerDiv.innerHTML = `<h3>${folderPath}</h3>`;

  entries.forEach(entry => {
    if (entry.isDirectory || entry.isE01) {
      const item = createExplorerItem(entry);
      explorerDiv.appendChild(item);
    }
  });
}