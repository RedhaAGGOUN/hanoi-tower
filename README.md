# Tower of Hanoi Interactive Application

## Project Overview

An immersive implementation of the classic Tower of Hanoi puzzle, blending a terminal-based solver, a graphical interface, animations, and drag-and-drop interaction. Originally inspired by a virtual journey through Vietnam, this project demonstrates recursive algorithms in practice and showcases Python programming skills using modular design, sound feedback, and persistent scorekeeping.

## Repository Structure

The repository follows a clear module-based organization reflecting the actual code files:

```
hanoi-tower/
├─ assets/
│   ├─ images/           # Disk and peg visuals
│   ├─ sounds/           # Audio feedback for moves and errors
│   └─ fonts/            # Font files for UI text
├─ solve.py             # Recursive solver implementation
├─ utils.py             # Utility functions (e.g., input parsing, time formatting)
├─ graphics.py          # Pygame-based GUI engine: rendering, event loop, animations
├─ main.py              # Entry point: argument parsing, mode dispatch (CLI vs GUI)
├─ scoreboard.json      # Persistent top-scores by disk count and time
└─ README.md            # This detailed documentation
```

## Deep Dive: Recursive Solver (solve.py)

At the heart of this application lies a succinct recursive function:

```python
# solve.py
def hanoi_solver(n, source, target, auxiliary, moves=None):
    """
    Generate the minimal list of moves to solve Tower of Hanoi.
    Parameters:
    - n (int): number of disks
    - source (str): label of the starting peg
    - target (str): label of the destination peg
    - auxiliary (str): label of the helper peg
    - moves (list): accumulator for move tuples
    Returns:
    - list of tuples: [(from_peg, to_peg), ...]
    """
    if moves is None:
        moves = []
    # Base case: move single disk directly
    if n == 1:
        moves.append((source, target))
    else:
        # Step 1: move n-1 disks from source to auxiliary
        hanoi_solver(n-1, source, auxiliary, target, moves)
        # Step 2: move the largest disk to target
        moves.append((source, target))
        # Step 3: move n-1 disks from auxiliary to target
        hanoi_solver(n-1, auxiliary, target, source, moves)
    return moves
```

### Translating Theory to Code

1. **Recursive Principle**: Any instance of size *n* reduces to three operations:
   - Solve *n-1* disks to the auxiliary peg
   - Move the nth disk to the target peg
   - Solve *n-1* disks from auxiliary to target

2. **Accumulator Pattern**: A shared `moves` list collects the ordered moves, avoiding list concatenation overhead.

3. **Base Case**: When `n == 1`, the function performs a direct move, anchoring the recursion.

4. **Function Signature**: The parameters mirror theoretical labels (`source`, `target`, `auxiliary`), promoting clarity and maintainability.

## Utility Module (utils.py)

- **parse_args(arg_str)**: Parses the CLI string `"n,m"` into integer values, validating ranges.
- **format_time(seconds)**: Converts elapsed seconds into `HH:MM:SS` format for display.
- **load_scores(path)** / **save_scores(path, data)**: JSON serialization of the `scoreboard.json` file.

## Graphical Interface (graphics.py)

- **Game Loop**: Initializes Pygame, loads assets, and enters an event-driven loop handling:
  - Drag-and-drop of disks
  - Automatic solution playback with tweened animations
  - Real-time move and timer updates

- **Visual Feedback**:
  - Valid moves highlight in green; invalid in red
  - Disk sprites scale according to size and stack order

- **Audio Feedback**:
  - Separate WAV files for pick-up, drop, error, and victory cues

- **Score Persistence**:
  - On victory, compares current moves/time against `scoreboard.json`, updates if improved

## Entry Point (main.py)

Handles:

1. **Argument Parsing** with `argparse`:
   - `"n,m"` positional
   - `--mode` flag: `terminal` or `gui` (default)

2. **Mode Dispatch**:
   - **Terminal Mode**: Calls `hanoi_solver` and prints moves line-by-line
   - **GUI Mode**: Instantiates `GraphicsEngine(n_disks, n_pegs)`, launches Pygame window

## Installation & Requirements

```bash
pip install pygame
```

Tested on Python 3.10+ under Windows, macOS, and Linux.

## Usage Examples

**Terminal Solver**
```bash
python main.py "5,3" --mode terminal
```
**Graphical Mode**
```bash
python main.py "7,4"
```

## Contribution Guidelines

- Fork the repository and submit PRs against `develop` branch
- Follow PEP8; run `flake8` before committing
- Write docstrings for all new functions

---
*Enjoy exploring recursion and the art of algorithmic puzzles!*
