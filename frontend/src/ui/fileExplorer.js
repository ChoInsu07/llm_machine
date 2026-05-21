class FileExplorer {
  constructor(onFileSelect) {
    this.treeEl = document.getElementById('file-tree');
    this.onFileSelect = onFileSelect;
    this.files = new Map();
  }

  addFile(filePath) {
    if (!this.files.has(filePath)) {
      this.files.set(filePath, { path: filePath, name: filePath.split('/').pop() });
    }
    this.render();
  }

  addFiles(filePaths) {
    for (const fp of filePaths) this.addFile(fp);
  }

  render() {
    if (this.files.size === 0) {
      this.treeEl.innerHTML = '<div class="tree-empty">No files yet.\nAsk the AI to create something!</div>';
      return;
    }

    this.treeEl.innerHTML = '';

    const sorted = Array.from(this.files.values()).sort((a, b) => a.path.localeCompare(b.path));

    for (const file of sorted) {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'tree-item';
      itemDiv.innerHTML = `<span class="icon">📄</span>${file.path}`;
      itemDiv.addEventListener('click', () => {
        document.querySelectorAll('#file-tree .tree-item').forEach(e => e.classList.remove('active'));
        itemDiv.classList.add('active');
        if (this.onFileSelect) this.onFileSelect(file.path);
      });
      this.treeEl.appendChild(itemDiv);
    }
  }

  async refresh() {
    this.render();
  }
}
