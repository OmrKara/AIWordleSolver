const WORD_LENGTH = 5;
const MAX_GUESSES = 6;
const FIRST_GUESS = "SOARE";
const KEY_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"];
const SEVERITY = { absent: 1, present: 2, correct: 3 };

const board = document.querySelector("#board");
const statusLine = document.querySelector("#status");
const aiButton = document.querySelector("#ai-guess");
const aiLabel = document.querySelector("#ai-label");
const newGameButtons = [
  document.querySelector("#new-game-top"),
  document.querySelector("#new-game-bottom"),
];

const cells = [];
const keyButtons = new Map();
const keyStates = new Map();

let guessWords = [];
let answerWords = [];
let guessWordSet = new Set();
let history = [];
let answer = "";
let currentRow = 0;
let currentCol = 0;
let gameOver = false;
let aiBusy = false;
let worker;

function createBoard() {
  board.replaceChildren();
  for (let row = 0; row < MAX_GUESSES; row += 1) {
    const rowElement = document.createElement("div");
    rowElement.className = "board-row";
    rowElement.setAttribute("role", "row");
    const rowCells = [];
    for (let col = 0; col < WORD_LENGTH; col += 1) {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.setAttribute("role", "gridcell");
      tile.setAttribute("aria-label", `Satır ${row + 1}, harf ${col + 1}`);
      rowElement.append(tile);
      rowCells.push(tile);
    }
    board.append(rowElement);
    cells.push(rowCells);
  }
}

function createKeyboard() {
  for (const row of KEY_ROWS) {
    const rowElement = document.querySelector(`[data-row="${row.toLowerCase()}"]`);
    if (row === "ZXCVBNM") {
      const enter = createKey("ENTER", submitGuess, "key-wide");
      rowElement.append(enter);
    }
    for (const letter of row) {
      const button = createKey(letter, () => addLetter(letter));
      rowElement.append(button);
      keyButtons.set(letter, button);
      keyStates.set(letter, "");
    }
    if (row === "ZXCVBNM") {
      const backspace = createKey("⌫", removeLetter, "key-wide");
      backspace.setAttribute("aria-label", "Geri sil");
      rowElement.append(backspace);
    }
  }
}

function createKey(label, handler, extraClass = "") {
  const button = document.createElement("button");
  button.className = `key ${extraClass}`.trim();
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}

function setStatus(message, isError = false) {
  statusLine.textContent = message;
  statusLine.classList.toggle("error", isError);
}

function evaluateGuess(guess, target) {
  const result = Array(WORD_LENGTH).fill("absent");
  const remaining = new Map();

  for (let i = 0; i < WORD_LENGTH; i += 1) {
    if (guess[i] === target[i]) {
      result[i] = "correct";
    } else {
      remaining.set(target[i], (remaining.get(target[i]) ?? 0) + 1);
    }
  }

  for (let i = 0; i < WORD_LENGTH; i += 1) {
    if (result[i] === "correct") continue;
    const count = remaining.get(guess[i]) ?? 0;
    if (count > 0) {
      result[i] = "present";
      remaining.set(guess[i], count - 1);
    }
  }
  return result;
}

function renderCurrentRow(extraClass = "") {
  const rowCells = cells[currentRow];
  for (let col = 0; col < WORD_LENGTH; col += 1) {
    const tile = rowCells[col];
    tile.textContent = col < currentCol ? tileLetters[col] : "";
    tile.classList.toggle("filled", col < currentCol);
    tile.classList.toggle("ai-filled", col < currentCol && extraClass === "ai-filled");
  }
}

let tileLetters = Array(WORD_LENGTH).fill("");

function addLetter(letter) {
  if (gameOver || aiBusy || currentRow >= MAX_GUESSES || currentCol >= WORD_LENGTH) return;
  tileLetters[currentCol] = letter;
  currentCol += 1;
  renderCurrentRow();
  setStatus("");
}

function removeLetter() {
  if (gameOver || aiBusy || currentCol === 0) return;
  currentCol -= 1;
  tileLetters[currentCol] = "";
  renderCurrentRow();
  setStatus("");
}

function updateKeyboard(guess, states) {
  for (let i = 0; i < WORD_LENGTH; i += 1) {
    const letter = guess[i];
    const nextState = states[i];
    const currentState = keyStates.get(letter) ?? "";
    if ((SEVERITY[nextState] ?? 0) > (SEVERITY[currentState] ?? 0)) {
      keyStates.set(letter, nextState);
      const button = keyButtons.get(letter);
      button.classList.remove("correct", "present", "absent");
      button.classList.add(nextState);
    }
  }
}

