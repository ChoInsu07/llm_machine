let editor;
let currentFilePath = null;
let fileContents = new Map();

function onFileCreated(filePath) {
  explorer.addFile(filePath);
  loadFileInEditor(filePath);
}

const chat = new ChatPanel(onFileCreated);
const explorer = new FileExplorer((path) => loadFileInEditor(path));
const diff = new DiffViewer();

// ─── Tab switching ───
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    if (btn.dataset.tab === 'files') explorer.render();
    if (btn.dataset.tab === 'diff') diff.refresh();
  });
});

// ─── Monaco Editor ───
function initEditor() {
  return new Promise((resolve, reject) => {
    if (typeof require === 'undefined') {
      reject(new Error('Monaco Editor failed to load (require not found). Check internet connection.'));
      return;
    }
    require.config({ paths: { vs: MONACO_CDN } });
    require(['vs/editor/editor.main'], (monaco) => {
      monaco.editor.defineTheme('llm-dark', {
        base: 'vs-dark', inherit: true, rules: [],
        colors: {
          'editor.background': '#1e1e1e',
          'editor.foreground': '#d4d4d4',
          'editor.lineHighlightBackground': '#2a2a2a',
          'editor.selectionBackground': '#264f78',
          'editorCursor.foreground': '#0078d4',
        },
      });
      editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: '# Ask the AI in the chat panel to create code!\n\n// Files created by the AI will appear here',
        language: 'python',
        theme: 'llm-dark',
        fontSize: 14,
        fontFamily: "'SF Mono', Monaco, 'Cascadia Code', monospace",
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 2,
        wordWrap: 'on',
      });
      window.editorInstance = editor;
      window.monaco = monaco;
      resolve(monaco);
    }, reject);
  });
}

function updateEditorLang(filePath) {
  if (!window.monaco || !editor) return;
  const ext = filePath.split('.').pop().toLowerCase();
  const map = {
    py: 'python', js: 'javascript', ts: 'typescript', jsx: 'javascriptreact',
    tsx: 'typescriptreact', html: 'html', css: 'css', json: 'json',
    md: 'markdown', yaml: 'yaml', yml: 'yaml', xml: 'xml',
    sh: 'shell', bash: 'shell', c: 'c', cpp: 'cpp', h: 'c',
    java: 'java', go: 'go', rs: 'rust', rb: 'ruby', php: 'php', sql: 'sql',
  };
  window.monaco.editor.setModelLanguage(editor.getModel(), map[ext] || 'plaintext');
}

// ─── File loading ───
async function loadFileInEditor(filePath) {
  currentFilePath = filePath;

  if (fileContents.has(filePath)) {
    editor.setValue(fileContents.get(filePath));
  } else {
    try {
      const res = await window.api.readFile(filePath);
      if (res.success) {
        const idx = res.output.indexOf('\n');
        const content = idx !== -1 ? res.output.substring(idx + 1) : '';
        fileContents.set(filePath, content);
        editor.setValue(content);
      } else {
        editor.setValue(`// ${res.error}`);
      }
    } catch (err) {
      editor.setValue(`// Error: ${err.message}`);
    }
  }

  document.getElementById('editor-filename').textContent = filePath;
  updateEditorLang(filePath);
}

// ─── Save ───
document.getElementById('editor-save').addEventListener('click', async () => {
  if (!currentFilePath) return;
  const content = editor.getValue();
  try {
    const res = await window.api.writeFile(currentFilePath, content);
    if (res.success) {
      fileContents.set(currentFilePath, content);
      chat.addToolMessage(`Saved ${currentFilePath}`);
    } else {
      chat.addMessage('error', `Save failed: ${res.error}`);
    }
  } catch (err) {
    chat.addMessage('error', `Save error: ${err.message}`);
  }
});

document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault();
    document.getElementById('editor-save').click();
  }
});

// ─── Model management ───
async function refreshModelList() {
  const select = document.getElementById('setting-model');
  try {
    const data = await window.api.listModels();
    select.innerHTML = '';
    if (data.models && data.models.length > 0) {
      for (const m of data.models) {
        const opt = document.createElement('option');
        opt.value = m.name;
        const toolIcon = m.supports_tools ? '🛠' : '📝';
        const sizeStr = m.size ? ` (${(m.size / 1e9).toFixed(1)}GB)` : '';
        opt.textContent = `${toolIcon} ${m.name}${sizeStr}`;
        if (m.selected) opt.selected = true;
        select.appendChild(opt);
      }
    } else {
      const opt = document.createElement('option');
      opt.textContent = data.error || 'No models found';
      opt.disabled = true;
      select.appendChild(opt);
    }
  } catch (err) {
    select.innerHTML = `<option disabled>Error: ${err.message}</option>`;
  }
}

// ─── Settings ───
document.getElementById('settings-btn').addEventListener('click', async () => {
  const cfg = await window.api.getConfig();
  document.getElementById('setting-host').value = cfg.ollama_host || 'http://localhost:11434';
  document.getElementById('setting-workspace').value = cfg.workspace_dir || '.';
  await refreshModelList();
  document.getElementById('settings-modal').classList.add('active');
});

document.getElementById('settings-close').addEventListener('click', () => {
  document.getElementById('settings-modal').classList.remove('active');
});

document.getElementById('settings-save').addEventListener('click', async () => {
  const select = document.getElementById('setting-model');
  const model = select.options[select.selectedIndex]?.value || '';
  await window.api.setConfig({
    model: model,
    ollama_host: document.getElementById('setting-host').value,
    workspace_dir: document.getElementById('setting-workspace').value,
  });
  document.getElementById('settings-modal').classList.remove('active');
  chat.addToolMessage(`Model set to: ${model}`);
});

document.getElementById('model-refresh-btn').addEventListener('click', refreshModelList);

document.getElementById('model-pull-btn').addEventListener('click', async () => {
  const input = document.getElementById('model-pull-input');
  const status = document.getElementById('model-pull-status');
  const name = input.value.trim();
  if (!name) return;

  status.textContent = `Pulling ${name}...`;
  document.getElementById('model-pull-btn').disabled = true;

  try {
    const res = await fetch(`http://localhost:5001/api/models/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      const lines = text.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const d = JSON.parse(line.slice(6));
            if (d.status) status.textContent = d.status;
            if (d.error) status.textContent = `Error: ${d.error}`;
          } catch {}
        }
      }
    }

    status.textContent = 'Done!';
    input.value = '';
    await refreshModelList();
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
  } finally {
    document.getElementById('model-pull-btn').disabled = false;
  }
});

// ─── Init ───
(async function init() {
  try {
    await initEditor();
  } catch (err) {
    document.getElementById('editor-container').innerHTML =
      `<div style="padding:20px;color:#f44747;font-family:sans-serif;"><h3>${err.message}</h3></div>`;
  }

  try {
    const health = await window.api.health();
    if (!health.ollama) {
      chat.addMessage('error', 'Ollama not running. Start: ollama serve');
    } else {
      chat.addToolMessage(`Connected: ${health.model}`);
    }
  } catch {
    chat.addMessage('error', 'Backend not running. Start: python backend/server.py');
  }
})();
