const ANIMATION_DURATION = 1000;

const DOT_POSITIONS = {
  1: [4],
  2: [2, 6],
  3: [2, 4, 6],
  4: [0, 2, 6, 8],
  5: [0, 2, 4, 6, 8],
  6: [0, 2, 3, 5, 6, 8]
};

const die1El = document.getElementById('die-1');
const die2El = document.getElementById('die-2');
const sumDisplay = document.getElementById('sum-display');
const rollButton = document.getElementById('roll-button');

let audioCtx = null;

function getRandomDie() {
  return Math.floor(Math.random() * 6) + 1;
}

function renderDie(element, value) {
  element.innerHTML = '';
  const positions = DOT_POSITIONS[value];
  for (let i = 0; i < 9; i++) {
    const slot = document.createElement('div');
    slot.className = 'dot-slot';
    if (positions.includes(i)) {
      const dot = document.createElement('div');
      dot.className = 'dot';
      slot.appendChild(dot);
    }
    element.appendChild(slot);
  }
}

function initDie(element) {
  element.innerHTML = '';
  for (let i = 0; i < 9; i++) {
    const slot = document.createElement('div');
    slot.className = 'dot-slot';
    element.appendChild(slot);
  }
}

function playSound() {
  try {
    if (!audioCtx) audioCtx = new AudioContext();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const duration = 0.35;
    const buffer = audioCtx.createBuffer(1, audioCtx.sampleRate * duration, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < data.length; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (audioCtx.sampleRate * 0.12));
    }

    const source = audioCtx.createBufferSource();
    source.buffer = buffer;

    const filter = audioCtx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 600;

    source.connect(filter);
    filter.connect(audioCtx.destination);
    source.start();
  } catch (_) {
    // автовоспроизведение заблокировано браузером — некритично
  }
}

function rollDice() {
  rollButton.disabled = true;
  die1El.classList.add('rolling');
  die2El.classList.add('rolling');
  sumDisplay.textContent = '';

  playSound();

  const value1 = getRandomDie();
  const value2 = getRandomDie();

  setTimeout(() => {
    die1El.classList.remove('rolling');
    die2El.classList.remove('rolling');
    renderDie(die1El, value1);
    renderDie(die2El, value2);
    sumDisplay.textContent = `Сумма: ${value1 + value2}`;
    rollButton.disabled = false;
  }, ANIMATION_DURATION);
}

rollButton.addEventListener('click', rollDice);

initDie(die1El);
initDie(die2El);
