"""
Simulation 2 — Voluntary Commitment Cellular Automata
=========================================================
Volunteer Coordination Platform for Community Education
Universidad Distrital Francisco José de Caldas — Workshop 4

Adapted from: sir_simulation.py (SIR Epidemic Model – tkinter visualisation)
Authors    : Jose Luis Leudo, David Rojas, Adrián Hernández, Johan Candia
Instructor : Carlos Andrés Sierra, M.Sc. — Systems Analysis and Design
Date       : May 2026

General Description
-------------------
Each cell in the 30×30 grid represents a member of the university
community. The automaton models the propagation of voluntary commitment
through five life-cycle states:

    INACTIVE → AWARE → COMMITTED → ACTIVE_TUTOR → EXHAUSTED → INACTIVE

State transitions are local (Moore neighborhood, 8 neighbors)
and incorporate a global modifier when the platform is active,
exactly replicating the probabilities specified in the W4 report:

    P(INACTIVE → AWARE)    = 0.25  if ≥2 active/committed neighbors
    P(AWARE → COMMITTED)   = 0.45 (platform ON) / 0.10 (platform OFF)
    P(COMMITTED → ACTIVE_TUTOR) = 0.60
    P(ACTIVE_TUTOR → EXHAUSTED) = 0.08 + 0.05 × n_exhausted_neighbors
    P(EXHAUSTED → INACTIVE)     = 0.30  (recovery and cycle re-entry)

Interactive Controls
-----------------------
    1         Population curves view (state evolution over time)
    2         Spatial grid view (animated cellular automaton)
    p         Toggle digital platform in real time
    Space     Pause / resume grid simulation
    r         Reset grid with initial ratio from W1 (8%)
    +/-       Increase / decrease simulation speed
    ESC       Exit

Dependencies: tkinter (included in standard Python — no additional installation)

Reproducibility
----------------
Global random seed SEED = 42 for deterministic results.
"""

import tkinter as tk
import random

# =============================================================================
# GLOBAL CONSTANTS
# =============================================================================

# --- Window and grid ---
WIDTH, HEIGHT = 900, 600          # window dimensions in pixels
CELL          = 20                # size of each cell (~30×28 grid)
GCOLS         = WIDTH  // CELL    # columns
GROWS         = (HEIGHT - 30) // CELL  # rows (30px reserved for status bar)
FONT          = ("Courier", 11)

# --- Reproducibility seed (identical to simulation_1_discrete_event.py) ---
SEED = 42
random.seed(SEED)

# =============================================================================
# VOLUNTEER LIFE-CYCLE STATE DEFINITIONS
# =============================================================================

INACTIVE     = 0   # No active participation in the platform
AWARE        = 1   # Knows about the platform, not yet committed
COMMITTED    = 2   # Registered, in process of assignment
ACTIVE_TUTOR = 3   # Assigned to a community tutoring project
EXHAUSTED    = 4   # Burnout; temporarily out of the system

NUM_STATES = 5

# --- Color palette by state (consistent with W4 report figures) ---
COLOR_STATE = {
    INACTIVE     : "#1e1e32",   # dark gray
    AWARE        : "#d4a017",   # amber yellow
    COMMITTED    : "#3c8cdc",   # blue
    ACTIVE_TUTOR : "#e8780a",   # orange ("Active" color from W4 figures)
    EXHAUSTED    : "#dc3c3c",   # red
}

# Labels for legend and status bar
STATE_NAME = {
    INACTIVE     : "Inactive",
    AWARE        : "Aware",
    COMMITTED    : "Committed",
    ACTIVE_TUTOR : "Active Tutor",
    EXHAUSTED    : "Exhausted",
}

BG = "#0c0c16"   # general window background

# =============================================================================
# MODEL PARAMETERS (calibrated from W1-W3, Table 2 of the report)
# =============================================================================

INITIAL_RATIO        = 0.08   # 8% — W1 volunteer base (Table 2, CA column)
CONTAGION_PROB       = 0.25   # P(INACTIVE→AWARE) with ≥2 active neighbors
MINIMUM_NEIGHBORS    = 2      # threshold of influential neighbors to spark interest
COMMIT_PROB_ON       = 0.45   # P(AWARE→COMMITTED) with platform active
COMMIT_PROB_OFF      = 0.10   # P(AWARE→COMMITTED) without platform
ACTIVATE_PROB        = 0.60   # P(COMMITTED→ACTIVE_TUTOR)
BASE_EXHAUSTION_PROB = 0.08   # base component of P(ACTIVE→EXHAUSTED)
EXHAUSTION_COEFF     = 0.05   # increment per exhausted neighbor (social contagion)
RECOVERY_PROB        = 0.30   # P(EXHAUSTED→INACTIVE) — re-entry to the cycle

