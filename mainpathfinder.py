import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import random
import time
import math

# ─────────────────────────────────────────────
#  GLOBAL CONFIGURATION
# ─────────────────────────────────────────────
DEFAULT_ROWS    = 18
DEFAULT_COLS    = 22
CELL_SIZE       = 36
ANIMATION_DELAY = 0.025   # seconds between steps

BG_DEEP     = "#0d0f18"   # deepest background
BG_BASE     = "#11131f"   # main background
BG_MANTLE   = "#181a2a"   # panel background
BG_SURFACE0 = "#1e2035"   # card / box background
BG_SURFACE1 = "#252840"   # slightly lighter surface
BG_OVERLAY  = "#2e3150"   # overlay elements

TEXT_MAIN   = "#e2e8ff"   # primary text
TEXT_DIM    = "#6b7280"   # secondary / label text
TEXT_FAINT  = "#3d4263"   # very faint text

# Cell colours — NEON theme
C_EMPTY     = "#0f1120"   # empty cell
C_GRID      = "#1a1d32"   # grid lines
C_OBSTACLE  = "#e05c7a"   # wall  — hot pink/red
C_START     = "#00e5a0"   # start — neon mint
C_TARGET    = "#00b4ff"   # target— neon sky blue
C_VISITED   = "#1f3a5c"   # visited — deep ocean blue
C_FRONTIER  = "#e8a820"   # frontier — amber
C_PATH      = "#bf7fff"   # path — neon lavender
C_AGENT     = "#ff6b35"   # agent — neon orange

# Accent colours for UI
ACCENT_CYAN  = "#00e5ff"
ACCENT_PINK  = "#ff4f82"
ACCENT_GREEN = "#00e5a0"
ACCENT_AMBER = "#ffb340"
ACCENT_PURP  = "#bf7fff"

# Button themes
BTN_PRIMARY  = "#1a2a4a"
BTN_SUCCESS  = "#0d3326"
BTN_DANGER   = "#3a1120"
BTN_NEUTRAL  = "#1a1d32"

# Movement directions (8-directional)
MOVES = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1,-1), (-1, 1), (1,-1), (1, 1),
]
DIAGONAL_MOVES = {(-1,-1),(-1,1),(1,-1),(1,1)}


# ─────────────────────────────────────────────
#  NODE CLASS
# ─────────────────────────────────────────────
class Node:
    """Represents one cell during search."""
    def __init__(self, r, c, parent=None, g=0, h=0):
        self.r = r;  self.c = c
        self.parent = parent
        self.g = g;  self.h = h
        self.f = g + h

    def pos(self):   return (self.r, self.c)
    def __lt__(self, other): return self.f < other.f
    def __eq__(self, other): return self.pos() == other.pos()


# ─────────────────────────────────────────────
#  HEURISTICS
# ─────────────────────────────────────────────
def h_manhattan(r, c, gr, gc):
    return abs(r-gr) + abs(c-gc)

def h_euclidean(r, c, gr, gc):
    return math.hypot(r-gr, c-gc)

def h_chebyshev(r, c, gr, gc):
    return max(abs(r-gr), abs(c-gc))

