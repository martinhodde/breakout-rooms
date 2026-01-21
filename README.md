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
| **Simulated Annealing** | Greedy init + SA with geometric cooling | Best overall (44.4% win rate) |
| **Greedy + Local Search** | Greedy construction with iterative swaps | Balanced performance (31.1% win rate) |
| **Genetic Algorithm** | Evolutionary approach with crossover/mutation | High quality on select instances |

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
| **Simulated Annealing** | **1534.24** | **44.4%** | **32.3s** |
| **Genetic** | 1638.19 | 24.4% | 813.2s |
| **Greedy** | 1615.20 | 31.1% | 80.7s |

**By Size:**
- **Small** (n ≤ 20): SA dominates (86.7% win rate, 26/30 wins), Greedy 0 wins
- **Medium** (20 < n ≤ 50): Three-way tie (all algorithms win 10/30)
- **Large** (n > 50): Greedy best (18/30 wins), SA competitive (4/30 wins)

**Key Takeaway:** Simulated Annealing achieves the best overall win rate at 44.4% while maintaining excellent speed (25× faster than Genetic). It completely dominates small instances and remains competitive on larger ones.
