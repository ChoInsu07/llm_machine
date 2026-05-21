const { contextBridge } = require('electron');

const BACKEND_URL = 'http://localhost:5001';

contextBridge.exposeInMainWorld('api', {
  backendUrl: BACKEND_URL,

  async health() {
    const res = await fetch(`${BACKEND_URL}/api/health`);
    return res.json();
  },

  async chat(message, planning = true) {
    const res = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, planning }),
    });
    return res.json();
  },

  async readFile(filePath, offset = 0, limit = 2000) {
    const res = await fetch(`${BACKEND_URL}/api/read-file`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, offset, limit }),
    });
    return res.json();
  },

  async writeFile(filePath, content) {
    const res = await fetch(`${BACKEND_URL}/api/write-file`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, content }),
    });
    return res.json();
  },

  async fileTree() {
    const res = await fetch(`${BACKEND_URL}/api/file-tree`);
    return res.json();
  },

  async getConfig() {
    const res = await fetch(`${BACKEND_URL}/api/config`);
    return res.json();
  },

  async setConfig(data) {
    const res = await fetch(`${BACKEND_URL}/api/config`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async listModels() {
    const res = await fetch(`${BACKEND_URL}/api/models`);
    return res.json();
  },

  async pullModel(name) {
    const res = await fetch(`${BACKEND_URL}/api/models/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    return res.body;
  },
});