def h_octile(r, c, gr, gc):
    """Best admissible heuristic for 8-directional movement."""
    dx = abs(r - gr);  dy = abs(c - gc)
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class DynamicPathfinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(" Dynamic pathfinding agent (Informed searches)")
        self.root.configure(bg=BG_DEEP)
        self.root.resizable(False, False)

        self.rows = DEFAULT_ROWS
        self.cols = DEFAULT_COLS

        # State
        self.grid         = []
        self.rects        = {}
        self.start_pos    = None
        self.target_pos   = None
        self.mode         = "Wall"
        self.running      = False
        self.current_path = []
        self.agent_pos    = None

        # Metrics
        self.nodes_visited = 0
        self.path_cost     = 0.0
        self.exec_time_ms  = 0.0
        self.replans       = 0

        # Search steps log for step-by-step animation
        self.search_log    = []   # list of (type, r, c)  — "v"=visited "f"=frontier

        self._build_ui()
        self._init_grid()
        self._place_defaults()

    # ──────────────────────────────────────────
    #  DEFAULT START / TARGET PLACEMENT
    # ──────────────────────────────────────────
    def _place_defaults(self):
        """Place start top-left, target bottom-right automatically."""
        self.start_pos  = (1, 1)
        self.target_pos = (self.rows-2, self.cols-2)
        self._paint(1, 1, C_START, "S")
        self._paint(self.rows-2, self.cols-2, C_TARGET, "T")

    # ──────────────────────────────────────────
    #  UI CONSTRUCTION
    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── TOP HEADER BAR ────────────────────────────────
        header = tk.Frame(self.root, bg=BG_MANTLE, pady=10)
        header.pack(fill=tk.X)

        tk.Label(header, text="⬡  DYNAMIC PATHFINDING AGENT",
                 bg=BG_MANTLE, fg=ACCENT_CYAN,
                 font=("Consolas", 16, "bold")).pack(side=tk.LEFT, padx=18)

        tk.Label(header, text="AI 2002  |  NUCES Faisalabad  |  Spring 2026 | Ahmad Shakeel ",
                 bg=BG_MANTLE, fg=TEXT_DIM,
                 font=("Consolas", 9)).pack(side=tk.LEFT, padx=4)

        # Version / status badge on right
        self.header_status = tk.Label(header, text="◉  READY",
                                       bg=BG_MANTLE, fg=ACCENT_GREEN,
                                       font=("Consolas", 10, "bold"))
        self.header_status.pack(side=tk.RIGHT, padx=18)

        # ── MAIN BODY ─────────────────────────────────────
        body = tk.Frame(self.root, bg=BG_DEEP)
        body.pack(fill=tk.BOTH, expand=True)

        # ── LEFT: Canvas ──────────────────────────────────
        canvas_wrap = tk.Frame(body, bg=BG_DEEP, padx=12, pady=10)
        canvas_wrap.pack(side=tk.LEFT, fill=tk.BOTH)

        # Canvas border glow effect (outer frame)
        glow = tk.Frame(canvas_wrap, bg=ACCENT_CYAN, padx=1, pady=1)
        glow.pack()

        inner = tk.Frame(glow, bg=BG_BASE)
        inner.pack(padx=1, pady=1)

        self.canvas = tk.Canvas(inner, bg=C_EMPTY, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<Button-1>",  self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-3>",  self._on_right_click)

        # ── RIGHT PANEL ───────────────────────────────────
        panel_outer = tk.Frame(body, bg=BG_MANTLE, width=290)
        panel_outer.pack(side=tk.RIGHT, fill=tk.Y)
        panel_outer.pack_propagate(False)

        # Scrollable inner panel
        pcanvas = tk.Canvas(panel_outer, bg=BG_MANTLE, highlightthickness=0, width=290)
        vsb = tk.Scrollbar(panel_outer, orient="vertical", command=pcanvas.yview)
        pcanvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        pcanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.panel = tk.Frame(pcanvas, bg=BG_MANTLE, width=270)
        win = pcanvas.create_window((0,0), window=self.panel, anchor="nw")

        self.panel.bind("<Configure>",
                        lambda e: pcanvas.configure(scrollregion=pcanvas.bbox("all")))
        pcanvas.bind_all("<MouseWheel>",
                         lambda e: pcanvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_panel()

    # ──────────────────────────────────────────
    #  PANEL CONTENTS
    # ──────────────────────────────────────────
    def _build_panel(self):
        p = self.panel

        def gap(h=6):
            tk.Frame(p, bg=BG_MANTLE, height=h).pack(fill=tk.X)

        def divider(color=BG_OVERLAY):
            tk.Frame(p, bg=color, height=1).pack(fill=tk.X, padx=10, pady=4)

        def sec_label(txt, color=ACCENT_CYAN):
            row = tk.Frame(p, bg=BG_MANTLE)
            row.pack(fill=tk.X, padx=12, pady=(10,2))
            tk.Label(row, text="▸ " + txt, bg=BG_MANTLE, fg=color,
                     font=("Consolas", 9, "bold")).pack(side=tk.LEFT)

        def card(parent=None):
            if parent is None: parent = p
            f = tk.Frame(parent, bg=BG_SURFACE0,
                         highlightbackground=BG_OVERLAY,
                         highlightthickness=1)
            f.pack(fill=tk.X, padx=10, pady=3)
            return f

        def neon_btn(txt, cmd, bg=BTN_PRIMARY, fg=TEXT_MAIN,
                     accent=ACCENT_CYAN, bold=False, pad=7):
            font = ("Consolas", 10, "bold") if bold else ("Consolas", 10)
            frame = tk.Frame(p, bg=accent, padx=1, pady=1)
            frame.pack(fill=tk.X, padx=10, pady=2)
            b = tk.Button(frame, text=txt, command=cmd,
                          bg=bg, fg=fg, font=font,
                          relief="flat", activebackground=BG_OVERLAY,
                          activeforeground=fg, cursor="hand2", pady=pad,
                          borderwidth=0)
            b.pack(fill=tk.X)
            return b

        def small_btn(parent, txt, cmd, bg=BTN_NEUTRAL, fg=TEXT_MAIN, accent=BG_OVERLAY):
            frame = tk.Frame(parent, bg=accent, padx=1, pady=1)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            b = tk.Button(frame, text=txt, command=cmd, bg=bg, fg=fg,
                          font=("Consolas", 9), relief="flat", cursor="hand2",
                          pady=4, borderwidth=0,
                          activebackground=BG_OVERLAY, activeforeground=fg)
            b.pack(fill=tk.X)
            return b

        # ── TITLE CARD ─────────────────────────────────
        gap(8)
        title_card = tk.Frame(p, bg=BG_SURFACE1,
                               highlightbackground=ACCENT_PURP, highlightthickness=1)
        title_card.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(title_card, text="PATHFINDING AGENT",
                 bg=BG_SURFACE1, fg=ACCENT_PURP,
                 font=("Consolas", 13, "bold")).pack(pady=(8,0))
        tk.Label(title_card, text="Informed Search  •  Dynamic Re-planning",
                 bg=BG_SURFACE1, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(pady=(0,8))

        # ── PRIMARY ACTIONS ────────────────────────────
        gap(4)
        neon_btn("   RUN SEARCH", self._start_search,
                 bg=BTN_SUCCESS, fg=ACCENT_GREEN,
                 accent=ACCENT_GREEN, bold=True, pad=10)
        neon_btn("   STOP", self._stop_search,
                 bg=BTN_DANGER, fg=ACCENT_PINK,
                 accent=ACCENT_PINK, pad=6)

        divider(ACCENT_PURP)

        # ── ALGORITHM ─────────────────────────────────
        sec_label("ALGORITHM", ACCENT_PURP)
        c = card()
        tk.Label(c, text="Strategy", bg=BG_SURFACE0, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", padx=8, pady=(6,0))
        self.algo_var = tk.StringVar(value="A*")
        algo_cb = ttk.Combobox(c, textvariable=self.algo_var,
                               values=["A*", "Greedy Best-First (GBFS)"],
                               state="readonly", font=("Consolas", 10))
        algo_cb.pack(fill=tk.X, padx=8, pady=(2,6))
        self._style_combo(algo_cb)

        tk.Label(c, text="Heuristic", bg=BG_SURFACE0, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", padx=8)
        self.heuristic_var = tk.StringVar(value="Manhattan")
        h_cb = ttk.Combobox(c, textvariable=self.heuristic_var,
                             values=["Manhattan", "Euclidean", "Chebyshev", "Octile"],
                             state="readonly", font=("Consolas", 10))
        h_cb.pack(fill=tk.X, padx=8, pady=(2,8))
        self._style_combo(h_cb)

        divider()

        # ── EDIT MODE ─────────────────────────────────
        sec_label("EDITOR MODE", ACCENT_AMBER)
        self.mode_btns = {}
        modes = [
            ("  Set Start",  "S",    ACCENT_GREEN, BTN_SUCCESS),
            ("  Set Target", "T",    ACCENT_CYAN,  BTN_PRIMARY),
            ("   Draw Wall",  "Wall", ACCENT_PINK,  BTN_DANGER),
            ("  Erase",      "Erase",TEXT_MAIN,    BTN_NEUTRAL),
        ]
        row1 = tk.Frame(p, bg=BG_MANTLE); row1.pack(fill=tk.X, padx=10, pady=2)
        row2 = tk.Frame(p, bg=BG_MANTLE); row2.pack(fill=tk.X, padx=10, pady=2)

        for i, (lbl, mode, fg, bg) in enumerate(modes):
            parent_row = row1 if i < 2 else row2
            b = small_btn(parent_row, lbl, lambda m=mode: self._set_mode(m),
                          bg=bg, fg=fg, accent=fg)
            self.mode_btns[mode] = b

        divider()

        # ── GRID CONFIG ────────────────────────────────
        sec_label("GRID CONFIG", TEXT_DIM)
        gc = card()

        size_row = tk.Frame(gc, bg=BG_SURFACE0)
        size_row.pack(fill=tk.X, padx=8, pady=(6,4))
        for lbl, var_name, default in [("Rows", "rows_var", DEFAULT_ROWS),
                                        ("Cols", "cols_var", DEFAULT_COLS)]:
            col = tk.Frame(size_row, bg=BG_SURFACE0)
            col.pack(side=tk.LEFT, expand=True)
            tk.Label(col, text=lbl, bg=BG_SURFACE0, fg=TEXT_DIM,
                     font=("Consolas", 8)).pack()
            var = tk.IntVar(value=default)
            setattr(self, var_name, var)
            sb = tk.Spinbox(col, from_=5, to=30, textvariable=var,
                            width=5, font=("Consolas", 10),
                            bg=BG_SURFACE1, fg=TEXT_MAIN,
                            buttonbackground=BG_OVERLAY, relief="flat",
                            highlightthickness=0)
            sb.pack(padx=4)

        apply_row = tk.Frame(gc, bg=BG_SURFACE0)
        apply_row.pack(fill=tk.X, padx=8, pady=(0,4))
        small_btn(apply_row, "Apply Size", self._apply_grid_size,
                  bg=BTN_NEUTRAL, fg=ACCENT_CYAN, accent=ACCENT_CYAN)

        # Wall density
        dens_card = card()
        dens_inner = tk.Frame(dens_card, bg=BG_SURFACE0)
        dens_inner.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(dens_inner, text="Wall Density %", bg=BG_SURFACE0,
                 fg=TEXT_DIM, font=("Consolas", 8)).pack(side=tk.LEFT)
        self.density_var = tk.IntVar(value=28)
        tk.Spinbox(dens_inner, from_=0, to=70, textvariable=self.density_var,
                   width=4, font=("Consolas", 10), bg=BG_SURFACE1,
                   fg=TEXT_MAIN, buttonbackground=BG_OVERLAY,
                   relief="flat", highlightthickness=0).pack(side=tk.RIGHT)

        maze_row = tk.Frame(p, bg=BG_MANTLE)
        maze_row.pack(fill=tk.X, padx=10, pady=2)
        small_btn(maze_row, "  Random Map", self._generate_random_map,
                  bg=BTN_NEUTRAL, fg=ACCENT_AMBER, accent=ACCENT_AMBER)
        small_btn(maze_row, "  Clear Walls", self._clear_walls,
                  bg=BTN_NEUTRAL, fg=TEXT_DIM, accent=BG_OVERLAY)

        ctrl_row = tk.Frame(p, bg=BG_MANTLE)
        ctrl_row.pack(fill=tk.X, padx=10, pady=2)
        small_btn(ctrl_row, "  Clear Path", self._clear_path,
                  bg=BTN_NEUTRAL, fg=ACCENT_PURP, accent=ACCENT_PURP)
        small_btn(ctrl_row, " Reset All", self._reset_grid,
                  bg=BTN_DANGER, fg=ACCENT_PINK, accent=ACCENT_PINK)

        divider()

        # ── DYNAMIC MODE ───────────────────────────────
        sec_label("DYNAMIC MODE", ACCENT_PINK)
        dyn_card = card()

        self.dynamic_var = tk.BooleanVar(value=False)
        dyn_toggle = tk.Checkbutton(
            dyn_card, text="  Enable Dynamic Obstacles",
            variable=self.dynamic_var,
            bg=BG_SURFACE0, fg=ACCENT_PINK, selectcolor=BG_SURFACE1,
            activebackground=BG_SURFACE0, activeforeground=ACCENT_PINK,
            font=("Consolas", 9, "bold"),
            indicatoron=True
        )
        dyn_toggle.pack(anchor="w", padx=8, pady=(6,2))

        prob_row = tk.Frame(dyn_card, bg=BG_SURFACE0)
        prob_row.pack(fill=tk.X, padx=8, pady=(0,6))
        tk.Label(prob_row, text="Spawn prob %", bg=BG_SURFACE0,
                 fg=TEXT_DIM, font=("Consolas", 8)).pack(side=tk.LEFT)
        self.spawn_prob_var = tk.IntVar(value=12)
        tk.Spinbox(prob_row, from_=1, to=60, textvariable=self.spawn_prob_var,
                   width=4, font=("Consolas", 10),
                   bg=BG_SURFACE1, fg=TEXT_MAIN,
                   buttonbackground=BG_OVERLAY, relief="flat",
                   highlightthickness=0).pack(side=tk.RIGHT)

        divider()

        # ── ANIMATION SPEED ────────────────────────────
        sec_label("ANIMATION", TEXT_DIM)
        spd_card = card()
        spd_row = tk.Frame(spd_card, bg=BG_SURFACE0)
        spd_row.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(spd_row, text="Delay (ms)", bg=BG_SURFACE0,
                 fg=TEXT_DIM, font=("Consolas", 8)).pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=25)
        tk.Scale(spd_row, from_=5, to=200, orient="horizontal",
                 variable=self.speed_var, bg=BG_SURFACE0,
                 fg=TEXT_DIM, troughcolor=BG_OVERLAY, sliderrelief="flat",
                 highlightthickness=0, length=120,
                 activebackground=ACCENT_PURP).pack(side=tk.RIGHT)

        divider()

        # ── METRICS DASHBOARD ──────────────────────────
        sec_label("METRICS", ACCENT_GREEN)
        m_card = tk.Frame(p, bg=BG_SURFACE0,
                          highlightbackground=ACCENT_GREEN, highlightthickness=1)
        m_card.pack(fill=tk.X, padx=10, pady=4)

        self.metric_labels = {}
        rows_data = [
            ("algo",      "Algorithm",     ACCENT_PURP),
            ("heuristic", "Heuristic",     ACCENT_CYAN),
            ("visited",   "Nodes Visited", ACCENT_AMBER),
            ("cost",      "Path Cost",     ACCENT_GREEN),
            ("time",      "Time (ms)",     TEXT_MAIN),
            ("replans",   "Re-plans",      ACCENT_PINK),
        ]
        for key, label, fg_c in rows_data:
            row = tk.Frame(m_card, bg=BG_SURFACE0)
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=label, bg=BG_SURFACE0, fg=TEXT_DIM,
                     font=("Consolas", 8), width=14, anchor="w").pack(side=tk.LEFT)
            val = tk.Label(row, text="—", bg=BG_SURFACE0, fg=fg_c,
                           font=("Consolas", 9, "bold"), anchor="w")
            val.pack(side=tk.LEFT)
            self.metric_labels[key] = val

        gap(6)

        # ── STATUS ─────────────────────────────────────
        self.status_lbl = tk.Label(p, text="◉  Ready — Set S and T, then Run",
                                    bg=BG_MANTLE, fg=ACCENT_GREEN,
                                    font=("Consolas", 9, "bold"),
                                    wraplength=260, justify="left")
        self.status_lbl.pack(anchor="w", padx=12, pady=4)

        divider(ACCENT_PURP)

        # ── LEGEND ─────────────────────────────────────
        sec_label("LEGEND", TEXT_DIM)
        legends = [
            (C_START,    "Start Node (S)"),
            (C_TARGET,   "Target Node (T)"),
            (C_OBSTACLE, "Wall / Obstacle"),
            (C_FRONTIER, "Frontier (Open List)"),
            (C_VISITED,  "Visited (Closed)"),
            (C_PATH,     "Final Path"),
            (C_AGENT,    "Agent Position"),
        ]
        leg_card = card()
        for col, lbl in legends:
            lr = tk.Frame(leg_card, bg=BG_SURFACE0)
            lr.pack(fill=tk.X, padx=10, pady=2)
            dot = tk.Frame(lr, bg=col, width=14, height=14)
            dot.pack(side=tk.LEFT, padx=(0,8))
            dot.pack_propagate(False)
            tk.Label(lr, text=lbl, bg=BG_SURFACE0, fg=TEXT_MAIN,
                     font=("Consolas", 9)).pack(side=tk.LEFT)

        # ── KEYBOARD SHORTCUTS ─────────────────────────
        sec_label("SHORTCUTS", TEXT_DIM)
        shortcuts = [
            ("Enter / Space", "Run Search"),
            ("R",             "Random Map"),
            ("C",             "Clear Path"),
            ("Esc",           "Stop"),
            ("Right-click",   "Erase Cell"),
        ]
        sc_card = card()
        for key, desc in shortcuts:
            sr = tk.Frame(sc_card, bg=BG_SURFACE0)
            sr.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(sr, text=key, bg=BG_SURFACE0, fg=ACCENT_AMBER,
                     font=("Consolas", 8, "bold"), width=14, anchor="w").pack(side=tk.LEFT)
            tk.Label(sr, text=desc, bg=BG_SURFACE0, fg=TEXT_DIM,
                     font=("Consolas", 8), anchor="w").pack(side=tk.LEFT)

        gap(16)

        # ── KEYBOARD BINDINGS ──────────────────────────
        self.root.bind("<Return>",  lambda e: self._start_search())
        self.root.bind("<space>",   lambda e: self._start_search())
        self.root.bind("<Escape>",  lambda e: self._stop_search())
        self.root.bind("<r>",       lambda e: self._generate_random_map())
        self.root.bind("<c>",       lambda e: self._clear_path())

    # ──────────────────────────────────────────
    #  COMBOBOX STYLING
    # ──────────────────────────────────────────
    def _style_combo(self, cb):
        """Apply dark theme to a ttk Combobox."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=BG_SURFACE1,
                         background=BG_SURFACE1,
                         foreground=TEXT_MAIN,
                         arrowcolor=ACCENT_CYAN,
                         selectbackground=BG_OVERLAY,
                         selectforeground=TEXT_MAIN)
        cb.configure(style="TCombobox")

    # ──────────────────────────────────────────
    #  GRID INIT
    # ──────────────────────────────────────────
    def _init_grid(self):
        self.canvas.config(
            width  = self.cols * CELL_SIZE,
            height = self.rows * CELL_SIZE
        )
        self.canvas.delete("all")
        self.rects = {}
        self.grid  = [[0]*self.cols for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * CELL_SIZE;  y1 = r * CELL_SIZE
                rect = self.canvas.create_rectangle(
                    x1+1, y1+1, x1+CELL_SIZE-1, y1+CELL_SIZE-1,
                    fill=C_EMPTY, outline=C_GRID, width=1
                )
                self.rects[(r, c)] = rect

        # Draw coordinate tick marks every 5 cells
        for c in range(0, self.cols, 5):
            x = c * CELL_SIZE + 2
            self.canvas.create_text(x, 3, text=str(c),
                                     fill=TEXT_FAINT, font=("Consolas", 7), anchor="nw")
        for r in range(0, self.rows, 5):
            y = r * CELL_SIZE + 2
            self.canvas.create_text(2, y, text=str(r),
                                     fill=TEXT_FAINT, font=("Consolas", 7), anchor="nw")

    def _apply_grid_size(self):
        self.rows = self.rows_var.get()
        self.cols = self.cols_var.get()
        self.start_pos  = None
        self.target_pos = None
        self._init_grid()
        self._place_defaults()
        self._set_status("Grid resized.", ACCENT_CYAN)

    # ──────────────────────────────────────────
    #  PAINTING
    # ──────────────────────────────────────────
    def _paint(self, r, c, color, text=""):
        rect = self.rects.get((r, c))
        if rect is None: return
        self.canvas.itemconfig(rect, fill=color, outline=C_GRID)

        # Remove old label on this cell
        tag = f"t{r}_{c}"
        self.canvas.delete(tag)

        if text:
            x = c * CELL_SIZE + CELL_SIZE // 2
            y = r * CELL_SIZE + CELL_SIZE // 2
            dark_bg = color in (C_START, C_TARGET, C_FRONTIER, C_PATH, C_AGENT)
            fg = BG_DEEP if dark_bg else "#cdd6f4"
            self.canvas.create_text(x, y, text=text, fill=fg,
                                     font=("Consolas", 9, "bold"), tag=tag)

    def _flash(self, r, c, color):
        """Paint with a bright outline (highlights the cell briefly)."""
        rect = self.rects.get((r, c))
        if rect is None: return
        self.canvas.itemconfig(rect, fill=color, outline=ACCENT_CYAN)
        self.root.after(120, lambda: self.canvas.itemconfig(rect, outline=C_GRID)
                        if self.rects.get((r, c)) else None)

    # ──────────────────────────────────────────
    #  METRICS + STATUS
    # ──────────────────────────────────────────
    def _update_metrics(self):
        self.metric_labels["algo"].config(text=self.algo_var.get())
        self.metric_labels["heuristic"].config(text=self.heuristic_var.get())
        self.metric_labels["visited"].config(text=f"{self.nodes_visited:,}")
        self.metric_labels["cost"].config(text=f"{self.path_cost:.1f}")
        self.metric_labels["time"].config(text=f"{self.exec_time_ms:.2f}")
        self.metric_labels["replans"].config(text=str(self.replans))

    def _set_status(self, msg, color=TEXT_MAIN):
        self.status_lbl.config(text=f"◉  {msg}", fg=color)
        self.header_status.config(text=f"◉  {msg.upper()[:25]}", fg=color)

    # ──────────────────────────────────────────
    #  MOUSE INTERACTION
    # ──────────────────────────────────────────
    def _set_mode(self, mode):
        self.mode = mode
        colors = {"S": ACCENT_GREEN, "T": ACCENT_CYAN,
                  "Wall": ACCENT_PINK, "Erase": TEXT_MAIN}
        self._set_status(f"Mode: {mode}", colors.get(mode, TEXT_MAIN))

    def _cell_from_event(self, event):
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None, None

    def _on_click(self, event):
        if self.running: return
        r, c = self._cell_from_event(event)
        if r is not None:
            self._handle_cell(r, c)

    def _on_drag(self, event):
        if self.running: return
        r, c = self._cell_from_event(event)
        if r is not None and self.mode in ("Wall", "Erase"):
            self._handle_cell(r, c)

    def _on_right_click(self, event):
        if self.running: return
        r, c = self._cell_from_event(event)
        if r is not None and (r,c) not in (self.start_pos, self.target_pos):
            self.grid[r][c] = 0
            self._paint(r, c, C_EMPTY)

    def _handle_cell(self, r, c):
        if self.mode == "S":
            if self.start_pos:
                self._paint(*self.start_pos, C_EMPTY)
                self.grid[self.start_pos[0]][self.start_pos[1]] = 0
            self.start_pos = (r, c)
            self.grid[r][c] = 0
            self._paint(r, c, C_START, "S")

        elif self.mode == "T":
            if self.target_pos:
                self._paint(*self.target_pos, C_EMPTY)
                self.grid[self.target_pos[0]][self.target_pos[1]] = 0
            self.target_pos = (r, c)
            self.grid[r][c] = 0
            self._paint(r, c, C_TARGET, "T")

        elif self.mode == "Wall":
            if (r,c) in (self.start_pos, self.target_pos): return
            self.grid[r][c] = -1
            self._paint(r, c, C_OBSTACLE)

        elif self.mode == "Erase":
            if (r,c) in (self.start_pos, self.target_pos): return
            self.grid[r][c] = 0
            self._paint(r, c, C_EMPTY)

    # ──────────────────────────────────────────
    #  GRID MANAGEMENT
    # ──────────────────────────────────────────
    def _reset_grid(self):
        self.running = False
        self.start_pos = self.target_pos = None
        self.current_path = []
        self.agent_pos    = None
        self.nodes_visited = self.path_cost = self.exec_time_ms = self.replans = 0
        self._init_grid()
        self._place_defaults()
        self._update_metrics()
        self._set_status("Reset complete.", ACCENT_GREEN)

    def _clear_path(self):
        self.current_path = []
        self.agent_pos    = None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1: continue
                if (r,c) == self.start_pos:   self._paint(r, c, C_START,  "S")
                elif (r,c) == self.target_pos: self._paint(r, c, C_TARGET, "T")
                else:                          self._paint(r, c, C_EMPTY)

    def _clear_walls(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    self.grid[r][c] = 0
                    self._paint(r, c, C_EMPTY)
        self._set_status("Walls cleared.", TEXT_DIM)

    def _generate_random_map(self):
        if not self.start_pos or not self.target_pos:
            messagebox.showwarning("Notice",
                "Place Start (S) and Target (T) first.")
            return
        density = self.density_var.get() / 100.0
        for r in range(self.rows):
            for c in range(self.cols):
                if (r,c) in (self.start_pos, self.target_pos): continue
                if random.random() < density:
                    self.grid[r][c] = -1;  self._paint(r, c, C_OBSTACLE)
                else:
                    self.grid[r][c] = 0;   self._paint(r, c, C_EMPTY)
        self._set_status("Random map generated.", ACCENT_AMBER)

    # ──────────────────────────────────────────
    #  HEURISTIC SELECTOR
    # ──────────────────────────────────────────
    def _get_h(self, r, c):
        gr, gc = self.target_pos
        name = self.heuristic_var.get()
        if   name == "Manhattan":  return h_manhattan(r, c, gr, gc)
        elif name == "Euclidean":  return h_euclidean(r, c, gr, gc)
        elif name == "Chebyshev":  return h_chebyshev(r, c, gr, gc)
        else:                      return h_octile(r, c, gr, gc)

    def _move_cost(self, dr, dc):
        return 1.414 if (dr,dc) in DIAGONAL_MOVES else 1.0

    def _get_neighbors(self, node):
        out = []
        for dr, dc in MOVES:
            nr, nc = node.r+dr, node.c+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] != -1:
                    g = node.g + self._move_cost(dr, dc)
                    h = self._get_h(nr, nc)
                    out.append(Node(nr, nc, node, g, h))
        return out

    # ──────────────────────────────────────────
    #  SEARCH CORE
    # ──────────────────────────────────────────
    def _search(self, sr, sc):
        """
        Unified A* / GBFS search with live canvas animation.
        Returns goal Node (with parent chain) or None.
        """
        algo  = self.algo_var.get()
        delay = self.speed_var.get() / 1000.0

        h0   = self._get_h(sr, sc)
        s_node = Node(sr, sc, None, g=0, h=h0)
        s_node.f = s_node.h if "GBFS" in algo else s_node.g + s_node.h

        heap    = []
        counter = 0
        heapq.heappush(heap, (s_node.f, counter, s_node))

        open_map  = {(sr, sc): s_node.f}   # pos -> f  for fast updates
        closed    = set()

        while heap and self.running:
            _, _, curr = heapq.heappop(heap)
            pos = curr.pos()
            if pos in closed: continue

            closed.add(pos)
            self.nodes_visited += 1

            # Visualise visited cell
            if pos not in (self.start_pos, self.target_pos):
                self._paint(curr.r, curr.c, C_VISITED)
                self.root.update()
                time.sleep(delay)

            if pos == self.target_pos:
                return curr

            for nb in self._get_neighbors(curr):
                np = nb.pos()
                if np in closed: continue

                nb.f = nb.h if "GBFS" in algo else nb.g + nb.h

                if np not in open_map or nb.f < open_map[np]:
                    open_map[np] = nb.f
                    counter += 1
                    heapq.heappush(heap, (nb.f, counter, nb))
                    if np not in (self.start_pos, self.target_pos):
                        self._paint(nb.r, nb.c, C_FRONTIER)

        return None

    def _extract_path(self, goal_node):
        path = []
        n = goal_node
        while n:
            path.append(n.pos())
            n = n.parent
        path.reverse()
        return path

    def _draw_path(self, path):
        for r, c in path:
            if (r,c) not in (self.start_pos, self.target_pos):
                self._paint(r, c, C_PATH)

    # ──────────────────────────────────────────
    #  DYNAMIC OBSTACLE SPAWNING
    # ──────────────────────────────────────────
    def _spawn_obstacle(self):
        """
        Randomly spawns a wall with probability spawn_prob%.
        Returns True if it landed ON the current path (needs re-plan).
        """
        if random.random() > self.spawn_prob_var.get() / 100.0:
            return False

        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if self.grid[r][c] == 0
            and (r, c) != self.start_pos
            and (r, c) != self.target_pos
            and (r, c) != self.agent_pos
        ]
        if not candidates:
            return False

        r, c = random.choice(candidates)
        self.grid[r][c] = -1
        self._paint(r, c, C_OBSTACLE)
        return (r, c) in self.current_path

    # ──────────────────────────────────────────
    #  AGENT ANIMATION
    # ──────────────────────────────────────────
    def _animate_agent(self, path):
        """
        Walk the agent along path, step by step.
        Re-plans on-the-fly if a new obstacle blocks the route.
        """
        self.current_path = list(path)
        delay = self.speed_var.get() / 1000.0
        idx   = 0

        while idx < len(self.current_path)-1 and self.running:
            r, c   = self.current_path[idx]
            self.agent_pos = (r, c)

            # Paint agent
            if (r,c) not in (self.start_pos, self.target_pos):
                self._paint(r, c, C_AGENT, "●")
            self.root.update()
            time.sleep(delay * 2)

            # Leave path trail
            if (r,c) not in (self.start_pos, self.target_pos):
                self._paint(r, c, C_PATH)

            # Dynamic obstacles
            if self.dynamic_var.get():
                blocked = self._spawn_obstacle()
                if blocked:
                    self._set_status(" Obstacle! Re-planning...", ACCENT_AMBER)
                    self.root.update()

                    # Clear future path visuals
                    for fr, fc in self.current_path[idx+1:]:
                        if (fr,fc) != self.target_pos:
                            self._paint(fr, fc, C_EMPTY)

                    self.nodes_visited = 0
                    t0 = time.perf_counter()
                    goal_node = self._search(r, c)
                    self.exec_time_ms = (time.perf_counter()-t0)*1000
                    self.replans += 1

                    if goal_node is None:
                        self._set_status(" Stuck! No path after obstacle.", ACCENT_PINK)
                        self._update_metrics()
                        return

                    new_path = self._extract_path(goal_node)
                    self._draw_path(new_path)
                    self.current_path = new_path
                    self.path_cost    = sum(
                        self._move_cost(
                            new_path[i+1][0]-new_path[i][0],
                            new_path[i+1][1]-new_path[i][1]
                        ) for i in range(len(new_path)-1)
                    )
                    idx = 0
                    self._update_metrics()
                    continue

            idx += 1

        # Arrived!
        self._paint(*self.target_pos, C_TARGET, "T")
        self._set_status("✅ Target Reached!", ACCENT_GREEN)

    # ──────────────────────────────────────────
    #  START / STOP
    # ──────────────────────────────────────────
    def _start_search(self):
        if not self.start_pos or not self.target_pos:
            messagebox.showerror("Missing",
                "Please place both Start (S) and Target (T) on the grid.")
            return

        self._clear_path()
        self.running       = True
        self.nodes_visited = 0
        self.path_cost     = 0.0
        self.exec_time_ms  = 0.0
        self.replans       = 0
        self.agent_pos     = self.start_pos

        self._set_status("Searching…", ACCENT_AMBER)
        self._update_metrics()

        t0 = time.perf_counter()
        goal_node = self._search(*self.start_pos)
        self.exec_time_ms = (time.perf_counter() - t0) * 1000

        if not self.running:
            self._set_status("Stopped.", ACCENT_PINK)
            return

        if goal_node is None:
            self._set_status("No path found! Remove some walls.", ACCENT_PINK)
            self._update_metrics()
            self.running = False
            return

        path = self._extract_path(goal_node)
        # Calculate actual path cost (using step costs)
        self.path_cost = sum(
            self._move_cost(
                path[i+1][0]-path[i][0],
                path[i+1][1]-path[i][1]
            ) for i in range(len(path)-1)
        )
        self._draw_path(path)
        self._update_metrics()
        self._set_status("✅ Path found! Agent moving…", ACCENT_GREEN)
        self.root.update()
        time.sleep(0.3)

        self._animate_agent(path)
        self._update_metrics()
        self.running = False

    def _stop_search(self):
        self.running = False
        self._set_status("Stopped.", ACCENT_PINK)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = DynamicPathfinderApp(root)
    root.mainloop()
