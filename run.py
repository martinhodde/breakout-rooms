#!/usr/bin/env python3
"""
Unified CLI runner for breakout room optimization algorithms.

Usage:
    python run.py --algorithm sim_annealing --input data/small/inputs/small-1.in
    python run.py --benchmark --size small
    python run.py --validate data/
"""

import argparse
import os
import sys
import time
import glob
from tabulate import tabulate

import parse
from utils import is_valid_solution, calculate_happiness
from algorithms import simulated_annealing, greedy_local_search, genetic_algorithm


ALGORITHMS = {
    'sim_annealing': ('Simulated Annealing', simulated_annealing),
    'greedy': ('Greedy + Local Search', greedy_local_search),
    'genetic': ('Genetic Algorithm', genetic_algorithm),
}


def run_algorithm(algorithm_name, G, s):
    """Run specified algorithm and return results with timing."""
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm_name}. Choose from: {list(ALGORITHMS.keys())}")

    name, func = ALGORITHMS[algorithm_name]
    start_time = time.time()
    D, k = func(G, s)
    elapsed = time.time() - start_time

    return D, k, elapsed


def process_single_file(input_path, algorithm_name, output_path=None):
    """Process a single input file."""
    G, s = parse.read_input_file(input_path)
    D, k, elapsed = run_algorithm(algorithm_name, G, s)

    valid = is_valid_solution(D, G, s, k)
    happiness = calculate_happiness(D, G) if valid else 0

    result = {
        'input': os.path.basename(input_path),
        'algorithm': algorithm_name,
        'happiness': round(happiness, 2),
        'rooms': k,
        'valid': 'Yes' if valid else 'No',
        'time': f"{elapsed:.3f}s"
    }

    if output_path:
        parse.write_output_file(D, output_path)
        print(f"Output written to: {output_path}")

    return result


def benchmark(size, algorithms=None):
    """Benchmark algorithms on all inputs of a given size."""
    if algorithms is None:
        algorithms = list(ALGORITHMS.keys())

    input_dir = f"data/{size}/inputs"
    if not os.path.exists(input_dir):
        print(f"Error: Directory {input_dir} does not exist")
        return

    input_files = sorted(glob.glob(os.path.join(input_dir, "*.in")))
    if not input_files:
        print(f"No input files found in {input_dir}")
        return

    print(f"Benchmarking {len(input_files)} {size} inputs with {len(algorithms)} algorithms...\n")

    results = []
    totals = {alg: {'happiness': 0, 'time': 0, 'valid': 0, 'count': 0} for alg in algorithms}

    for input_file in input_files[:10]:  # Limit to 10 files for quick benchmark
        G, s = parse.read_input_file(input_file)
        basename = os.path.basename(input_file)

        for alg in algorithms:
            try:
                D, k, elapsed = run_algorithm(alg, G, s)
                valid = is_valid_solution(D, G, s, k)
                happiness = calculate_happiness(D, G) if valid else 0

                results.append({
                    'Input': basename,
                    'Algorithm': alg,
                    'Happiness': round(happiness, 2),
                    'Rooms': k,
                    'Valid': 'Yes' if valid else 'No',
                    'Time': f"{elapsed:.3f}s"
                })

                totals[alg]['happiness'] += happiness
                totals[alg]['time'] += elapsed
                totals[alg]['valid'] += 1 if valid else 0
                totals[alg]['count'] += 1

            except Exception as e:
                results.append({
                    'Input': basename,
                    'Algorithm': alg,
                    'Happiness': 'ERROR',
                    'Rooms': '-',
                    'Valid': 'No',
                    'Time': '-'
                })
                print(f"Error processing {basename} with {alg}: {e}")

    # Print results table
    print(tabulate(results, headers='keys', tablefmt='grid'))
    print()

    # Print summary
    print("=== Summary ===")
    summary = []
    for alg in algorithms:
        t = totals[alg]
        if t['count'] > 0:
            summary.append({
                'Algorithm': ALGORITHMS[alg][0],
                'Avg Happiness': round(t['happiness'] / t['count'], 2),
                'Valid Rate': f"{t['valid']}/{t['count']}",
                'Avg Time': f"{t['time'] / t['count']:.3f}s"
            })
    print(tabulate(summary, headers='keys', tablefmt='grid'))


def validate_outputs(data_dir):
    """Validate all output files in a data directory."""
    results = []
    sizes = ['small', 'medium', 'large']

    for size in sizes:
        input_dir = os.path.join(data_dir, size, 'inputs')
        output_dir = os.path.join(data_dir, size, 'outputs')

        if not os.path.exists(input_dir) or not os.path.exists(output_dir):
            continue

        for input_file in glob.glob(os.path.join(input_dir, "*.in")):
            basename = os.path.basename(input_file).replace('.in', '.out')
            output_file = os.path.join(output_dir, basename)

            if not os.path.exists(output_file):
                results.append({
                    'Size': size,
                    'File': basename,
                    'Valid': 'Missing',
                    'Happiness': '-'
                })
                continue

            try:
                G, s = parse.read_input_file(input_file)
                D = parse.read_output_file(output_file, G, s)
                k = len(set(D.values()))
                valid = is_valid_solution(D, G, s, k)
                happiness = calculate_happiness(D, G)

                results.append({
                    'Size': size,
                    'File': basename,
                    'Valid': 'Yes' if valid else 'No',
                    'Happiness': round(happiness, 2)
                })
            except Exception as e:
                results.append({
                    'Size': size,
                    'File': basename,
                    'Valid': f'Error: {str(e)[:30]}',
                    'Happiness': '-'
                })

    print(tabulate(results, headers='keys', tablefmt='grid'))

    # Summary
    valid_count = sum(1 for r in results if r['Valid'] == 'Yes')
    print(f"\nValid: {valid_count}/{len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description='Breakout Room Optimizer - Unified CLI Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --algorithm sim_annealing --input data/small/inputs/small-1.in
  python run.py --algorithm greedy --input data/small/inputs/small-1.in --output result.out
  python run.py --benchmark --size small
  python run.py --benchmark --size medium --algorithms sim_annealing,greedy
  python run.py --validate data/
        """
    )

    parser.add_argument('--algorithm', '-a', choices=list(ALGORITHMS.keys()),
                        help='Algorithm to use (sim_annealing, greedy, genetic)')
    parser.add_argument('--input', '-i', help='Input file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--benchmark', '-b', action='store_true',
                        help='Run benchmark mode')
    parser.add_argument('--size', '-s', choices=['small', 'medium', 'large'],
                        help='Size category for benchmark')
    parser.add_argument('--algorithms', help='Comma-separated list of algorithms for benchmark')
    parser.add_argument('--validate', '-v', metavar='DIR',
                        help='Validate all outputs in directory')

    args = parser.parse_args()

    if args.validate:
        validate_outputs(args.validate)
    elif args.benchmark:
        if not args.size:
            parser.error("--benchmark requires --size")
        algorithms = args.algorithms.split(',') if args.algorithms else None
        benchmark(args.size, algorithms)
    elif args.algorithm and args.input:
        result = process_single_file(args.input, args.algorithm, args.output)
        print(tabulate([result], headers='keys', tablefmt='grid'))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
