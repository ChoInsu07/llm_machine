class DiffViewer {
  constructor() {
    this.selectEl = document.getElementById('diff-file-select');
    this.refreshBtn = document.getElementById('diff-refresh');
    this.contentEl = document.getElementById('diff-content');

    this.refreshBtn.addEventListener('click', () => this.refresh());
  }

  async refresh() {
    this.contentEl.innerHTML = '<div class="diff-placeholder">Loading diff...</div>';

    try {
      const tree = await window.api.fileTree();
      this.populateFileList(tree);
      this.contentEl.innerHTML = '<div class="diff-placeholder">Select a file to view diff</div>';
    } catch (err) {
      this.contentEl.innerHTML = `<div class="diff-placeholder">Error: ${err.message}</div>`;
    }
  }

  populateFileList(tree, prefix = '') {
    this.selectEl.innerHTML = '<option value="">Select a file</option>';

    const addFiles = (items, path) => {
      for (const item of items) {
        const fullPath = path ? `${path}/${item.name}` : item.name;
        if (item.type === 'file') {
          const opt = document.createElement('option');
          opt.value = fullPath;
          opt.textContent = fullPath;
          this.selectEl.appendChild(opt);
        }
        if (item.children) {
          addFiles(item.children, fullPath);
        }
      }
    };

    addFiles(tree, '');
  }

  showDiff(diffText) {
    this.contentEl.innerHTML = '';

    if (!diffText || diffText === '(empty)') {
      this.contentEl.innerHTML = '<div class="diff-placeholder">No changes</div>';
      return;
    }

    const lines = diffText.split('\n');
    for (const line of lines) {
      const div = document.createElement('div');
      if (line.startsWith('+') && !line.startsWith('+++')) {
        div.className = 'diff-added';
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        div.className = 'diff-removed';
      } else if (line.startsWith('@@')) {
        div.className = 'diff-header-line';
      }
      div.textContent = line;
      this.contentEl.appendChild(div);
    }
  }
}
