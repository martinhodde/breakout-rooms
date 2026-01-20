# Breakout Room Optimizer

Optimize student assignments to Zoom breakout rooms by maximizing happiness while respecting stress constraints.

## Problem

Given n students, assign them to k breakout rooms such that:
- **Maximize** total happiness H<sub>total</sub> across all rooms
- **Constraint**: Each room's stress ≤ S<sub>max</sub>/k

For each student pair (i,j):
- h<sub>ij</sub> = happiness value when together
- s<sub>ij</sub> = stress value when together

## Algorithms

Three optimization approaches are implemented:

| Algorithm | Description | Performance |
|-----------|-------------|-------------|
| **Simulated Annealing** | Greedy initialization + SA with geometric cooling | Best overall (66% win rate) |
| **Greedy + Local Search** | Greedy construction with iterative swaps | Fastest (7ms avg) |
| **Genetic Algorithm** | Evolutionary approach with crossover/mutation | Good exploration |

## Usage

### Run single file
```bash
python run.py --algorithm sim_annealing --input data/small/inputs/small-001.in
```

Available algorithms: `sim_annealing`, `greedy`, `genetic`

### Benchmark all algorithms
```bash
python benchmark.py --sizes small medium large
```

Options:
- `--sizes`: Which size categories to test
- `--max-files N`: Limit files per category
- `--no-save`: Don't save output files

### Validate outputs
```bash
python run.py --validate data/
```

## Data Organization

```
data/
  small/      242 files (10 students, n ≤ 20)
  medium/     240 files (20 students, 20 < n ≤ 50)
  large/      236 files (50 students, n > 50)
```

Files use 3-digit numbering: `{size}-{001-242}.{in,out}`

## Results

Benchmark on 180 files (65 small, 63 medium, 52 large):

| Algorithm | Avg Happiness | Win Rate | Avg Time |
|-----------|---------------|----------|----------|
| **SA** | **1397.82** | **66.1%** | 18.2s |
| Greedy | 1351.16 | 17.8% | 0.8s |
| Genetic | 1335.31 | 16.1% | 8.8s |
