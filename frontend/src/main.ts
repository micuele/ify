import { getLetterboxdFilms } from './integrations';

const API_BASE = '';

const accessView = document.querySelector<HTMLElement>('#accessView')!;
const resultView = document.querySelector<HTMLElement>('#resultView')!;
const lastfmLogin = document.querySelector<HTMLAnchorElement>('#lastfmLogin')!;
const letterboxdToggle = document.querySelector<HTMLButtonElement>('#letterboxdToggle')!;
const letterboxdForm = document.querySelector<HTMLFormElement>('#letterboxdForm')!;
const letterboxdUsername = document.querySelector<HTMLInputElement>('#letterboxdUsername')!;
const letterboxdSubmit = document.querySelector<HTMLButtonElement>('#letterboxdSubmit')!;
const letterboxdStatus = document.querySelector<HTMLElement>('#letterboxdStatus')!;
const resultLabel = document.querySelector<HTMLElement>('#resultLabel')!;
const letterboxdOutput = document.querySelector<HTMLElement>('#letterboxdOutput')!;
const outputImage = document.querySelector<HTMLImageElement>('#outputImage')!;
const outputPlaceholder = document.querySelector<HTMLElement>('#outputPlaceholder')!;
const emojiValue = document.querySelector<HTMLElement>('#emojiValue')!;
const resultTitle = document.querySelector<HTMLElement>('#resultTitle')!;
const resultMeta = document.querySelector<HTMLElement>('#resultMeta')!;
const userValue = document.querySelector<HTMLElement>('#userValue')!;
const tryAgainButton = document.querySelector<HTMLButtonElement>('#tryAgainButton')!;

const OUTPUT_EXTENSIONS = ['png', 'webp', 'jpg', 'jpeg'];

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

function randomOutputSlot() {
  const value = new Uint32Array(1);
  crypto.getRandomValues(value);
  return (value[0] % 24) + 1;
}

function loadOutputImage(slot: number) {
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
    if (extensionIndex < OUTPUT_EXTENSIONS.length) {
      outputImage.src = `/output-images/${filename}.${OUTPUT_EXTENSIONS[extensionIndex]}`;
    }
  };
  outputImage.alt = `Output ${filename}`;
  outputImage.src = `/output-images/${filename}.${OUTPUT_EXTENSIONS[0]}`;
}

function showLetterboxdResult(
  integration: Awaited<ReturnType<typeof getLetterboxdFilms>>,
  slot: number,
) {
  const selected = integration.slots[slot - 1]?.data;
  const movie = selected?.tmdb.movie;

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
    const integration = await getLetterboxdFilms(username);
    sessionStorage.setItem('ify:letterboxd', JSON.stringify(integration));
    sessionStorage.setItem('ify:letterboxd-username', integration.username);
    const outputSlot = randomOutputSlot();
    sessionStorage.setItem('ify:letterboxd-output', String(outputSlot));
    window.dispatchEvent(new CustomEvent('letterboxd:loaded', {
      detail: integration,
    }));
    showLetterboxdResult(integration, outputSlot);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Could not load Letterboxd';
    setLetterboxdStatus(message, 'error');
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
