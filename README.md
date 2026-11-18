# Wordle Entropy Solver

A Wordle game and deterministic entropy-based solver implemented in Python and JavaScript. The project includes a Tkinter desktop game and a browser version with an AI suggestion button.

## Live Demo

[Play Wordle Entropy Solver](https://aiwordlesolver.onrender.com/)

## Project Goal

The goal is to solve a five-letter Wordle using feedback from previous guesses to reduce the remaining answer set. The solver does not train a machine-learning model. Given the same answers and feedback, it follows the same deterministic selection rules.

The browser version follows the game layout of the original Wordle board and keyboard. Its AI button fills the current empty row with a suggestion; the player submits that suggestion with Enter.

## How It Works

1. The game selects a hidden answer from `answers.txt`. Valid guesses are checked against `eng_dict.txt`.
2. After each guess, the game marks letters as green, yellow, or gray. It handles repeated letters by matching greens first, then allocating remaining occurrences to yellow tiles.
3. The solver filters the answer list to keep only words consistent with every previous guess and its feedback.
4. The first AI suggestion is the fixed seed word `SOARE`, matching the desktop solver's strategy.
5. For later suggestions, the solver simulates every valid guess against the remaining answers. It groups answers by their possible feedback patterns and calculates Shannon entropy:

   `H = -Σ pᵢ log₂(pᵢ)`

   It suggests the guess with the highest feedback entropy. Ties prefer a remaining answer, then the alphabetically earlier guess.

The browser solver runs in a Web Worker so the game remains responsive while it scores guesses. The web app uses local word-list files and makes no API calls.

## Findings

The final project report records results from an earlier 100-game experiment:

| Guesses used | Games solved |
| --- | ---: |
| 3 | 28 |
| 4 | 58 |
| 5 | 13 |
| 6 | 1 |

That run reported a 100% solve rate and an average of 3.87 guesses. Its average game time was about 3.81 seconds on the test machine. These are historical results, not a fresh benchmark of the current code: the earlier experiment used one combined word list and tested its first 100 alphabetically sorted words. The current simulator separates answer and guess lists and uses a reproducible random sample across the answer list by default. Run it again to produce results for the current setup.

Entropy is a greedy information-gain heuristic. It chooses the guess with the most informative immediate feedback and does not guarantee the globally shortest solution path for every answer.

## Run the Browser Game Locally

From the project directory, run:

```powershell
python server.py
```

The server opens the game at `http://127.0.0.1:8766`. Stop it with `Ctrl+C` in the server window.

## Run the Desktop Game

```powershell
python wordle.py
```

## Run the Solver Simulation

```powershell
python test_wordle_entropy.py
python test_wordle_entropy.py --all-answers
```

The default run evaluates a reproducible sample of 100 answers using seed `441`. Use `--games N` and `--seed N` to change the sample. `--all-answers` evaluates all 2,315 answers in the bundled original answer list. Detailed output is saved to `wordle_entropy_test_results.txt`.

## Word Lists

- `eng_dict.txt` contains 14,855 accepted five-letter guesses.
- `answers.txt` contains the original 2,315 Wordle answer words.

See [WORDLIST_SOURCES.md](WORDLIST_SOURCES.md) for the list provenance and scope. The answer list is the original solution set, not a live feed of current NYT daily answers.
