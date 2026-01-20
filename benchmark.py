#!/usr/bin/env python3
"""
Comprehensive benchmark: Run all algorithms on all inputs and compare results.
"""

import os
import sys
import time
import glob
from collections import defaultdict
from tabulate import tabulate

import parse
from utils import is_valid_solution, calculate_happiness
from algorithms import simulated_annealing, greedy_local_search, genetic_algorithm


ALGORITHMS = {
    'sim_annealing': ('Sim Annealing', simulated_annealing),
    'greedy': ('Greedy', greedy_local_search),
    'genetic': ('Genetic', genetic_algorithm),
}


def run_benchmark(sizes=None, save_outputs=True, max_files=None):
    """Run all algorithms on all inputs."""
    if sizes is None:
        sizes = ['small', 'medium', 'large']

    results = []
    summary = {alg: defaultdict(lambda: {'happiness': 0, 'time': 0, 'valid': 0, 'count': 0, 'wins': 0})
               for alg in ALGORITHMS}

    for size in sizes:
        input_dir = f"data/{size}/inputs"
        if not os.path.exists(input_dir):
            print(f"Skipping {size}: directory not found")
            continue

        input_files = sorted(glob.glob(os.path.join(input_dir, "*.in")))
        if max_files:
            input_files = input_files[:max_files]

        print(f"\n{'='*60}")
        print(f"Processing {len(input_files)} {size.upper()} inputs")
        print('='*60)

        for idx, input_file in enumerate(input_files):
            basename = os.path.basename(input_file)
            print(f"[{idx+1}/{len(input_files)}] {basename}...", end=" ", flush=True)

            try:
                G, s = parse.read_input_file(input_file)
            except Exception as e:
                print(f"ERROR reading: {e}")
                continue

            file_results = {}
            best_happiness = -1
            best_alg = None

            for alg_key, (alg_name, alg_func) in ALGORITHMS.items():
                try:
                    start = time.time()
                    D, k = alg_func(G, s)
                    elapsed = time.time() - start

                    valid = is_valid_solution(D, G, s, k)
                    happiness = calculate_happiness(D, G) if valid else 0

                    file_results[alg_key] = {
                        'D': D,
                        'k': k,
                        'happiness': happiness,
                        'valid': valid,
                        'time': elapsed
                    }

                    # Track best for this file
                    if valid and happiness > best_happiness:
                        best_happiness = happiness
                        best_alg = alg_key

                    # Update summary
                    summary[alg_key][size]['happiness'] += happiness
                    summary[alg_key][size]['time'] += elapsed
                    summary[alg_key][size]['valid'] += 1 if valid else 0
                    summary[alg_key][size]['count'] += 1

                except Exception as e:
                    print(f"{alg_name} ERROR: {e}", end=" ")
                    file_results[alg_key] = None

            # Mark winner
            if best_alg:
                summary[best_alg][size]['wins'] += 1

            # Save best output
            if save_outputs and best_alg and file_results[best_alg]:
                output_dir = f"data/{size}/outputs"
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, basename.replace('.in', '.out'))
                parse.write_output_file(file_results[best_alg]['D'], output_file)

            # Print comparison for this file
            result_str = []
            for alg_key in ALGORITHMS:
                if file_results.get(alg_key):
                    r = file_results[alg_key]
                    marker = "*" if alg_key == best_alg else " "
                    result_str.append(f"{alg_key}:{r['happiness']:.1f}{marker}")
            print(" | ".join(result_str))

            results.append({
                'size': size,
                'file': basename,
                'results': file_results,
                'winner': best_alg
            })

    return results, summary


def print_summary(summary):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("SUMMARY BY SIZE")
    print("="*80)

    for size in ['small', 'medium', 'large']:
        print(f"\n{size.upper()}:")
        table = []
        for alg_key, (alg_name, _) in ALGORITHMS.items():
            s = summary[alg_key][size]
            if s['count'] > 0:
                table.append({
                    'Algorithm': alg_name,
                    'Avg Happiness': round(s['happiness'] / s['count'], 2),
                    'Total Happiness': round(s['happiness'], 2),
                    'Valid': f"{s['valid']}/{s['count']}",
                    'Wins': s['wins'],
                    'Avg Time': f"{s['time'] / s['count']:.3f}s"
                })
        if table:
            print(tabulate(table, headers='keys', tablefmt='grid'))

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    overall = []
    for alg_key, (alg_name, _) in ALGORITHMS.items():
        total_happiness = sum(summary[alg_key][sz]['happiness'] for sz in ['small', 'medium', 'large'])
        total_count = sum(summary[alg_key][sz]['count'] for sz in ['small', 'medium', 'large'])
        total_valid = sum(summary[alg_key][sz]['valid'] for sz in ['small', 'medium', 'large'])
        total_wins = sum(summary[alg_key][sz]['wins'] for sz in ['small', 'medium', 'large'])
        total_time = sum(summary[alg_key][sz]['time'] for sz in ['small', 'medium', 'large'])

        if total_count > 0:
            overall.append({
                'Algorithm': alg_name,
                'Avg Happiness': round(total_happiness / total_count, 2),
                'Total Happiness': round(total_happiness, 2),
                'Valid': f"{total_valid}/{total_count}",
                'Wins': total_wins,
                'Win Rate': f"{100*total_wins/total_count:.1f}%",
                'Total Time': f"{total_time:.1f}s"
            })

    print(tabulate(overall, headers='keys', tablefmt='grid'))


def print_head_to_head(results):
    """Print head-to-head comparison."""
    print("\n" + "="*80)
    print("HEAD-TO-HEAD COMPARISON")
    print("="*80)

    comparisons = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0})

    for r in results:
        if not r['results']:
            continue

        algs = list(ALGORITHMS.keys())
        for i, alg_a in enumerate(algs):
            for alg_b in algs[i+1:]:
                res_a = r['results'].get(alg_a)
                res_b = r['results'].get(alg_b)

                if res_a and res_b and res_a['valid'] and res_b['valid']:
                    key = f"{alg_a} vs {alg_b}"
                    if res_a['happiness'] > res_b['happiness']:
                        comparisons[key]['wins'] += 1
                    elif res_a['happiness'] < res_b['happiness']:
                        comparisons[key]['losses'] += 1
                    else:
                        comparisons[key]['ties'] += 1

    table = []
    for matchup, stats in comparisons.items():
        alg_a, alg_b = matchup.split(' vs ')
        total = stats['wins'] + stats['losses'] + stats['ties']
        table.append({
            'Matchup': matchup,
            f'{alg_a} wins': stats['wins'],
            f'{alg_b} wins': stats['losses'],
            'Ties': stats['ties'],
            'Total': total
        })

    print(tabulate(table, headers='keys', tablefmt='grid'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Comprehensive algorithm benchmark')
    parser.add_argument('--sizes', nargs='+', choices=['small', 'medium', 'large'],
                        default=['small', 'medium', 'large'], help='Sizes to benchmark')
    parser.add_argument('--max-files', type=int, help='Max files per size category')
    parser.add_argument('--no-save', action='store_true', help='Do not save output files')

    args = parser.parse_args()

    print("Starting comprehensive benchmark...")
    print(f"Sizes: {args.sizes}")
    print(f"Max files per size: {args.max_files or 'all'}")

    results, summary = run_benchmark(
        sizes=args.sizes,
        save_outputs=not args.no_save,
        max_files=args.max_files
    )

    print_summary(summary)
    print_head_to_head(results)
