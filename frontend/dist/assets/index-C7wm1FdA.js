const accessView = document.querySelector('#accessView');
const resultView = document.querySelector('#resultView');
const lastfmLogin = document.querySelector('#lastfmLogin');
const letterboxdToggle = document.querySelector('#letterboxdToggle');
const letterboxdForm = document.querySelector('#letterboxdForm');
const letterboxdUsername = document.querySelector('#letterboxdUsername');
const letterboxdSubmit = document.querySelector('#letterboxdSubmit');
const letterboxdStatus = document.querySelector('#letterboxdStatus');
const resultLabel = document.querySelector('#resultLabel');
const letterboxdOutput = document.querySelector('#letterboxdOutput');
const outputImage = document.querySelector('#outputImage');
const outputPlaceholder = document.querySelector('#outputPlaceholder');
const emojiValue = document.querySelector('#emojiValue');
const resultTitle = document.querySelector('#resultTitle');
const resultMeta = document.querySelector('#resultMeta');
const userValue = document.querySelector('#userValue');
const tryAgainButton = document.querySelector('#tryAgainButton');
const outputExtensions = ['png', 'webp', 'jpg', 'jpeg'];

async function fetchJson(path, init) {
  const response = await fetch(path, { ...init, credentials: 'include' });
  let data = null;
  try { data = await response.json(); } catch {}
  if (!response.ok) throw new Error(data?.error || `Request failed with ${response.status}`);
  return data;
}

function setLetterboxdStatus(message, type) {
  letterboxdStatus.textContent = message;
  letterboxdStatus.classList.toggle('error', type === 'error');
  letterboxdStatus.classList.toggle('success', type === 'success');
}

function randomOutputSlot() {
  const value = new Uint32Array(1);
  crypto.getRandomValues(value);
  return (value[0] % 24) + 1;
}

function loadOutputImage(slot) {
  const filename = String(slot).padStart(2, '0');
  let extensionIndex = 0;
  outputImage.classList.add('hidden');
  outputPlaceholder.classList.remove('hidden');
  outputPlaceholder.textContent = filename;
  outputImage.onload = () => {
    outputPlaceholder.classList.add('hidden');
    outputImage.classList.remove('hidden');
  };
  outputImage.onerror = () => {
    extensionIndex += 1;
    if (extensionIndex < outputExtensions.length) {
      outputImage.src = `/output-images/${filename}.${outputExtensions[extensionIndex]}`;
    }
  };
  outputImage.alt = `Output ${filename}`;
  outputImage.src = `/output-images/${filename}.${outputExtensions[0]}`;
}

function showLetterboxdResult(integration, slot) {
  const selected = integration.slots[slot - 1]?.data;
  const movie = selected?.tmdb?.movie;
  accessView.classList.add('hidden');
  resultView.classList.remove('hidden');
  resultLabel.textContent = 'Your Letterboxd result:';
  letterboxdOutput.classList.remove('hidden');
  emojiValue.classList.add('hidden');
  resultTitle.classList.remove('hidden');
  resultMeta.classList.remove('hidden');
  tryAgainButton.classList.remove('hidden');
  resultTitle.textContent = `Output ${String(slot).padStart(2, '0')}`;
  resultMeta.textContent = movie?.title || selected?.title || 'Random profile data point';
  userValue.textContent = `@${integration.username}`;
  loadOutputImage(slot);
}

letterboxdToggle.addEventListener('click', () => {
  const willOpen = letterboxdForm.classList.contains('hidden');
  letterboxdForm.classList.toggle('hidden', !willOpen);
  letterboxdToggle.setAttribute('aria-expanded', String(willOpen));
  if (willOpen) letterboxdUsername.focus();
});

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
    const outputSlot = randomOutputSlot();
    sessionStorage.setItem('ify:letterboxd', JSON.stringify(integration));
    sessionStorage.setItem('ify:letterboxd-username', integration.username);
    sessionStorage.setItem('ify:letterboxd-output', String(outputSlot));
    window.dispatchEvent(new CustomEvent('letterboxd:loaded', { detail: integration }));
    showLetterboxdResult(integration, outputSlot);
  } catch (error) {
    setLetterboxdStatus(error?.message || 'Could not load Letterboxd', 'error');
  } finally {
    letterboxdSubmit.disabled = false;
    letterboxdSubmit.textContent = 'Connect';
  }
});

tryAgainButton.addEventListener('click', () => {
  resultView.classList.add('hidden');
  accessView.classList.remove('hidden');
  letterboxdForm.classList.remove('hidden');
  letterboxdToggle.setAttribute('aria-expanded', 'true');
  letterboxdUsername.focus();
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
    const saved = sessionStorage.getItem('ify:letterboxd');
    const savedSlot = Number(sessionStorage.getItem('ify:letterboxd-output'));
    if (saved && savedSlot >= 1 && savedSlot <= 24) {
      try {
        showLetterboxdResult(JSON.parse(saved), savedSlot);
        return;
      } catch {}
    }
    setMode(false);
  }
}

lastfmLogin.href = '/auth/lastfm';
letterboxdUsername.value = sessionStorage.getItem('ify:letterboxd-username') || '';
loadState();
