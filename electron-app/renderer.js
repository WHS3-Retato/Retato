function createDriveCard(drive) {
  const used = drive.size - drive.free;
  const usedPercent = Math.round((used / drive.size) * 100);

  const el = document.createElement('div');
  el.className = 'drive-card';

  el.innerHTML = `
    <div class="info">
      <div><strong>${drive.label || drive.mount}</strong></div>
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
    loadFolder(drive.mount);
  };

  return el;
}

function renderDrives(categorized) {
    document.getElementById('internal-list').innerHTML = '';
    document.getElementById('external-list').innerHTML = '';
    document.getElementById('portable-list').innerHTML = '';

    categorized.internal.forEach(d => {
        document.getElementById('internal-list').appendChild(createDriveCard(d));
    });

    categorized.external.forEach(d => {
        document.getElementById('external-list').appendChild(createDriveCard(d));
    });

    categorized.portable.forEach(d => {
        document.getElementById('portable-list').appendChild(createDriveCard(d));
    });
}

window.api.getDrives().then(renderDrives);

// 실시간 변경 감지
window.api.onDrivesUpdated((newDrives) => {
    renderDrives(newDrives);
});

const explorerDiv = document.getElementById('explorer');

async function loadFolder(folderPath) {
  const entries = await window.api.readFolder(folderPath);
  explorerDiv.innerHTML = `<h3>${folderPath}</h3>`;

  entries.forEach(entry => {
    if (entry.isDirectory || entry.isE01) {
      const item = document.createElement('div');
      item.textContent = entry.name;

      if (entry.isDirectory) {
        item.style.fontWeight = 'bold';
        item.style.cursor = 'pointer';
        item.onclick = () => loadFolder(entry.path);
      } else if (entry.isE01) {
        item.style.color = 'blue';
      }

      explorerDiv.appendChild(item);
    }
  });
}
