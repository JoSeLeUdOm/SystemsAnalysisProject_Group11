"""
Simulation 2: Cellular Automata Engagement Model
Community Education Volunteer Coordination Platform
Workshop 4 — System Simulation & Validation
Universidad Distrital Francisco José de Caldas

Parámetro del PDF (secciones 3.2.2, 4.2, 5.2, 7.1).
"""
# Docstring: describes the cellular automata simulation for volunteer engagement dynamics.

import numpy as np                     # Import NumPy for array operations and random numbers.
import matplotlib.pyplot as plt        # Import Matplotlib for plotting.
import matplotlib.colors as mcolors    # Import colormap utilities.
import matplotlib.patches as mpatches  # Import patches for legend creation.

# ── Reproducibilidad ──────────────────────────────────────────────────────────
SEED = 42                              # Fixed seed for reproducible results.
rng = np.random.default_rng(SEED)      # Create a random number generator with the given seed.

# ── Parámetros de la cuadrícula (Table 2 del PDF) ────────────────────────────
GRID_SIZE          = 30                # 30×30 grid = 900 cells.
INITIAL_RATIO      = 0.08              # 8% initial active volunteers (W1 base).
PLATFORM_RECRUIT   = 0.175             # Recruitment boost of 15‑20% per step (mean 17.5%).
SIM_WEEKS          = 20                # CA simulation horizon: 20 weeks.

# ── Estados del ciclo de vida del voluntario ──────────────────────────────────
INACTIVE   = 0                         # State 0: Inactive.
AWARE      = 1                         # State 1: Aware (has heard about the platform).
ENGAGED    = 2                         # State 2: Engaged (regularly participates).
ACTIVE     = 3                         # State 3: Active Tutor.
BURNED_OUT = 4                         # State 4: Burned out (temporarily leaves).

STATE_LABELS = {                       # Human‑readable names for each state.
    INACTIVE:   "Inactive",
    AWARE:      "Aware",
    ENGAGED:    "Engaged",
    ACTIVE:     "Active Tutor",
    BURNED_OUT: "Burned Out",
}

# Paleta de colores (warm → red para burnout, orange para activo)
STATE_COLORS = {                       # Color codes for each state.
    INACTIVE:   "#D9D9D9",             # Light gray.
    AWARE:      "#FFE699",             # Pale yellow.
    ENGAGED:    "#F4B942",             # Soft orange.
    ACTIVE:     "#E8820C",             # Dark orange (matches Fig. 4 of PDF).
    BURNED_OUT: "#C00000",             # Dark red.
}

CMAP_COLORS = [STATE_COLORS[s] for s in sorted(STATE_COLORS)]  # List of colors in state order.
CMAP = mcolors.ListedColormap(CMAP_COLORS)                     # Create a discrete colormap.
NORM = mcolors.BoundaryNorm(boundaries=[-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], ncolors=5)  # Normalizer for integer states.

# ── Inicialización de la cuadrícula ──────────────────────────────────────────

def init_grid(initial_ratio: float = INITIAL_RATIO) -> np.ndarray:
    """
    Cuadrícula 30×30. El 8% inicial está en estado ACTIVE (W1 base).
    El resto es INACTIVE.
    """
    # Docstring: creates a grid with the given initial ratio of ACTIVE cells.
    grid = np.full((GRID_SIZE, GRID_SIZE), INACTIVE, dtype=np.int8)  # Fill entire grid with INACTIVE.
    n_active = int(GRID_SIZE * GRID_SIZE * initial_ratio)            # Number of cells to set as ACTIVE.
    indices = rng.choice(GRID_SIZE * GRID_SIZE, size=n_active, replace=False)  # Random indices without replacement.
    for idx in indices:                                               # Iterate over chosen indices.
        row, col = divmod(int(idx), GRID_SIZE)                        # Convert flat index to (row, col).
        grid[row, col] = ACTIVE                                       # Set that cell to ACTIVE.
    return grid                                                       # Return the initialized grid.

# ── Vecindario de Moore (8 vecinos) ──────────────────────────────────────────

def count_neighbors(grid: np.ndarray, row: int, col: int, state: int) -> int:
    """Cuenta vecinos en el vecindario de Moore (8 celdas)."""
    # Docstring: counts Moore neighbors (8 directions) with a specific state.
    count = 0                                                         # Initialize counter.
    for dr in [-1, 0, 1]:                                             # Loop over row offset -1,0,1.
        for dc in [-1, 0, 1]:                                         # Loop over column offset -1,0,1.
            if dr == 0 and dc == 0:                                   # Skip the cell itself.
                continue
            r, c = (row + dr) % GRID_SIZE, (col + dc) % GRID_SIZE    # Wrap around toroidal boundary.
            if grid[r, c] == state:                                   # If neighbor has the target state.
                count += 1                                            # Increment counter.
    return count                                                      # Return total count.

