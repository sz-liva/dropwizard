#!/usr/bin/env python3
"""
Quiz Ranking Simulation

Simulates quiz results based on per-question success rates to estimate
what ranking a team would achieve.

Supports two simulation modes:
1. Independent: Questions answered independently (no correlation between team strength)
2. Correlated: Stronger teams perform better across all questions

Usage:
  # Independent mode (default)
  python3 quiz_ranking_simulation.py 1 2 4 7 < quiz_stats.txt

  # Correlated mode (models team strength)
  python3 quiz_ranking_simulation.py 1 2 4 7 --mode correlated < quiz_stats.txt

  # Control correlation strength (default: 1.0)
  python3 quiz_ranking_simulation.py 1 2 4 7 --mode correlated --strength 1.5 < quiz_stats.txt

Input format (via stdin):
  question_number: correct_answers/total_teams

Example:
  1: 177/313
  2: 190/313
  3: 266/313
"""

import sys
import random
import statistics
import argparse
import math
from collections import Counter


def parse_quiz_stats(input_lines):
    """
    Parse quiz statistics from input lines.

    Expected format: "question_number: correct/total"
    Example: "1: 177/313"

    Returns:
        dict: {question_number: (correct, total)}
        int: total number of teams
    """
    quiz_stats = {}
    total_teams = None

    for line in input_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        try:
            # Parse "1: 177/313" format
            parts = line.split(':')
            if len(parts) != 2:
                continue

            question_num = int(parts[0].strip())
            stats = parts[1].strip().split('/')

            if len(stats) != 2:
                continue

            correct = int(stats[0].strip())
            total = int(stats[1].strip())

            quiz_stats[question_num] = (correct, total)

            # Verify all questions have same total
            if total_teams is None:
                total_teams = total
            elif total_teams != total:
                print(f"Warning: Question {question_num} has different total ({total}) than previous questions ({total_teams})", file=sys.stderr)

        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse line: {line}", file=sys.stderr)
            continue

    if not quiz_stats:
        raise ValueError("No valid quiz statistics found in input")

    if total_teams is None:
        raise ValueError("Could not determine total number of teams")

    return quiz_stats, total_teams


def simulate_quiz_independent(probabilities, total_teams):
    """
    Simulate quiz with independent question answering.
    Each question is answered independently based on its success probability.
    """
    scores = []

    for _ in range(total_teams):
        # Each team answers each question independently based on success probability
        score = sum(1 for q in probabilities.keys() if random.random() < probabilities[q])
        scores.append(score)

    return scores


def simulate_quiz_correlated(probabilities, total_teams, correlation_strength=1.0):
    """
    Simulate quiz with correlated question answering.
    Stronger teams perform better across all questions.

    Uses a latent variable model:
    - Each team has an underlying "strength" drawn from Normal(0, correlation_strength)
    - Team strength affects probability of answering each question correctly
    - Uses logit transformation to maintain valid probabilities

    Args:
        probabilities: dict of question -> base probability
        total_teams: number of teams
        correlation_strength: standard deviation of team strength distribution
                            (higher = more variation between teams)
    """
    scores = []

    # Convert probabilities to logits for transformation
    def logit(p):
        # Handle edge cases
        p = max(0.001, min(0.999, p))
        return math.log(p / (1 - p))

    def inverse_logit(x):
        return 1 / (1 + math.exp(-x))

    base_logits = {q: logit(p) for q, p in probabilities.items()}

    for _ in range(total_teams):
        # Draw team strength from normal distribution
        team_strength = random.gauss(0, correlation_strength)

        # Adjust each question's probability based on team strength
        score = 0
        for q, base_logit in base_logits.items():
            # Add team strength to logit, then convert back to probability
            adjusted_logit = base_logit + team_strength
            adjusted_prob = inverse_logit(adjusted_logit)

            # Answer question based on adjusted probability
            if random.random() < adjusted_prob:
                score += 1

        scores.append(score)

    return scores