function submitGuess() {
  if (gameOver || aiBusy || currentRow >= MAX_GUESSES) return;
  if (currentCol !== WORD_LENGTH) {
    setStatus("Tahmin için 5 harfi tamamla.", true);
    return;
  }

  const guess = tileLetters.join("");
  if (!guessWordSet.has(guess)) {
    setStatus("Bu kelime tahmin sözlüğünde bulunamadı.", true);
    return;
  }

  const states = evaluateGuess(guess, answer);
  history.push({ guess, states });
  for (let col = 0; col < WORD_LENGTH; col += 1) {
    const tile = cells[currentRow][col];
    tile.classList.remove("filled", "ai-filled");
    tile.classList.add(states[col]);
  }
  updateKeyboard(guess, states);

  if (guess === answer) {
    gameOver = true;
    setAiBusy(false);
    setStatus(`Bildin! Cevap: ${answer}`);
    return;
  }

  currentRow += 1;
  currentCol = 0;
  tileLetters = Array(WORD_LENGTH).fill("");
  if (currentRow >= MAX_GUESSES) {
    gameOver = true;
    setAiBusy(false);
    setStatus(`Oyun bitti. Cevap: ${answer}`);
  } else {
    setStatus(`${MAX_GUESSES - currentRow} tahmin hakkın kaldı.`);
  }
}

function setAiBusy(isBusy) {
  aiBusy = isBusy;
  aiButton.disabled = isBusy || gameOver;
  aiLabel.textContent = isBusy ? "Hesaplanıyor…" : "AI Tahmini";
  for (const button of newGameButtons) button.disabled = isBusy;
  for (const button of keyButtons.values()) button.disabled = isBusy || gameOver;
  for (const button of document.querySelectorAll(".key-wide")) {
    button.disabled = isBusy || gameOver;
  }
}

function requestAiGuess() {
  if (gameOver || aiBusy || currentRow >= MAX_GUESSES) return;
  if (currentCol > 0) {
    setStatus("AI tahmini için önce mevcut satırı temizle.", true);
    return;
  }

  if (history.length === 0) {
    fillAiGuess(FIRST_GUESS, null, answerWords.length);
    return;
  }

  setAiBusy(true);
  setStatus("Aday kelimeler için entropy hesaplanıyor…");
  worker.postMessage({ type: "guess", history });
}

function fillAiGuess(guess, entropy, candidateCount) {
  tileLetters = guess.split("");
  currentCol = WORD_LENGTH;
  renderCurrentRow("ai-filled");
  const details = entropy === null
    ? "sabit başlangıç tahmini"
    : `entropy ${entropy.toFixed(3)} bit, ${candidateCount} aday`;
  setStatus(`${guess}: ${details}. Enter ile gönder.`);
}

function startNewGame() {
  if (!answerWords.length) return;
  history = [];
  answer = answerWords[Math.floor(Math.random() * answerWords.length)];
  currentRow = 0;
  currentCol = 0;
  tileLetters = Array(WORD_LENGTH).fill("");
  gameOver = false;
  setAiBusy(false);
  for (const row of cells) {
    for (const tile of row) {
      tile.textContent = "";
      tile.className = "tile";
    }
  }
  for (const [letter, button] of keyButtons) {
    keyStates.set(letter, "");
    button.classList.remove("correct", "present", "absent");
  }
  setStatus("Yeni oyun başladı.");
}

function loadWords(text) {
  return [...new Set(text.split(/\r?\n/).map((word) => word.trim().toUpperCase()).filter(
    (word) => word.length === WORD_LENGTH && /^[A-Z]+$/.test(word),
  ))].sort();
}

async function initialize() {
  try {
    const [answersResponse, guessesResponse] = await Promise.all([
      fetch("answers.txt"),
      fetch("eng_dict.txt"),
    ]);
    if (!answersResponse.ok || !guessesResponse.ok) {
      throw new Error("Yerel kelime dosyaları sunucudan okunamadı.");
    }

    [answerWords, guessWords] = await Promise.all([
      answersResponse.text().then(loadWords),
      guessesResponse.text().then(loadWords),
    ]);
    guessWordSet = new Set(guessWords);
    if (!guessWordSet.has(FIRST_GUESS) || answerWords.some((word) => !guessWordSet.has(word))) {
      throw new Error("Cevap listesi tahmin sözlüğüyle uyumlu değil.");
    }

    worker = new Worker("solver.worker.js");
    worker.addEventListener("message", (event) => {
      const message = event.data;
      if (message.type === "ready") {
        aiButton.disabled = false;
        setStatus("Hazır. Tahminini yaz veya AI Tahmini’ne bas.");
      } else if (message.type === "result") {
        setAiBusy(false);
        if (message.error) {
          setStatus(message.error, true);
        } else {
          fillAiGuess(message.guess, message.entropy, message.candidateCount);
        }
      }
    });
    worker.addEventListener("error", () => {
      setAiBusy(false);
      setStatus("AI çözücü başlatılamadı. Yerel sunucuyu yeniden başlat.", true);
    });
    worker.postMessage({ type: "init", guessWords, answerWords });
    startNewGame();
    aiButton.disabled = true;
    setStatus("AI çözücü hazırlanıyor…");
  } catch (error) {
    setStatus(`${error.message} Sayfayı python server.py ile aç.`, true);
    aiButton.disabled = true;
  }
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    submitGuess();
  } else if (event.key === "Backspace") {
    event.preventDefault();
    removeLetter();
  } else if (/^[a-zA-Z]$/.test(event.key)) {
    addLetter(event.key.toUpperCase());
  }
});

aiButton.addEventListener("click", requestAiGuess);
for (const button of newGameButtons) button.addEventListener("click", startNewGame);

createBoard();
createKeyboard();
initialize();