# ── Reglas de transición (Ecuaciones 2, 3, 4 del PDF) ────────────────────────

def transition(grid: np.ndarray, platform_active: bool) -> np.ndarray:
    """
    Aplica las reglas de transición CA en paralelo (copia del grid).

    Reglas extraídas del PDF (secciones 3.2.2):
      Inactive → Aware   : P = 0.25  si n_active + n_engaged ≥ 2  (Ec. 2)
      Aware    → Engaged : P = 0.45 con plataforma / 0.10 sin ella (Ec. 3)
      Engaged  → Active  : P = 0.60 (probabilidad estándar de activación)
      Active   → Burned  : P = 0.08 + 0.05 × n_burnout_vecinos     (Ec. 4)
      Burned   → Inactive: P = 0.30 (recuperación/reinicio del ciclo)
      Active   → Inactive: churn natural P = 0.02
    """
    # Docstring: applies parallel update rules (asynchronous updates on a copy).
    new_grid = grid.copy()                                            # Work on a copy to avoid sequential interference.

    for row in range(GRID_SIZE):                                      # Loop over all rows.
        for col in range(GRID_SIZE):                                  # Loop over all columns.
            state = grid[row, col]                                    # Current state of the cell.
            n_active   = count_neighbors(grid, row, col, ACTIVE)      # Count active neighbors.
            n_engaged  = count_neighbors(grid, row, col, ENGAGED)     # Count engaged neighbors.
            n_burnout  = count_neighbors(grid, row, col, BURNED_OUT)  # Count burned‑out neighbors.

            if state == INACTIVE:                                     # Rule for inactive cells.
                # Ecuación 2: P(Inactive→Aware) = 0.25 si n_active + n_engaged ≥ 2
                if (n_active + n_engaged) >= 2 and rng.random() < 0.25:  # If enough active/engaged neighbors.
                    new_grid[row, col] = AWARE                        # Become aware.
                # Boost de reclutamiento de la plataforma
                elif platform_active and rng.random() < PLATFORM_RECRUIT * 0.10:  # Additional recruitment boost.
                    new_grid[row, col] = AWARE                        # Also become aware.

            elif state == AWARE:                                      # Rule for aware cells.
                # Ecuación 3: P(Aware→Engaged) = 0.45 plataforma / 0.10 sin ella
                p_engage = 0.45 if platform_active else 0.10         # Probability depends on platform state.
                if rng.random() < p_engage:                          # With that probability.
                    new_grid[row, col] = ENGAGED                     # Become engaged.

            elif state == ENGAGED:                                    # Rule for engaged cells.
                # Transición natural a Active Tutor
                if rng.random() < 0.60:                              # 60% chance.
                    new_grid[row, col] = ACTIVE                      # Become an active tutor.

            elif state == ACTIVE:                                     # Rule for active tutors.
                # Ecuación 4: P(Active→Burned) = 0.08 + 0.05 × n_burnout
                p_burnout = 0.08 + 0.05 * n_burnout                  # Burnout probability increases with burnout neighbors.
                if rng.random() < p_burnout:                         # With that probability.
                    new_grid[row, col] = BURNED_OUT                  # Become burned out.
                # Churn natural
                elif rng.random() < 0.02:                            # 2% natural churn.
                    new_grid[row, col] = INACTIVE                    # Leave the system (back to inactive).

            elif state == BURNED_OUT:                                 # Rule for burned‑out cells.
                # Recuperación → Inactive (reinicio del ciclo)
                if rng.random() < 0.30:                              # 30% chance of recovery.
                    new_grid[row, col] = INACTIVE                    # Return to inactive (re‑enter cycle).

    return new_grid                                                   # Return the updated grid.

# ── Ejecución de un escenario completo ───────────────────────────────────────