def simulate_quiz(probabilities, total_teams, mode='independent', correlation_strength=1.0):
    """
    Simulate one instance of the quiz.

    Args:
        probabilities: dict of question -> probability
        total_teams: number of teams
        mode: 'independent' or 'correlated'
        correlation_strength: strength of correlation (only used in correlated mode)
    """
    if mode == 'correlated':
        return simulate_quiz_correlated(probabilities, total_teams, correlation_strength)
    else:
        return simulate_quiz_independent(probabilities, total_teams)


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
    parser = argparse.ArgumentParser(
        description='Simulate quiz rankings based on per-question success rates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Independent mode (default) - questions answered independently
  python3 quiz_ranking_simulation.py 1 2 4 7 < quiz_stats.txt

  # Correlated mode - stronger teams perform better across all questions
  python3 quiz_ranking_simulation.py 1 2 4 7 --mode correlated < quiz_stats.txt

  # Adjust correlation strength (higher = more variation)
  python3 quiz_ranking_simulation.py 1 2 4 7 --mode correlated --strength 1.5 < quiz_stats.txt

  # From file with custom simulations
  python3 quiz_ranking_simulation.py 1 2 4 7 --simulations 50000 --input stats.txt

Input format (stdin):
  question_number: correct_answers/total_teams
"""
    )

    parser.add_argument(
        'correct_answers',
        type=int,
        nargs='+',
        help='Question numbers that the target team answered correctly (e.g., 1 2 4 7)'
    )

    parser.add_argument(
        '--simulations',
        type=int,
        default=100000,
        help='Number of simulations to run (default: 100000)'
    )

    parser.add_argument(
        '--input',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='Input file with quiz statistics (default: stdin)'
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['independent', 'correlated'],
        default='independent',
        help='Simulation mode: "independent" (default) or "correlated" (teams have varying strength)'
    )

    parser.add_argument(
        '--strength',
        type=float,
        default=1.0,
        help='Correlation strength for correlated mode (default: 1.0, higher = more variation between teams)'
    )

    args = parser.parse_args()

    # Read quiz statistics from stdin or file
    try:
        quiz_stats, total_teams = parse_quiz_stats(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nExpected input format:", file=sys.stderr)
        print("  1: 177/313", file=sys.stderr)
        print("  2: 190/313", file=sys.stderr)
        print("  3: 266/313", file=sys.stderr)
        sys.exit(1)

    # Calculate probabilities
    probabilities = {q: correct / total for q, (correct, total) in quiz_stats.items()}

    # Validate that target questions exist in quiz stats
    num_questions = len(quiz_stats)
    for q in args.correct_answers:
        if q not in quiz_stats:
            print(f"Error: Question {q} not found in quiz statistics", file=sys.stderr)
            print(f"Available questions: {sorted(quiz_stats.keys())}", file=sys.stderr)
            sys.exit(1)

    target_score = len(args.correct_answers)

    # Print configuration
    print("="*60)
    print("QUIZ RANKING SIMULATION")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Total teams: {total_teams}")
    print(f"  Total questions: {num_questions}")
    print(f"  Target team answered correctly: {sorted(args.correct_answers)}")
    print(f"  Target score: {target_score}/{num_questions}")
    print(f"  Number of simulations: {args.simulations:,}")
    print(f"  Simulation mode: {args.mode}")
    if args.mode == 'correlated':
        print(f"  Correlation strength: {args.strength}")

    print(f"\nQuestion Success Rates:")
    for q in sorted(probabilities.keys()):
        correct, total = quiz_stats[q]
        marker = " ✓" if q in args.correct_answers else ""
        print(f"  Q{q}: {probabilities[q]:.1%} ({correct}/{total}){marker}")
    print()

    # Run simulations
    print(f"Running {args.simulations:,} simulations...\n")

    min_ranks = []
    max_ranks = []
    score_distributions = []

    progress_interval = max(1, args.simulations // 10)

    for i in range(args.simulations):
        if (i + 1) % progress_interval == 0:
            print(f"Progress: {i + 1:,}/{args.simulations:,}")

        scores = simulate_quiz(probabilities, total_teams, args.mode, args.strength)
        score_distributions.append(Counter(scores))

        min_rank, max_rank = calculate_ranking(scores, target_score)
        min_ranks.append(min_rank)
        max_ranks.append(max_rank)

    # Analyze results
    print("\n" + "="*60)
    print("SIMULATION RESULTS")
    print("="*60)

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

    print(f"\nTeam with {target_score} correct answer{'s' if target_score != 1 else ''}:")
    print(f"  Average ranking: {avg_min_rank:.1f}-{avg_max_rank:.1f}")
    print(f"  Median ranking:  {median_min_rank:.0f}-{median_max_rank:.0f}")
    print(f"  Best case (5th percentile):  {p5_min}-{p5_max}")
    print(f"  Worst case (95th percentile): {p95_min}-{p95_max}")

    # Score distribution
    print(f"\nAverage Score Distribution (out of {total_teams} teams):")
    avg_distribution = Counter()
    for dist in score_distributions:
        avg_distribution.update(dist)

    max_score = max(avg_distribution.keys())
    for score in range(max_score, -1, -1):
        avg_count = avg_distribution[score] / args.simulations
        percentage = (avg_count / total_teams) * 100
        marker = " ← Target team" if score == target_score else ""
        print(f"  {score} correct: {avg_count:6.1f} teams ({percentage:5.1f}%){marker}")

    # Teams scoring better
    teams_better = sum(avg_distribution[score] / args.simulations
                      for score in range(target_score + 1, max_score + 1))
    print(f"\nExpected teams scoring {target_score + 1}+ points: {teams_better:.1f}")
    print(f"Expected ranking for {target_score} points: ~{teams_better + 1:.0f}")

    # Ranking distribution
    print(f"\nRanking Distribution for {target_score}-point teams (top 10):")
    rank_combo_counts = Counter(zip(min_ranks, max_ranks))
    most_common = rank_combo_counts.most_common(10)

    for (min_r, max_r), count in most_common:
        percentage = (count / args.simulations) * 100
        if min_r == max_r:
            print(f"  Place {min_r}: {percentage:.1f}%")
        else:
            print(f"  Places {min_r}-{max_r}: {percentage:.1f}%")


if __name__ == "__main__":
    main()