# =============================================================================
# CELLULAR AUTOMATON LOGIC
# =============================================================================

def initialize_grid(ratio: float = INITIAL_RATIO) -> list:
    """
    Creates the initial grid with `ratio` of cells in ACTIVE_TUTOR state,
    the rest INACTIVE. Replicates the initial condition of the CA experiment (W4 §4.2).

    Parameters
    ----------
    ratio : float
        Fraction of initially active cells (default 8%, W1 data).

    Returns
    -------
    list[list[int]]
        GROWS × GCOLS grid with initial states.
    """
    grid = [[INACTIVE] * GCOLS for _ in range(GROWS)]
    for r in range(GROWS):
        for c in range(GCOLS):
            if random.random() < ratio:
                grid[r][c] = ACTIVE_TUTOR
    return grid


def count_state_neighbors(grid: list, r: int, c: int, state: int) -> int:
    """
    Counts how many of the 8 neighbors in the (toroidal) Moore neighborhood
    are in a given state.

    The toroidal boundary (modulo) is consistent with the implementation of
    sir_simulation.py and the topology used in the W4 report.

    Parameters
    ----------
    grid   : current state grid
    r, c   : row and column of the central cell
    state  : state code to count

    Returns
    -------
    int : number of neighbors in `state` (0–8)
    """
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue   # exclude central cell
            nr = (r + dr) % GROWS
            nc = (c + dc) % GCOLS
            if grid[nr][nc] == state:
                count += 1
    return count


def next_generation(grid: list, platform_active: bool) -> list:
    """
    Applies the cellular automaton transition rules to the entire grid
    and returns a new grid (without modifying the original).

    Probabilities implement exactly the W4 §3.2.2 model:

        INACTIVE     → AWARE       : P = 0.25  if n_active + n_committed ≥ 2
        AWARE        → COMMITTED   : P = 0.45 (platform ON) / 0.10 (OFF)
        COMMITTED    → ACTIVE_TUTOR: P = 0.60
        ACTIVE_TUTOR → EXHAUSTED   : P = 0.08 + 0.05 × n_exhausted_neighbors
        EXHAUSTED    → INACTIVE    : P = 0.30  (recovery)

    The platform modifier acts as an environmental variable that alters
    transition probabilities without imposing direct changes — this produces
    emergent behavior, not centralized control (W4 §7.2).

    Parameters
    ----------
    grid            : current grid
    platform_active : bool — if True, applies W2 recruitment boost

    Returns
    -------
    list[list[int]] : new grid with updated states
    """
    new = [row[:] for row in grid]   # shallow copy row by row

    for r in range(GROWS):
        for c in range(GCOLS):
            current_state = grid[r][c]

            # ------------------------------------------------------------------
            # RULE 1 — INACTIVE → AWARE
            # Social influence: requires critical mass of participating neighbors
            # ------------------------------------------------------------------
            if current_state == INACTIVE:
                n_influencers = (
                    count_state_neighbors(grid, r, c, ACTIVE_TUTOR) +
                    count_state_neighbors(grid, r, c, COMMITTED)
                )
                if n_influencers >= MINIMUM_NEIGHBORS:
                    if random.random() < CONTAGION_PROB:
                        new[r][c] = AWARE

            # ------------------------------------------------------------------
            # RULE 2 — AWARE → COMMITTED
            # Digital platform increases this probability (W2 design)
            # ------------------------------------------------------------------
            elif current_state == AWARE:
                prob = (COMMIT_PROB_ON
                        if platform_active
                        else COMMIT_PROB_OFF)
                if random.random() < prob:
                    new[r][c] = COMMITTED

            # ------------------------------------------------------------------
            # RULE 3 — COMMITTED → ACTIVE_TUTOR
            # ------------------------------------------------------------------
            elif current_state == COMMITTED:
                if random.random() < ACTIVATE_PROB:
                    new[r][c] = ACTIVE_TUTOR

            # ------------------------------------------------------------------
            # RULE 4 — ACTIVE_TUTOR → EXHAUSTED
            # Burnout contagion by neighborhood (Equation 4, W4 §3.2.2):
            #    P = 0.08 + 0.05 × n_exhausted_neighbors
            # ------------------------------------------------------------------
            elif current_state == ACTIVE_TUTOR:
                n_exhausted = count_state_neighbors(grid, r, c, EXHAUSTED)
                exhaustion_prob = BASE_EXHAUSTION_PROB + EXHAUSTION_COEFF * n_exhausted
                exhaustion_prob = min(exhaustion_prob, 1.0)   # bounded in [0, 1]
                if random.random() < exhaustion_prob:
                    new[r][c] = EXHAUSTED

            # ------------------------------------------------------------------
            # RULE 5 — EXHAUSTED → INACTIVE (recovery and re-entry to the cycle)
            # ------------------------------------------------------------------
            elif current_state == EXHAUSTED:
                if random.random() < RECOVERY_PROB:
                    new[r][c] = INACTIVE

    return new


