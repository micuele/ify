import { getLetterboxdFilms } from './integrations';

const API_BASE = '';

const accessView = document.querySelector<HTMLElement>('#accessView')!;
const resultView = document.querySelector<HTMLElement>('#resultView')!;
const lastfmLogin = document.querySelector<HTMLAnchorElement>('#lastfmLogin')!;
const letterboxdForm = document.querySelector<HTMLFormElement>('#letterboxdForm')!;
const letterboxdUsername = document.querySelector<HTMLInputElement>('#letterboxdUsername')!;
const letterboxdSubmit = document.querySelector<HTMLButtonElement>('#letterboxdSubmit')!;
const letterboxdStatus = document.querySelector<HTMLElement>('#letterboxdStatus')!;
const emojiValue = document.querySelector<HTMLElement>('#emojiValue')!;
const userValue = document.querySelector<HTMLElement>('#userValue')!;

async function fetchJson(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, { ...init, credentials: 'include' });
  let data: any = null;
  try { data = await res.json(); } catch {}
  if (!res.ok) throw new Error(data?.error || `Request failed with ${res.status}`);
  return data;
}

function setLetterboxdStatus(
  message: string,
  type?: 'error' | 'success',
) {
  letterboxdStatus.textContent = message;
  letterboxdStatus.classList.toggle('error', type === 'error');
  letterboxdStatus.classList.toggle('success', type === 'success');
}

letterboxdForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const username = letterboxdUsername.value.trim().replace(/^@/, '');
  if (!username) return;

  letterboxdSubmit.disabled = true;
  letterboxdSubmit.textContent = 'Loading...';
  setLetterboxdStatus('Loading recent films from Letterboxd...');

  try {
    const integration = await getLetterboxdFilms(username);
    sessionStorage.setItem('ify:letterboxd', JSON.stringify(integration));
    sessionStorage.setItem('ify:letterboxd-username', integration.username);
    window.dispatchEvent(new CustomEvent('letterboxd:loaded', {
      detail: integration,
    }));
    setLetterboxdStatus(
      `Loaded ${integration.film_count} films for @${integration.username}.`,
      'success',
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Could not load Letterboxd';
    setLetterboxdStatus(message, 'error');
  } finally {
    letterboxdSubmit.disabled = false;
    letterboxdSubmit.textContent = 'Connect';
  }
});

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

lastfmLogin.href = '/auth/lastfm';
letterboxdUsername.value = sessionStorage.getItem('ify:letterboxd-username') || '';
loadState();
