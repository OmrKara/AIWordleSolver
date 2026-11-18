# Word list provenance

The project uses two newline-delimited UTF-8 word lists:

- `eng_dict.txt` contains 14,855 accepted five-letter guesses. It was recovered from the existing desktop project folder and matches the randomly ordered list in [tabatkins/wordle-list](https://github.com/tabatkins/wordle-list), sourced from the original Wordle game's client code.
- `answers.txt` contains the original 2,315 Wordle answer words, mirrored alphabetically in [cfreshman's answer-list gist](https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b). The downloaded revision is pinned at `a9e55d7e0c08100ce62133a1fa0d9c4f0f542f2c` so the project data can be traced.

The answer list is the original Wordle solution set, not a live feed of the New York Times' current daily answers. Every answer is also present in the accepted-guess list. The application draws hidden answers from `answers.txt`, accepts user guesses from `eng_dict.txt`, and searches the full accepted-guess list for entropy suggestions.