# =============================================================================
# TEMPORAL ANALYSIS
# =============================================================================

def count_states(grid: list) -> dict:
    """
    Counts how many cells are in each state.

    Returns
    -------
    dict {state (int): count (int)}
    """
    flat = [cell for row in grid for cell in row]
    return {e: flat.count(e) for e in range(NUM_STATES)}


# =============================================================================
# VISUALISATION — POPULATION CURVES (View 1)
# =============================================================================

def draw_curves(canvas: tk.Canvas, history: list) -> None:
    """
    Draws the temporal evolution of the population by state.

    Equivalent to Figure 5 in the W4 report (state evolution over time).
    One color curve for each of the five states.

    Parameters
    ----------
    canvas  : tkinter Canvas widget
    history : list of dicts {state: count} per generation
    """
    canvas.delete("curves")

    if len(history) < 2:
        canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="Run the simulation (key 2) to generate data.",
            fill="#aaaaaa", font=FONT, tags="curves"
        )
        return

    mx, my = 70, 30
    w  = WIDTH  - mx - 20
    h  = HEIGHT - my - 60
    total_cells = GROWS * GCOLS
    n  = len(history)

    # Chart frame
    canvas.create_rectangle(mx, my, mx + w, my + h,
                            outline="#505070", fill="#1e1e32", tags="curves")

    # One curve per state
    for state, color in COLOR_STATE.items():
        points = []
        for i, snapshot in enumerate(history):
            value = snapshot.get(state, 0) / total_cells   # fraction 0–1
            px = mx + int(i / (n - 1) * w)
            py = my + h - int(value * h)
            points.extend([px, py])
        if len(points) >= 4:
            canvas.create_line(points, fill=color, width=2, tags="curves")

    # Legend
    for i, (state, color) in enumerate(COLOR_STATE.items()):
        x0, y0 = mx + 10, my + 10 + i * 20
        canvas.create_rectangle(x0, y0, x0 + 12, y0 + 12,
                                fill=color, outline="", tags="curves")
        canvas.create_text(x0 + 18, y0 + 6,
                           text=STATE_NAME[state],
                           fill="#c8c8c8", font=FONT, anchor="w", tags="curves")

    # X-axis label
    canvas.create_text(mx + w // 2, my + h + 20,
                       text=f"Generation (week)  —  {n} steps simulated",
                       fill="#aaaaaa", font=FONT, tags="curves")


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class CAApplication:
    """
    Main controller for the Cellular Automata simulation.

    Manages:
    - Grid state and generational evolution.
    - Two views: population curves (mode 1) and spatial grid (mode 2).
    - Platform active/inactive switch (ON vs OFF experiment, W4 §4.2).
    - Snapshot history for plotting temporal evolution.

    The structure follows the App class pattern from sir_simulation.py,
    extended to handle five states and Workshop 4 experiments.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("CA — Volunteer Platform | Workshop 4 — UDFJC")
        root.resizable(False, False)

        # --- Main Canvas ---
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # --- Bottom status bar ---
        self.status = tk.Label(root, text="", font=FONT,
                               bg="#08080f", fg="#aaaaaa", anchor="w")
        self.status.pack(fill=tk.X)

        # --- Internal state ---
        self.mode            = 1          # 1=curves, 2=grid
        self.grid            = initialize_grid()
        self.generation      = 0
        self.paused          = False
        self.platform_active = True       # start with platform active (ON)
        self.delay_ms        = 120        # ms between generations
        self.history         = [count_states(self.grid)]

        # --- Pre-creation of rectangles (performance pattern from sir_simulation.py) ---
        # Creating all rectangles once and updating only their color
        # avoids the overhead of creating/destroying Canvas objects each frame.
        self.rects = [
            [self.canvas.create_rectangle(
                c * CELL, r * CELL,
                c * CELL + CELL - 1, r * CELL + CELL - 1,
                fill=COLOR_STATE[INACTIVE], outline="#1a1a28",
                state="hidden")
             for c in range(GCOLS)]
            for r in range(GROWS)
        ]

        # Persistent legend (drawn once, visible in both views)
        self._draw_fixed_legend()

        # Keyboard bindings
        root.bind("<Key>", self._handle_key)

        # Start with curves view and animation loop
        self._show_curves()
        self._main_loop()

    # =========================================================================
    # VIEWS
    # =========================================================================

    def _show_curves(self) -> None:
        """Activates view 1: temporal state evolution chart."""
        self._hide_grid()
        draw_curves(self.canvas, self.history)
        plat = "ON ✓" if self.platform_active else "OFF ✗"
        self.status.config(
            text=(f"  POPULATION CURVES  |  Gen: {self.generation}  |  "
                  f"Platform: {plat}  |  "
                  f"1=curves  2=grid  p=platform  ESC=exit")
        )

    def _show_grid(self) -> None:
        """
        Activates view 2: spatial grid of the cellular automaton.
        Updates the color of each pre-created rectangle according to current state.
        """
        self.canvas.delete("curves")
        counts = count_states(self.grid)
        total   = GROWS * GCOLS

        for r in range(GROWS):
            for c in range(GCOLS):
                self.canvas.itemconfig(
                    self.rects[r][c],
                    fill=COLOR_STATE[self.grid[r][c]],
                    state="normal"
                )

        plat    = "ON ✓" if self.platform_active else "OFF ✗"
        paused  = " [PAUSED]" if self.paused else ""
        self.status.config(
            text=(
                f"  Gen {self.generation}{paused}  |  Platform: {plat}  |  "
                f"Active: {counts[ACTIVE_TUTOR]/total*100:.1f}%  "
                f"Exhausted: {counts[EXHAUSTED]/total*100:.1f}%  "
                f"Aware: {counts[AWARE]/total*100:.1f}%  |  "
                f"1=curves  2=grid  p=plat  Space=pause  r=reset  +/-=speed  ESC=exit"
            )
        )

    def _hide_grid(self) -> None:
        """Hides all rectangles in the grid."""
        for row in self.rects:
            for rect in row:
                self.canvas.itemconfig(rect, state="hidden")

    def _draw_fixed_legend(self) -> None:
        """
        Draws the state legend in the top-right corner.
        Rendered only once at start; remains visible in both views.
        """
        x_base, y_base = WIDTH - 145, 8
        for i, (state, color) in enumerate(COLOR_STATE.items()):
            y = y_base + i * 16
            self.canvas.create_rectangle(x_base, y, x_base + 10, y + 10,
                                         fill=color, outline="", tags="legend")
            self.canvas.create_text(x_base + 14, y + 5,
                                    text=STATE_NAME[state],
                                    fill="#c8c8c8",
                                    font=("Courier", 9),
                                    anchor="w", tags="legend")

    # =========================================================================
    # MAIN SIMULATION LOOP
    # =========================================================================

    def _main_loop(self) -> None:
        """
        Simulation engine: advances a generation when the view is the
        grid and the simulation is not paused. Rescheduled with `after`
        to not block the tkinter event loop.

        Pattern inherited from _loop() in sir_simulation.py, adapted for five
        states and active/inactive platform control.
        """
        if self.mode == 2 and not self.paused:
            self.grid = next_generation(
                self.grid, self.platform_active
            )
            self.generation += 1
            # Record snapshot for curves view
            self.history.append(count_states(self.grid))
            self._show_grid()

        self.root.after(self.delay_ms, self._main_loop)

    # =========================================================================
    # KEYBOARD HANDLING
    # =========================================================================

    def _handle_key(self, event: tk.Event) -> None:
        """
        Processes all keyboard shortcuts defined in the module docstring.

        Key 'p' toggles the platform ON/OFF experiment (W4 §4.2)
        in real time to observe the network amplification effect.
        """
        k = event.keysym

        if k == "Escape":
            self.root.destroy()

        # View change
        elif k == "1":
            self.mode = 1
            self._show_curves()

        elif k == "2":
            self.mode = 2
            self._show_grid()

        # Platform switch — experiment ON vs OFF (W4 §4.2)
        elif k in ("p", "P"):
            self.platform_active = not self.platform_active
            state = "ACTIVE" if self.platform_active else "DEACTIVATED"
            print(f"[Platform] {state} — Generation {self.generation}")
            if self.mode == 1:
                self._show_curves()
            else:
                self._show_grid()

        # Pause / resume (grid view only)
        elif k == "space" and self.mode == 2:
            self.paused = not self.paused
            self._show_grid()

        # Reset with W1 initial condition (ratio = 8%)
        elif k in ("r", "R") and self.mode == 2:
            random.seed(SEED)   # ensures reproducibility on reset
            self.grid = initialize_grid(INITIAL_RATIO)
            self.generation  = 0
            self.history     = [count_states(self.grid)]
            self._show_grid()

        # Speed control
        elif k in ("plus", "equal"):
            self.delay_ms = max(self.delay_ms - 20, 20)   # min 20 ms (~50 fps)

        elif k == "minus":
            self.delay_ms = min(self.delay_ms + 20, 500)  # max 500 ms (2 fps)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main() -> None:
    """
    Initializes the tkinter window, instantiates the main controller, and
    starts the GUI event loop.
    """
    root = tk.Tk()
    CAApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()