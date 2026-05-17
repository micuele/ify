const API_BASE = 'http://127.0.0.1:5000';

const accessView = document.querySelector<HTMLElement>('#accessView')!;
const resultView = document.querySelector<HTMLElement>('#resultView')!;
const lastfmLogin = document.querySelector<HTMLAnchorElement>('#lastfmLogin')!;
const donateLink = document.querySelector<HTMLAnchorElement>('.donate')!;
const emojiValue = document.querySelector<HTMLElement>('#emojiValue')!;
const userValue = document.querySelector<HTMLElement>('#userValue')!;

async function fetchJson(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, { ...init, credentials: 'include' });
  let data: any = null;
  try { data = await res.json(); } catch {}
  if (!res.ok) throw new Error(data?.error || `Request failed with ${res.status}`);
  return data;
}

function setMode(loggedIn: boolean) {
  accessView.classList.toggle('hidden', loggedIn);
  resultView.classList.toggle('hidden', !loggedIn);
}

async function loadState() {
  try {
    const me = await fetchJson('/api/me');
    if (!me.authenticated) throw new Error('not logged in');
    
    const result = await fetchJson('/api/result');
    setMode(true);
    
    // Set the username profile text cleanly
    userValue.textContent = result.user?.name || me.user?.name || 'unknown';
    
    // Safely output only the dynamically scored profile emoji from the CSV backend algorithm
    emojiValue.textContent = result.selected_output?.emoji || '🎸';
  } catch {
    setMode(false);
  }
}

lastfmLogin.href = `${API_BASE}/auth/lastfm`;
loadState();