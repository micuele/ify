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

function loadOutputImage(imageKey) {
  const filename = imageKey.padStart(2, '0');
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
  outputImage.alt = `Vibe ${filename}: ${resultTitle.textContent}`;
  outputImage.src = `/output-images/${filename}.${outputExtensions[0]}`;
}

function showVibeResult(provider, username, output) {
  accessView.classList.add('hidden');
  resultView.classList.remove('hidden');
  resultLabel.textContent = `Your ${provider === 'lastfm' ? 'Last.fm' : 'Letterboxd'} vibe:`;
  letterboxdOutput.classList.remove('hidden');
  resultTitle.classList.remove('hidden');
  resultMeta.classList.remove('hidden');
  tryAgainButton.classList.remove('hidden');
  resultTitle.textContent = output.label;
  const evidence = output.evidence?.length ? ` Matched: ${output.evidence.join(', ')}.` : '';
  resultMeta.textContent = `${output.description}${evidence}`;
  userValue.textContent = `@${username}`;
  loadOutputImage(output.image_key);
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
  setLetterboxdStatus('Analyzing your Letterboxd films...');
  try {
    const params = new URLSearchParams({ username, limit: '24' });
    const integration = await fetchJson(`/api/integrations/letterboxd?${params}`);
    sessionStorage.setItem('ify:letterboxd', JSON.stringify(integration));
    sessionStorage.setItem('ify:letterboxd-username', integration.username);
    window.dispatchEvent(new CustomEvent('letterboxd:loaded', { detail: integration }));
    showVibeResult('letterboxd', integration.username, integration.selected_output);
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
    showVibeResult(
      'lastfm',
      result.user?.name || me.user?.name || 'unknown',
      result.selected_output,
    );
  } catch {
    const saved = sessionStorage.getItem('ify:letterboxd');
    if (saved) {
      try {
        const integration = JSON.parse(saved);
        showVibeResult('letterboxd', integration.username, integration.selected_output);
        return;
      } catch {}
    }
    setMode(false);
  }
}

lastfmLogin.href = '/auth/lastfm';
letterboxdUsername.value = sessionStorage.getItem('ify:letterboxd-username') || '';
loadState();