def run_ca(platform_active: bool,
           initial_ratio: float = INITIAL_RATIO,
           weeks: int = SIM_WEEKS) -> dict:
    """
    Ejecuta la simulación CA durante `weeks` pasos.
    Retorna historial de conteos por estado.
    """
    # Docstring: runs the CA simulation and returns state count history and snapshots.
    grid = init_grid(initial_ratio)                                   # Initialize the grid.
    history = {s: [] for s in range(5)}                               # Dictionary to store counts per state.
    snapshots = {}                                                    # Dictionary to store grid snapshots at key weeks.

    snapshot_weeks = {0, 4, 8, 12, 20}                                # Weeks at which to save grid snapshots.

    for week in range(weeks + 1):                                     # Loop over weeks (including week 0).
        if week in snapshot_weeks:                                    # If current week is a snapshot week.
            snapshots[week] = grid.copy()                             # Store a copy of the grid.

        # Conteos del estado actual
        total = GRID_SIZE * GRID_SIZE                                 # Total number of cells.
        for s in range(5):                                            # For each state.
            history[s].append(int(np.sum(grid == s)))                 # Count cells in that state and append to history.

        if week < weeks:                                              # Do not apply transition after the last week.
            grid = transition(grid, platform_active)                  # Update the grid using transition rules.

    return {"history": history, "snapshots": snapshots, "weeks": list(range(weeks + 1))}  # Return results.

# ── Análisis de sensibilidad a condiciones iniciales ─────────────────────────

