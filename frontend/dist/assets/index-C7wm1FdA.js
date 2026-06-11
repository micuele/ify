const accessView = document.querySelector('#accessView');
const resultView = document.querySelector('#resultView');
const lastfmLogin = document.querySelector('#lastfmLogin');
const letterboxdForm = document.querySelector('#letterboxdForm');
const letterboxdUsername = document.querySelector('#letterboxdUsername');
const letterboxdSubmit = document.querySelector('#letterboxdSubmit');
const letterboxdStatus = document.querySelector('#letterboxdStatus');
const emojiValue = document.querySelector('#emojiValue');
const userValue = document.querySelector('#userValue');

async function fetchJson(path, init) {
  const response = await fetch(path, { ...init, credentials: 'include' });
  let data = null;
  try { data = await response.json(); } catch {}
  if (!response.ok) {
    throw new Error(data?.error || `Request failed with ${response.status}`);
  }
  return data;
}

function setLetterboxdStatus(message, type) {
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
    const params = new URLSearchParams({ username, limit: '24' });
    const integration = await fetchJson(`/api/integrations/letterboxd?${params}`);
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
    setLetterboxdStatus(error?.message || 'Could not load Letterboxd', 'error');
  } finally {
    letterboxdSubmit.disabled = false;
    letterboxdSubmit.textContent = 'Connect';
  }
});

function setMode(loggedIn) {
  accessView.classList.toggle('hidden', loggedIn);
  resultView.classList.toggle('hidden', !loggedIn);
}

async function loadState() {
  try {
    const me = await fetchJson('/api/me');
    if (!me.authenticated) throw new Error('not logged in');
    const result = await fetchJson('/api/result');
    setMode(true);
    userValue.textContent = result.user?.name || me.user?.name || 'unknown';
    emojiValue.textContent = result.selected_output?.emoji || '🎸';
  } catch {
    setMode(false);
  }
}

lastfmLogin.href = '/auth/lastfm';
letterboxdUsername.value = sessionStorage.getItem('ify:letterboxd-username') || '';
loadState();
