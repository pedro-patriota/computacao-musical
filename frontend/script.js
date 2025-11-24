function getApiBase() {
  const saved = localStorage.getItem('apiBase');
  if (saved && saved.trim()) return saved.trim();
  // Default to localhost:8000 if served via file:// or other host
  return 'http://localhost:8000';
}

function setApiBase(url) {
  localStorage.setItem('apiBase', url);
}

function statusEl() { return document.getElementById('status'); }
function textEl() { return document.getElementById('syncedText'); }
function jsonEl() { return document.getElementById('syncedJson'); }

function renderSynced(data) {
  if (!Array.isArray(data)) {
    textEl().textContent = '';
    jsonEl().textContent = '';
    statusEl().textContent = 'No data returned';
    return;
  }
  const joined = data.map(x => x.word).join(' ');
  textEl().textContent = joined;
  jsonEl().textContent = JSON.stringify(data, null, 2);
}

async function loadDemo() {
  const base = getApiBase();
  statusEl().textContent = `Loading demo from ${base} ...`;
  try {
    const res = await fetch(`${base}/demo-sync`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    renderSynced(body.synced_data);
    statusEl().textContent = 'Demo loaded';
  } catch (e) {
    statusEl().textContent = `Error: ${e.message}`;
  }
}

async function uploadAndSync(ev) {
  ev.preventDefault();
  const base = getApiBase();
  const form = document.getElementById('syncForm');
  const fd = new FormData(form);
  statusEl().textContent = `Syncing via ${base} ...`;
  try {
    const res = await fetch(`${base}/sync`, { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const body = await res.json();
    renderSynced(body.synced_data);
    statusEl().textContent = 'Synced successfully';
  } catch (e) {
    statusEl().textContent = `Error: ${e.message}`;
  }
}

function initSettings() {
  const input = document.getElementById('apiBase');
  const saveBtn = document.getElementById('saveApiBase');
  input.value = getApiBase();
  saveBtn.addEventListener('click', () => {
    const url = input.value.trim();
    if (!url) return;
    setApiBase(url);
    statusEl().textContent = `Saved backend URL: ${url}`;
  });
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('demoBtn').addEventListener('click', loadDemo);
  document.getElementById('syncForm').addEventListener('submit', uploadAndSync);
  initSettings();
});
