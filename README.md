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
| **Greedy + Local Search** | Greedy construction with iterative swaps | Best overall (44% win rate) |
| **Simulated Annealing** | Greedy init + SA with geometric cooling | Fastest (0.13s avg) |
| **Genetic Algorithm** | Evolutionary approach with crossover/mutation | Highest quality solutions |

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

Benchmark on 90 files (30 small, 30 medium, 30 large):

| Algorithm | Avg Happiness | Win Rate | Total Time |
|-----------|---------------|----------|------------|
| **Greedy** | **1644.06** | **43.3%** | 82.9s |
| **Genetic** | 1628.74 | 22.2% | 857.7s |
| **Simulated Annealing** | 1568.28 | 34.4% | **23.0s** |

**By Size:**
- **Small** (n ≤ 20): SA dominates (63% win rate), 7.5× faster than Genetic
- **Medium** (20 < n ≤ 50): Genetic slightly ahead in quality, Greedy/SA competitive
- **Large** (n > 50): Greedy best (73% win rate), SA 4.6× faster than Greedy

**Key Takeaway:** Greedy achieves the best overall balance. Simulated Annealing offers the best speed-to-quality ratio, especially strong on small instances.
