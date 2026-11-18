const WORD_LENGTH = 5;
let guessWords = [];
let answerWords = [];
const remainingLetters = new Uint8Array(26);
const feedbackDigits = new Uint8Array(WORD_LENGTH);
const bucketCounts = new Uint32Array(3 ** WORD_LENGTH);

function feedbackCode(guess, target) {
  remainingLetters.fill(0);
  for (let i = 0; i < WORD_LENGTH; i += 1) {
    if (guess.charCodeAt(i) === target.charCodeAt(i)) {
      feedbackDigits[i] = 2;
    } else {
      feedbackDigits[i] = 0;
      remainingLetters[target.charCodeAt(i) - 65] += 1;
    }
  }

  for (let i = 0; i < WORD_LENGTH; i += 1) {
    if (feedbackDigits[i] === 2) continue;
    const letterIndex = guess.charCodeAt(i) - 65;
    if (remainingLetters[letterIndex] > 0) {
      feedbackDigits[i] = 1;
      remainingLetters[letterIndex] -= 1;
    }
  }

  let code = 0;
  let place = 1;
  for (let i = 0; i < WORD_LENGTH; i += 1) {
    code += feedbackDigits[i] * place;
    place *= 3;
  }
  return code;
}

function statesCode(states) {
  let code = 0;
  let place = 1;
  for (const state of states) {
    code += (state === "correct" ? 2 : state === "present" ? 1 : 0) * place;
    place *= 3;
  }
  return code;
}

function getCandidates(history) {
  const codedHistory = history.map(({ guess, states }) => ({
    guess,
    code: statesCode(states),
  }));
  return answerWords.filter((answer) => codedHistory.every(
    ({ guess, code }) => feedbackCode(guess, answer) === code,
  ));
}

function entropyForGuess(guess, candidates) {
  bucketCounts.fill(0);
  const touched = [];
  for (const target of candidates) {
    const pattern = feedbackCode(guess, target);
    if (bucketCounts[pattern] === 0) touched.push(pattern);
    bucketCounts[pattern] += 1;
  }

  let entropy = 0;
  const total = candidates.length;
  for (const pattern of touched) {
    const probability = bucketCounts[pattern] / total;
    entropy -= probability * Math.log2(probability);
  }
  return entropy;
}

function bestEntropyGuess(candidates) {
  if (candidates.length === 0) return null;
  if (candidates.length === 1) return { guess: candidates[0], entropy: 0 };

  const candidateSet = new Set(candidates);
  let bestGuess = null;
  let bestEntropy = -1;
  for (const guess of guessWords) {
    const entropy = entropyForGuess(guess, candidates);
    if (entropy > bestEntropy + 1e-12) {
      bestGuess = guess;
      bestEntropy = entropy;
    } else if (Math.abs(entropy - bestEntropy) <= 1e-12) {
      const isCandidate = candidateSet.has(guess);
      const bestIsCandidate = candidateSet.has(bestGuess);
      if ((isCandidate && !bestIsCandidate) ||
          (isCandidate === bestIsCandidate && guess < bestGuess)) {
        bestGuess = guess;
      }
    }
  }
  return { guess: bestGuess, entropy: bestEntropy };
}

self.addEventListener("message", (event) => {
  const message = event.data;
  if (message.type === "init") {
    guessWords = message.guessWords;
    answerWords = message.answerWords;
    self.postMessage({ type: "ready" });
    return;
  }
  if (message.type !== "guess") return;

  const candidates = getCandidates(message.history);
  if (candidates.length === 0) {
    self.postMessage({ type: "result", error: "Geri bildirimlerle eşleşen cevap kalmadı." });
    return;
  }

  const result = bestEntropyGuess(candidates);
  self.postMessage({
    type: "result",
    guess: result.guess,
    entropy: result.entropy,
    candidateCount: candidates.length,
  });
});
