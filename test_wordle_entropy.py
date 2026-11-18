# Entropi çözücüsü için tekrarlanabilir oyun simülasyonu.

import argparse
import math
import random
import time
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

from wordle import ANSWER_WORDS, GUESS_WORDS, MAX_GUESSES, evaluate_guess

FIRST_GUESS = "SOARE"
N_GAMES = 100
DEFAULT_SEED = 441
OUTPUT_FILE = Path(__file__).resolve().parent / "wordle_entropy_test_results.txt"
MAX_FEEDBACK_CACHE_SIZE = 250_000


class WordleEntropyTester:
    def __init__(self, guess_words, answer_words, output_file=OUTPUT_FILE):
        self.guess_words = sorted(set(guess_words))
        self.answer_words = sorted(set(answer_words))
        if not self.answer_words:
            raise ValueError("Cevap listesi boş.")
        if not set(self.answer_words).issubset(self.guess_words):
            raise ValueError("Cevap listesi, geçerli tahminler listesinin alt kümesi olmalı.")
        if FIRST_GUESS not in self.guess_words:
            raise ValueError(f"İlk tahmin {FIRST_GUESS}, tahmin listesinde bulunamadı.")

        self.feedback_cache = OrderedDict()
        self.pattern_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.output_file = Path(output_file)
        self.log_lines = []

    def log(self, message=""):
        print(message)
        self.log_lines.append(message)

    def save_log_file(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text("\n".join(self.log_lines), encoding="utf-8")

    def feedback_pattern(self, guess: str, target: str):
        self.pattern_requests += 1
        key = (guess, target)
        cached = self.feedback_cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            self.feedback_cache.move_to_end(key)
            return cached

        self.cache_misses += 1
        pattern = tuple(evaluate_guess(guess, target))
        self.feedback_cache[key] = pattern
        if len(self.feedback_cache) > MAX_FEEDBACK_CACHE_SIZE:
            self.feedback_cache.popitem(last=False)
        return pattern

    def get_candidates(self, history):
        candidates = []
        for word in self.answer_words:
            if all(
                self.feedback_pattern(past_guess, word) == tuple(past_states)
                for past_guess, past_states in history
            ):
                candidates.append(word)
        return candidates

    def entropy_score_with_stats(self, guess: str, candidates):
        buckets = defaultdict(int)
        for target in candidates:
            buckets[self.feedback_pattern(guess, target)] += 1

        total = len(candidates)
        entropy = 0.0
        for count in buckets.values():
            p = count / total
            entropy -= p * math.log2(p)

        return {
            "entropy": entropy,
            "bucket_count": len(buckets),
            "largest_bucket": max(buckets.values()) if buckets else 0,
            "pair_requests": len(candidates),
        }

    def best_entropy_guess(self, candidates):
        if not candidates:
            return None, None
        if len(candidates) == 1:
            return candidates[0], {
                "entropy": 0.0,
                "bucket_count": 1,
                "largest_bucket": 1,
                "pair_requests": 0,
                "evaluated_guesses": 0,
                "candidate_count": 1,
                "total_pair_requests": 0,
            }

        candidate_set = set(candidates)
        best_guess = None
        best_meta = None
        best_entropy = -1.0
        evaluated_guesses = 0
        total_pair_requests = 0

        for guess in self.guess_words:
            meta = self.entropy_score_with_stats(guess, candidates)
            evaluated_guesses += 1
            total_pair_requests += meta["pair_requests"]
            entropy = meta["entropy"]

            if entropy > best_entropy:
                best_entropy = entropy
                best_guess = guess
                best_meta = meta
            elif math.isclose(entropy, best_entropy, rel_tol=1e-12, abs_tol=1e-12):
                if best_guess is None:
                    best_guess = guess
                    best_meta = meta
                else:
                    guess_is_candidate = guess in candidate_set
                    best_is_candidate = best_guess in candidate_set
                    if guess_is_candidate and not best_is_candidate:
                        best_guess = guess
                        best_meta = meta
                    elif guess_is_candidate == best_is_candidate and guess < best_guess:
                        best_guess = guess
                        best_meta = meta

        best_meta = dict(best_meta)
        best_meta["evaluated_guesses"] = evaluated_guesses
        best_meta["candidate_count"] = len(candidates)
        best_meta["total_pair_requests"] = total_pair_requests
        return best_guess, best_meta

    def play_one_game(self, answer: str, game_index: int):
        history = []
        solved = False
        per_turn = []
        game_start = time.perf_counter()

        self.log("=" * 90)
        self.log(f"OYUN {game_index:03d} | Hedef kelime: {answer}")
        self.log("=" * 90)

        for turn in range(1, MAX_GUESSES + 1):
            turn_start = time.perf_counter()
            requests_before = self.pattern_requests
            cache_hits_before = self.cache_hits
            cache_misses_before = self.cache_misses

            if not history:
                guess = FIRST_GUESS
                selection_meta = {
                    "entropy": None,
                    "bucket_count": None,
                    "largest_bucket": None,
                    "evaluated_guesses": 0,
                    "candidate_count": len(self.answer_words),
                    "total_pair_requests": 0,
                }
                candidates_before = len(self.answer_words)
            else:
                candidates = self.get_candidates(history)
                candidates_before = len(candidates)
                guess, selection_meta = self.best_entropy_guess(candidates)
                if guess is None:
                    self.log(f"Tur {turn}: Aday kalmadığı için tahmin üretilemedi.")
                    break

            states = tuple(evaluate_guess(guess, answer))
            history.append((guess, states))
            candidates_after = len(self.get_candidates(history))

            turn_time = time.perf_counter() - turn_start
            request_delta = self.pattern_requests - requests_before
            cache_hits_delta = self.cache_hits - cache_hits_before
            cache_misses_delta = self.cache_misses - cache_misses_before
            turn_record = {
                "turn": turn,
                "guess": guess,
                "states": states,
                "candidates_before": candidates_before,
                "candidates_after": candidates_after,
                "turn_time": turn_time,
                "selection_meta": selection_meta,
                "pattern_requests": request_delta,
                "pattern_evaluations": cache_misses_delta,
                "cache_hits": cache_hits_delta,
                "cache_misses": cache_misses_delta,
            }
            per_turn.append(turn_record)

            state_str = ",".join(states)
            entropy = selection_meta["entropy"]
            entropy_str = "N/A" if entropy is None else f"{entropy:.6f}"
            bucket_count = selection_meta["bucket_count"]
            bucket_str = "N/A" if bucket_count is None else str(bucket_count)
            largest_bucket = selection_meta["largest_bucket"]
            largest_str = "N/A" if largest_bucket is None else str(largest_bucket)
            self.log(
                f"Tur {turn} | guess={guess} | states=[{state_str}] | "
                f"aday önce={candidates_before} | aday sonra={candidates_after} | "
                f"süre={turn_time:.6f}s | entropy={entropy_str} | "
                f"bucket={bucket_str} | max_bucket={largest_str} | "
                f"guess_eval={selection_meta['evaluated_guesses']} | "
                f"entropy_pair={selection_meta['total_pair_requests']} | "
                f"pattern_request={request_delta} | hesaplanan_pattern={cache_misses_delta} | "
                f"cache_hit={cache_hits_delta} | cache_miss={cache_misses_delta}"
            )

            if guess == answer:
                solved = True
                break

        game_time = time.perf_counter() - game_start
        total_guesses = len(per_turn)
        avg_turn_time = (
            sum(turn["turn_time"] for turn in per_turn) / total_guesses
            if total_guesses else 0.0
        )
        total_pattern_requests = sum(turn["pattern_requests"] for turn in per_turn)
        total_pattern_evaluations = sum(turn["pattern_evaluations"] for turn in per_turn)

        self.log("-" * 90)
        self.log(
            f"OYUN SONUCU | solved={solved} | deneme_sayısı={total_guesses} | "
            f"toplam_süre={game_time:.6f}s | ort_tur_süresi={avg_turn_time:.6f}s | "
            f"pattern_isteği={total_pattern_requests} | "
            f"hesaplanan_pattern={total_pattern_evaluations}"
        )
        self.log()

        return {
            "answer": answer,
            "solved": solved,
            "guesses_used": total_guesses,
            "game_time": game_time,
            "avg_turn_time": avg_turn_time,
            "total_pattern_requests": total_pattern_requests,
            "total_pattern_evaluations": total_pattern_evaluations,
            "turns": per_turn,
        }

    def run_batch(self, answers_to_test):
        if not answers_to_test:
            raise ValueError("Test edilecek cevap bulunamadı.")
        results = [
            self.play_one_game(answer, game_index)
            for game_index, answer in enumerate(answers_to_test, start=1)
        ]

        self.print_summary(results)
        self.log()
        self.log(f"Test edilen cevap sayısı: {len(answers_to_test)}")
        self.log(f"Sonuçlar dosyaya kaydedildi: {self.output_file.resolve()}")
        self.save_log_file()
        return results

    def print_summary(self, results):
        total_games = len(results)
        solved_games = sum(1 for result in results if result["solved"])
        total_guesses = sum(result["guesses_used"] for result in results)
        total_time = sum(result["game_time"] for result in results)
        total_pattern_requests = sum(result["total_pattern_requests"] for result in results)
        total_pattern_evaluations = sum(result["total_pattern_evaluations"] for result in results)
        guesses_distribution = Counter(
            result["guesses_used"] for result in results if result["solved"]
        )
        all_turns = [turn for result in results for turn in result["turns"]]
        avg_turn_time = (
            sum(turn["turn_time"] for turn in all_turns) / len(all_turns)
            if all_turns else 0.0
        )
        max_turn_time = max((turn["turn_time"] for turn in all_turns), default=0.0)
        avg_candidates_before = (
            sum(turn["candidates_before"] for turn in all_turns) / len(all_turns)
            if all_turns else 0.0
        )
        cache_total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / cache_total * 100 if cache_total else 0.0

        self.log("#" * 90)
        self.log("GENEL ÖZET")
        self.log("#" * 90)
        self.log(f"Toplam oyun: {total_games}")
        self.log(f"Çözülen oyun: {solved_games}")
        self.log(f"Çözülemeyen oyun: {total_games - solved_games}")
        self.log(f"Başarı oranı: {solved_games / total_games * 100:.2f}%")
        self.log(f"Ortalama deneme sayısı: {total_guesses / total_games:.4f}")
        self.log(f"Toplam süre: {total_time:.6f}s")
        self.log(f"Ortalama oyun süresi: {total_time / total_games:.6f}s")
        self.log(f"Ortalama tur süresi: {avg_turn_time:.6f}s")
        self.log(f"Maksimum tek tur süresi: {max_turn_time:.6f}s")
        self.log(f"Ortalama aday sayısı (tur başı): {avg_candidates_before:.2f}")
        self.log(f"Geri bildirim isteği: {total_pattern_requests}")
        self.log(f"Önbellek dışında hesaplanan pattern: {total_pattern_evaluations}")
        self.log(f"Toplam cache hit: {self.cache_hits}")
        self.log(f"Toplam cache miss: {self.cache_misses}")
        self.log(f"Cache hit oranı: {hit_rate:.2f}%")
        self.log("Çözüm dağılımı (kaç denemede bulundu):")
        for guesses_used in sorted(guesses_distribution):
            self.log(f"  {guesses_used} deneme: {guesses_distribution[guesses_used]} oyun")


def main():
    parser = argparse.ArgumentParser(
        description="Entropi çözücüsünü cevap listesi üzerinde simüle eder."
    )
    parser.add_argument(
        "--all-answers",
        action="store_true",
        help="Özgün cevap listesindeki tüm kelimeleri test et.",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=N_GAMES,
        help=f"Sabit tohumla seçilecek oyun sayısı (varsayılan: {N_GAMES}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Tekrarlanabilir örneklem için tohum (varsayılan: {DEFAULT_SEED}).",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Sonuç dosyasının yolu.")
    args = parser.parse_args()
    if args.games < 1:
        parser.error("--games en az 1 olmalı.")

    tester = WordleEntropyTester(GUESS_WORDS, ANSWER_WORDS, output_file=args.output)
    if args.all_answers:
        answers_to_test = list(tester.answer_words)
    else:
        game_count = min(args.games, len(tester.answer_words))
        answers_to_test = random.Random(args.seed).sample(tester.answer_words, game_count)
        tester.log(f"Tekrarlanabilir örneklem: {game_count} cevap | seed={args.seed}")
    tester.run_batch(answers_to_test)


if __name__ == "__main__":
    main()
