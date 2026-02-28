# Dynamic-Pathfinding-Agent

## 🖥️ What It Looks Like

> Dark theme, neon colours, scrollable control panel, live animation of search

---

## 🚀 Quick Start

```bash
# 1. Install dependency
pip install pygame

# or use requirements file:
pip install -r requirements.txt

# 2. Run
python main.py
```

> Requires **Python 3.8+**

---

## 🎮 Controls

| Action | How |
|--------|-----|
| Draw walls | Click `▪ Draw Wall` then left-click / drag on grid |
| Erase walls | Click `✕ Erase` or **right-click** any cell |
| Place Start | Click `📍 Set Start` then click a cell |
| Place Target | Click `🎯 Set Target` then click a cell |
| Run search | Click `▶ RUN SEARCH` or press **Enter / Space** |
| Stop | Click `■ STOP` or press **Escape** |
| Random map | Click `🗺 Random Map` or press **R** |
| Clear path | Click `✦ Clear Path` or press **C** |
| Erase cell | **Right-click** on any grid cell |

---

## 🧠 Algorithms

### A* Search
```
f(n) = g(n) + h(n)
```
- Uses both actual cost `g(n)` and estimated remaining cost `h(n)`
- Guaranteed to find the **optimal (shortest) path**
- Uses an **expanded list** — allows re-opening nodes via cheaper paths

### Greedy Best-First Search (GBFS)
```
f(n) = h(n)
```
- Only looks at estimated distance — ignores actual cost so far
- Faster but **not optimal** — may find longer paths
- Uses a **strict visited list** — never revisits a node

---

## 📐 Heuristics

| Name | Formula | Best for |
|------|---------|----------|
| **Manhattan** | `\|dx\| + \|dy\|` | 4-directional grids |
| **Euclidean** | `√(dx²+dy²)` | Diagonal / free movement |
| **Chebyshev** | `max(\|dx\|,\|dy\|)` | 8-directional grids |
| **Octile** | `max+0.414×min` | 8-directional (admissible) |

---

## 🎨 Colour Legend

| Colour | Meaning |
|--------|---------|
| 🟢 Neon Mint | Start Node (S) |
| 🔵 Sky Blue | Target Node (T) |
| 🔴 Hot Pink | Wall / Obstacle |
| 🟡 Amber | Frontier (open list, not yet expanded) |
| 🔵 Deep Blue | Visited / Expanded (closed set) |
| 🟣 Lavender | Final path |
| 🟠 Orange | Agent current position |

---

## ⚡ Dynamic Re-planning Mode

1. Run a search first to find a path
2. Check **"Enable Dynamic Obstacles"** in the panel
3. Adjust **Spawn prob %** to control how often new walls appear
4. Click **▶ RUN SEARCH** again
5. Watch the agent walk — new obstacles appear randomly, and if one blocks the path, the agent **immediately re-plans from its current position**

---

## 📊 Metrics Panel

| Metric | Meaning |
|--------|---------|
| Nodes Visited | How many cells were expanded (lower = more efficient) |
| Path Cost | Total step cost of the final path (diagonals cost 1.414) |
| Time (ms) | Execution time in milliseconds |
| Re-plans | Number of times agent had to re-plan due to obstacles |

## 🔧 Customisation

At the top of `main.py`, you can change:

```python
DEFAULT_ROWS    = 18      # number of grid rows
DEFAULT_COLS    = 22      # number of grid columns
CELL_SIZE       = 36      # pixel size of each cell
ANIMATION_DELAY = 0.025   # default animation delay (seconds)
```

## ✅ Requirements Checklist

- [x] Dynamic grid sizing (Rows × Cols via spinbox)
- [x] Fixed Start & Goal (user-defined, visually clear)
- [x] Random map generation with user-defined density
- [x] Interactive map editor (click/drag walls, erase)
- [x] No static .txt map files used
- [x] Greedy Best-First Search (GBFS) — f(n) = h(n)
- [x] A* Search — f(n) = g(n) + h(n)
- [x] Manhattan Distance heuristic
- [x] Euclidean Distance heuristic
- [x] GUI toggle between heuristics and algorithms
- [x] Dynamic obstacle spawning while agent is moving
- [x] Re-planning mechanism when path is blocked
- [x] Avoids full reset — only re-plans from current position
- [x] Frontier nodes highlighted (Yellow/Amber)
- [x] Visited nodes highlighted (Deep Blue)
- [x] Final path highlighted (Lavender/Purple)
- [x] Nodes Visited counter
- [x] Path Cost display
- [x] Execution Time (ms) display

---

*Submitted by Ahmad Shakeel for AI 2002 Artificial Intelligence, Spring 2026*

