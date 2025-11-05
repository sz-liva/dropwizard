#!/usr/bin/env python3
"""
Quiz Ranking Simulation

Simulates quiz results based on per-question success rates to estimate
what ranking a team with 4 correct answers would achieve.
"""

import random
import statistics
from collections import Counter

# Quiz statistics: number of teams who answered correctly / total teams
QUIZ_STATS = {
    1: (177, 313),
    2: (190, 313),
    3: (266, 313),
    4: (104, 313),
    5: (77, 313),
    6: (35, 313),
    7: (72, 313),
}

TOTAL_TEAMS = 313
NUM_SIMULATIONS = 100000

# Calculate probability for each question
probabilities = {q: correct / total for q, (correct, total) in QUIZ_STATS.items()}

print("Question Success Rates:")
for q, prob in probabilities.items():
    print(f"  Q{q}: {prob:.1%}")
print()


def simulate_quiz():
    """Simulate one instance of the quiz with 313 teams."""
    scores = []

    for _ in range(TOTAL_TEAMS):
        # Each team answers each question independently based on success probability
        score = sum(1 for q in range(1, 8) if random.random() < probabilities[q])
        scores.append(score)

    return scores


def calculate_ranking(scores, target_score):
    """
    Calculate the ranking for a team with target_score.
    Teams with same score share places (e.g., if 2 teams tie for 1st, both get "1-2").

    Returns: (min_rank, max_rank) - the range of places shared
    """
    score_counts = Counter(scores)

    # Count teams with better scores
    teams_better = sum(count for score, count in score_counts.items() if score > target_score)

    # Count teams with same score
    teams_same = score_counts[target_score]

    # Ranking range: teams sharing places get min-max range
    min_rank = teams_better + 1
    max_rank = teams_better + teams_same

    return min_rank, max_rank


def main():
    print(f"Running {NUM_SIMULATIONS:,} simulations...\n")

    # Store results
    min_ranks = []
    max_ranks = []
    score_distributions = []

    for i in range(NUM_SIMULATIONS):
        if (i + 1) % 10000 == 0:
            print(f"Progress: {i + 1:,}/{NUM_SIMULATIONS:,}")

        scores = simulate_quiz()
        score_distributions.append(Counter(scores))

        min_rank, max_rank = calculate_ranking(scores, target_score=4)
        min_ranks.append(min_rank)
        max_ranks.append(max_rank)

    print("\n" + "="*60)
    print("SIMULATION RESULTS")
    print("="*60)

    # Analyze rankings for team with 4 correct answers
    avg_min_rank = statistics.mean(min_ranks)
    avg_max_rank = statistics.mean(max_ranks)
    median_min_rank = statistics.median(min_ranks)
    median_max_rank = statistics.median(max_ranks)

    # Calculate percentiles
    sorted_min = sorted(min_ranks)
    sorted_max = sorted(max_ranks)
    p5_min = sorted_min[int(len(sorted_min) * 0.05)]
    p5_max = sorted_max[int(len(sorted_max) * 0.05)]
    p95_min = sorted_min[int(len(sorted_min) * 0.95)]
    p95_max = sorted_max[int(len(sorted_max) * 0.95)]

    print(f"\nTeam with 4 correct answers:")
    print(f"  Average ranking: {avg_min_rank:.1f}-{avg_max_rank:.1f}")
    print(f"  Median ranking:  {median_min_rank:.0f}-{median_max_rank:.0f}")
    print(f"  Best case (5th percentile):  {p5_min}-{p5_max}")
    print(f"  Worst case (95th percentile): {p95_min}-{p95_max}")

    # Average score distribution
    print(f"\nAverage Score Distribution (out of {TOTAL_TEAMS} teams):")
    avg_distribution = Counter()
    for dist in score_distributions:
        avg_distribution.update(dist)

    for score in sorted(avg_distribution.keys(), reverse=True):
        avg_count = avg_distribution[score] / NUM_SIMULATIONS
        percentage = (avg_count / TOTAL_TEAMS) * 100
        print(f"  {score} correct: {avg_count:6.1f} teams ({percentage:5.1f}%)")

    # Calculate expected teams scoring better than 4
    teams_better = sum(avg_distribution[score] / NUM_SIMULATIONS
                      for score in range(5, 8))
    print(f"\nExpected teams scoring 5+ points: {teams_better:.1f}")
    print(f"Expected ranking for 4 points: ~{teams_better + 1:.0f}")

    # Ranking distribution
    print(f"\nRanking Distribution for 4-point teams:")
    rank_combo_counts = Counter(zip(min_ranks, max_ranks))
    most_common = rank_combo_counts.most_common(10)

    for (min_r, max_r), count in most_common:
        percentage = (count / NUM_SIMULATIONS) * 100
        if min_r == max_r:
            print(f"  Place {min_r}: {percentage:.1f}%")
        else:
            print(f"  Places {min_r}-{max_r}: {percentage:.1f}%")


if __name__ == "__main__":
    main()