def sensitivity_analysis(n_runs: int = 15,
                          ratio_range: tuple = (0.02, 0.25)) -> dict:
    """
    15 corridas con initial_ratio de 2% a 25% (sección 4.2 del PDF).
    Retorna activos y burnout finales por ratio.
    """
    # Docstring: sensitivity analysis over initial active ratios.
    ratios  = np.linspace(ratio_range[0], ratio_range[1], n_runs)      # 15 equally spaced ratios from 2% to 25%.
    final_active  = []                                                 # List to store final active counts.
    final_burnout = []                                                 # List to store final burnout counts.

    for ratio in ratios:                                               # For each initial ratio.
        result = run_ca(platform_active=True, initial_ratio=float(ratio), weeks=SIM_WEEKS)  # Run simulation.
        final_active.append(result["history"][ACTIVE][-1])             # Store final active count.
        final_burnout.append(result["history"][BURNED_OUT][-1])        # Store final burnout count.

    return {"ratios": ratios, "active": final_active, "burnout": final_burnout}  # Return results.

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Main function: runs ON/OFF scenarios, generates Figures 4,5,6."""
    print("=" * 60)                                                    # Print separator.
    print("  Simulation 2: Cellular Automata Engagement Model")        # Print title.
    print("  Community Education Volunteer Coordination Platform")      # Print subtitle.
    print("=" * 60)                                                    # Print separator.

    # Ejecutar condición ON y OFF
    print("\n  Running CA — Platform ON ...")                          # Print message.
    res_on  = run_ca(platform_active=True)                             # Run simulation with platform active.
    print("  Running CA — Platform OFF ...")                           # Print message.
    res_off = run_ca(platform_active=False)                            # Run simulation without platform.

    weeks_x = res_on["weeks"]                                          # X‑axis values (weeks).

    # Resumen textual de los resultados clave
    active_on_final  = res_on["history"][ACTIVE][-1]                   # Final active count (ON).
    active_off_final = res_off["history"][ACTIVE][-1]                  # Final active count (OFF).
    total            = GRID_SIZE * GRID_SIZE                           # Total cells.
    engagement_on    = (active_on_final  / total) * 100                # Final engagement % (ON).
    engagement_off   = (active_off_final / total) * 100                # Final engagement % (OFF).

    print(f"\n  Engagement week 20 — Platform ON : {engagement_on:.1f}%")    # Print ON engagement.
    print(f"  Engagement week 20 — Platform OFF: {engagement_off:.1f}%")     # Print OFF engagement.
    print(f"  Relative increase: +{engagement_on - engagement_off:.1f}pp "
          f"({(engagement_on/engagement_off - 1)*100:.0f}% relative)")        # Print difference.
    print(f"\n  Burnout week 20 — ON : {res_on['history'][BURNED_OUT][-1]}")  # Print ON burnout.
    print(f"  Burnout week 20 — OFF: {res_off['history'][BURNED_OUT][-1]}")   # Print OFF burnout.

    # ── FIGURA 4: Snapshots de la cuadrícula CA ───────────────────────────────
    snapshot_weeks = [0, 4, 8, 12, 20]                                 # Weeks to display.
    fig4, axes4 = plt.subplots(2, 5, figsize=(16, 7))                 # Create 2 rows, 5 columns of subplots.
    fig4.suptitle(                                                     # Overall title.
        "Figura 4 — Snapshots CA: Plataforma ON (arriba) vs OFF (abajo) "
        "en semanas 0, 4, 8, 12, 20",
        fontsize=12, fontweight="bold"
    )

    for col_idx, wk in enumerate(snapshot_weeks):                      # Loop over snapshot weeks.
        for row_idx, (res, label) in enumerate(                        # Loop over ON (row 0) and OFF (row 1).
            [(res_on, "ON"), (res_off, "OFF")]
        ):
            ax = axes4[row_idx, col_idx]                               # Get the current subplot.
            snap = res["snapshots"].get(wk, np.zeros((GRID_SIZE, GRID_SIZE)))  # Get snapshot (or zeros if missing).
            ax.imshow(snap, cmap=CMAP, norm=NORM, interpolation="nearest")     # Display grid as image.
            ax.set_title(f"{'ON' if row_idx==0 else 'OFF'} w{wk}", fontsize=9) # Subplot title.
            ax.axis("off")                                             # Turn off axes.

    # Leyenda
    legend_patches = [                                                 # Create colored patches for legend.
        mpatches.Patch(color=STATE_COLORS[s], label=STATE_LABELS[s])
        for s in range(5)
    ]
    fig4.legend(handles=legend_patches, loc="lower center", ncol=5,    # Add legend below the figure.
                fontsize=8, bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout(rect=[0, 0.05, 1, 1])                             # Adjust layout to leave room for legend.
    plt.savefig("figura4_snapshots.png",                           # Save figure.
                dpi=150, bbox_inches="tight")
    plt.close()                                                        # Close figure.

    # ── FIGURA 5: Evolución de estados a lo largo del tiempo ─────────────────
    fig5, axes5 = plt.subplots(2, 2, figsize=(14, 10))                 # Create 2×2 grid of subplots.
    fig5.suptitle(                                                     # Overall title.
        "Figura 5 — Evolución de estados (20 semanas): "
        "Tutores activos, Distribución, Burnout, Engagement total",
        fontsize=12, fontweight="bold"
    )

    # Top-left: Active Tutors ON vs OFF
    ax = axes5[0, 0]                                                   # Top‑left subplot.
    ax.plot(weeks_x, res_on["history"][ACTIVE],  color="#4472C4", label="Platform ON")   # Plot ON active.
    ax.plot(weeks_x, res_off["history"][ACTIVE], color="#ED7D31", label="Platform OFF")  # Plot OFF active.
    ax.set_title("Tutores activos")                                    # Title.
    ax.set_xlabel("Semana")                                            # X‑axis label.
    ax.set_ylabel("Número de células")                                 # Y‑axis label.
    ax.legend()                                                        # Add legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    # Top-right: Distribución completa de estados (ON)
    ax = axes5[0, 1]                                                   # Top‑right subplot.
    state_order = [INACTIVE, ACTIVE, BURNED_OUT]                       # Which states to stack.
    colors_stack = [STATE_COLORS[INACTIVE], STATE_COLORS[ACTIVE], STATE_COLORS[BURNED_OUT]]  # Corresponding colors.
    labels_stack = [STATE_LABELS[INACTIVE], STATE_LABELS[ACTIVE], STATE_LABELS[BURNED_OUT]]  # Labels.
    data_stack   = [res_on["history"][s] for s in state_order]         # Data for stacking.
    ax.stackplot(weeks_x, data_stack, labels=labels_stack, colors=colors_stack, alpha=0.85)  # Stacked area plot.
    ax.set_title("Distribución completa de estados (ON)")              # Title.
    ax.set_xlabel("Semana")                                            # X‑axis label.
    ax.set_ylabel("Número de células")                                 # Y‑axis label.
    ax.legend(fontsize=8)                                              # Legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    # Bottom-left: Tasa de burnout (%)
    ax = axes5[1, 0]                                                   # Bottom‑left subplot.
    burnout_pct_on  = [v / total * 100 for v in res_on["history"][BURNED_OUT]]   # ON burnout percentage.
    burnout_pct_off = [v / total * 100 for v in res_off["history"][BURNED_OUT]]  # OFF burnout percentage.
    ax.plot(weeks_x, burnout_pct_on,  color="#C00000", label="ON")     # Plot ON burnout.
    ax.plot(weeks_x, burnout_pct_off, color="#FF8C8C", linestyle="--", label="OFF")  # Plot OFF burnout (dashed).
    ax.set_title("Tasa de burnout (%)")                                # Title.
    ax.set_xlabel("Semana")                                            # X‑axis label.
    ax.set_ylabel("%")                                                 # Y‑axis label.
    ax.legend()                                                        # Legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    # Bottom-right: Tasa de engagement total (Active+Engaged+Aware / total)
    ax = axes5[1, 1]                                                   # Bottom‑right subplot.
    eng_on  = [(res_on["history"][ACTIVE][w] +                         # Sum of active, engaged, aware (ON)
                res_on["history"][ENGAGED][w] +
                res_on["history"][AWARE][w]) / total * 100
               for w in range(len(weeks_x))]
    eng_off = [(res_off["history"][ACTIVE][w] +                        # Sum of active, engaged, aware (OFF)
                res_off["history"][ENGAGED][w] +
                res_off["history"][AWARE][w]) / total * 100
               for w in range(len(weeks_x))]
    ax.plot(weeks_x, eng_on,  color="#4472C4", label="ON")             # Plot ON engagement.
    ax.plot(weeks_x, eng_off, color="#ED7D31", label="OFF")            # Plot OFF engagement.
    ax.set_title("Engagement total (%)")                               # Title.
    ax.set_xlabel("Semana")                                            # X‑axis label.
    ax.set_ylabel("%")                                                 # Y‑axis label.
    ax.legend()                                                        # Legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    plt.tight_layout()                                                 # Adjust layout.
    plt.savefig("figura5_evolucion.png",                           # Save figure.
                dpi=150, bbox_inches="tight")
    plt.close()                                                        # Close figure.

    # ── FIGURA 6: Análisis de caos y retrato de fase ─────────────────────────
    print("\n  Running sensitivity analysis (15 runs) ...")            # Print message.
    sens = sensitivity_analysis(n_runs=15)                             # Run sensitivity analysis.

    # Retrato de fase: Active vs Burned Out (semana a semana, ON)
    active_traj  = res_on["history"][ACTIVE]                           # Active trajectory over weeks.
    burnout_traj = res_on["history"][BURNED_OUT]                       # Burnout trajectory.

    fig6, axes6 = plt.subplots(1, 2, figsize=(12, 5))                  # Create 1×2 subplots.
    fig6.suptitle(                                                     # Overall title.
        "Figura 6 — Análisis de caos: Sensibilidad a condiciones iniciales "
        "y retrato de fase Active vs Burnout",
        fontsize=12, fontweight="bold"
    )

    # Sensibilidad a ratio inicial
    ax = axes6[0]                                                      # Left subplot.
    ax.plot(sens["ratios"] * 100, sens["active"],  "o-", color="#4472C4",  # Plot final active vs initial ratio.
            label="Active final")
    ax.plot(sens["ratios"] * 100, sens["burnout"], "s-", color="#C00000",  # Plot final burnout vs initial ratio.
            label="Burnout final")
    ax.set_title("Sensibilidad a condiciones iniciales")               # Title.
    ax.set_xlabel("Ratio de engagement inicial (%)")                   # X‑axis label.
    ax.set_ylabel("Células en estado final")                           # Y‑axis label.
    ax.legend()                                                        # Legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    # Retrato de fase
    ax = axes6[1]                                                      # Right subplot.
    sc = ax.scatter(active_traj, burnout_traj,                         # Scatter plot of (active, burnout) over time.
                    c=weeks_x, cmap="viridis", s=40, zorder=3)         # Color by week.
    ax.plot(active_traj, burnout_traj, "-", color="gray", alpha=0.5, linewidth=1)  # Connect points with line.
    plt.colorbar(sc, ax=ax, label="Semana")                            # Add colorbar showing week number.
    # Marcar atractor (región 120-180 activos, 50-80 burnout)
    ax.axvspan(120, 180, alpha=0.08, color="green", label="Región atractora")   # Attractor region for active.
    ax.axhspan(50,  80,  alpha=0.08, color="red")                      # Attractor region for burnout.
    ax.scatter([active_traj[-1]], [burnout_traj[-1]],                  # Mark the final point.
               marker="*", s=200, color="gold", zorder=5, label="Atractor final")
    ax.set_title("Retrato de fase: Active vs Burned Out")              # Title.
    ax.set_xlabel("Tutores activos")                                   # X‑axis label.
    ax.set_ylabel("Burnout")                                           # Y‑axis label.
    ax.legend(fontsize=8)                                              # Legend.
    ax.grid(True, alpha=0.3)                                           # Light grid.

    plt.tight_layout()                                                 # Adjust layout.
    plt.savefig("figura6_caos_fase.png",                           # Save figure.
                dpi=150, bbox_inches="tight")
    plt.close()                                                        # Close figure.

    print("\n" + "=" * 60)                                             # Print separator.
    print("  Generated figures:")                                      # Print message.
    print("    figura4_snapshots.png")                            # List generated file.
    print("    figura5_evolucion.png")                            # List generated file.
    print("    figura6_caos_fase.png")                            # List generated file.
    print("=" * 60)                                                    # Print separator.

if __name__ == "__main__":                                             # Standard Python guard.
    main()                                                             # Execute main function when script is run directly.