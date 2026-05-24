"""
Simulation 1: Discrete-Event Matching Pipeline
Community Education Volunteer Coordination Platform
Workshop 4 — System Simulation & Validation
Universidad Distrital Francisco José de Caldas

Parámetros del PDF (Table 2 y secciones 3.2.1, 5.1).
"""
# File docstring: describes the discrete‑event simulation for volunteer‑project matching.

import numpy as np                     # Import NumPy for numerical operations and random number generation.
import matplotlib.pyplot as plt        # Import Matplotlib's pyplot for plotting figures.
import matplotlib.gridspec as gridspec # Import GridSpec to create complex subplot layouts.

# ── Reproducibilidad ──────────────────────────────────────────────────────────
SEED = 42                              # Fixed seed for reproducible random numbers.
rng = np.random.default_rng(SEED)      # Create a random number generator with the given seed.

# ── Parámetros del modelo (Table 2 del PDF) ───────────────────────────────────
LOW_AVAILABILITY_RATIO   = 0.54        # 54% of volunteers have low availability (<2 hrs/week) – from W1 Survey Q5.
ENGINEERING_RATIO        = 0.40        # 40% of volunteers are from Engineering/Mathematics – from W1 Survey Q2.
PEDAGOGY_RATIO           = 0.22        # 22% of volunteers are from Pedagogy – from W1 Survey Q2.
SESSION_CANCEL_RATE      = 0.15        # 15% session cancellation risk – from W3 Risk RO03.
LATENCY_MEAN_MS          = 45.0        # Target mean matching latency 45 ms – from W2 NFR.
LATENCY_STD_MS           = 5.0         # Standard deviation around the mean latency.
SIMULATION_WEEKS         = 12          # Simulation horizon: 12 weeks – from W3 Gantt.
VOLUNTEER_CHURN_STD      = 3           # Weekly fluctuation of volunteer pool: ±3 volunteers – from PDF Fig. 2.
NUM_PROJECTS             = 20          # Number of projects to match (all three scenarios use 20 projects – Table 3).

# Pesos del algoritmo C(v,p)  — W2 Algorithm (ecuación 1 del PDF)
W_SKILL    = 0.40                      # Weight for skill match (40%).
W_SCHEDULE = 0.30                      # Weight for schedule compatibility (30%).
W_LOCATION = 0.15                      # Weight for location proximity (15%).
W_EXPERIENCE = 0.15                    # Weight for previous experience (15%).

# Escenarios (Table 3 del PDF)
SCENARIOS = {                          # Dictionary mapping scenario names to initial volunteer counts.
    "Baseline":   50,                  # Baseline: 50 volunteers.
    "Optimistic": 80,                  # Optimistic: 80 volunteers.
    "Stress":     25,                  # Stress test: 25 volunteers.
}

# Umbrales de cobertura y compatibilidad (W2 KPI)
COVERAGE_TARGET     = 0.70             # Target coverage: 70% of projects assigned.
COMPATIBILITY_TARGET = 0.80            # Target mean compatibility score: 0.80.

# ── Funciones auxiliares ──────────────────────────────────────────────────────

def generate_volunteers(n: int) -> list[dict]:
    """Generates n volunteers with attributes calibrated from W1 survey."""
    # Function docstring.
    volunteers = []                     # Initialize an empty list to store volunteer dictionaries.
    for i in range(n):                 # Loop over the desired number of volunteers.
        # Habilidad: Engineering 40%, Pedagogy 22%, Other 38%
        r = rng.random()               # Draw a uniform random number between 0 and 1.
        if r < ENGINEERING_RATIO:      # If the number is below 0.40 -> Engineering.
            skill_type = "engineering" # Set skill type to engineering.
        elif r < ENGINEERING_RATIO + PEDAGOGY_RATIO: # If between 0.40 and 0.62 -> Pedagogy.
            skill_type = "pedagogy"    # Set skill type to pedagogy.
        else:                          # Otherwise (above 0.62) -> Other.
            skill_type = "other"       # Set skill type to other.

        volunteers.append({            # Append a new volunteer dictionary to the list.
            "id": i,                   # Unique identifier.
            "skill_type": skill_type,  # One of "engineering", "pedagogy", "other".
            "availability": "low" if rng.random() < LOW_AVAILABILITY_RATIO else "high",
            # Randomly assign low availability with probability 0.54, else high.
            # Puntuaciones base normalizadas [0,1] para el algoritmo
            "skill_score":      rng.uniform(0.5, 1.0),   # Random skill score between 0.5 and 1.0.
            "schedule_score":   rng.uniform(0.3, 1.0),   # Random schedule score between 0.3 and 1.0.
            "location_score":   rng.uniform(0.4, 1.0),   # Random location score between 0.4 and 1.0.
            "experience_score": rng.uniform(0.2, 1.0),   # Random experience score between 0.2 and 1.0.
        })
    return volunteers                  # Return the list of generated volunteers.

def generate_projects(n: int) -> list[dict]:
    """Generates n community tutoring projects with required skills."""
    # Function docstring.
    return [{"id": j, "required_skill": rng.choice(["engineering", "pedagogy", "other"])}
            # Create a list of project dictionaries; each project has an ID and a randomly chosen required skill.
            for j in range(n)]         # Loop over project indices from 0 to n-1.

def compatibility(volunteer: dict, project: dict) -> float:
    """
    C(v,p) = 0.40·Sk + 0.30·Sc + 0.15·Sl + 0.15·Se   (Ecuación 1 del PDF)
    Bonus de habilidad si el tipo del voluntario coincide con el proyecto.
    """
    # Docstring: formula and skill‑match bonus.
    skill_match = 1.0 if volunteer["skill_type"] == project["required_skill"] else 0.6
    # Bonus: 1.0 if types match, otherwise 0.6.
    sk = volunteer["skill_score"] * skill_match   # Weighted skill component.
    sc = volunteer["schedule_score"]              # Schedule component.
    sl = volunteer["location_score"]              # Location component.
    se = volunteer["experience_score"]            # Experience component.
    return W_SKILL * sk + W_SCHEDULE * sc + W_LOCATION * sl + W_EXPERIENCE * se
    # Return the weighted sum according to Equation 1.

def match_pipeline(volunteers: list[dict], projects: list[dict]) -> dict:
    """
    Pipeline de asignación discreta:
      Para cada proyecto busca el voluntario disponible con mayor C(v,p).
    Retorna métricas del ciclo.
    """
    # Docstring: discrete matching pipeline.
    available = list(volunteers)                   # Create a mutable copy of the volunteer list.
    assigned_scores = []                           # List to store compatibility scores of assigned matches.
    cancelled = 0                                  # Counter for cancelled sessions.
    unassigned = 0                                 # Counter for projects that could not be matched.
    latencies_ms = []                              # List to store per‑project matching latencies (ms).

    for project in projects:                       # Iterate over each project.
        if not available:                          # If no volunteers are left, increment unassigned and skip.
            unassigned += 1                        # Count this project as unassigned.
            continue                               # Go to the next project.

        # Simular latencia de cómputo del algoritmo (media 45 ms, NFR <60 s)
        latency = rng.normal(LATENCY_MEAN_MS, LATENCY_STD_MS)  # Draw latency from normal distribution.
        latencies_ms.append(max(latency, 1.0))                 # Append latency (ensure at least 1 ms).

        # Seleccionar mejor match
        scores = [(compatibility(v, project), v) for v in available]  # List of (score, volunteer) pairs.
        scores.sort(key=lambda x: x[0], reverse=True)                 # Sort descending by score.
        best_score, best_vol = scores[0]                              # Take the highest‑scoring volunteer.

        # Posible cancellación (W3 Risk RO03: 15%)
        if rng.random() < SESSION_CANCEL_RATE:     # With probability 0.15, session is cancelled.
            cancelled += 1                         # Increment cancellation counter.
            # El proyecto sigue cubierto (se absorbe la cancellación)
            assigned_scores.append(best_score)     # Still record the score (project is considered covered).
        else:                                      # Otherwise, normal assignment.
            assigned_scores.append(best_score)     # Record the score.
            available.remove(best_vol)             # Remove the matched volunteer from the available pool.

    coverage = (len(projects) - unassigned) / len(projects) * 100  # Coverage percentage.
    mean_compat = float(np.mean(assigned_scores)) if assigned_scores else 0.0  # Mean compatibility.
    mean_latency = float(np.mean(latencies_ms)) if latencies_ms else 0.0       # Mean latency.

    return {                                     # Return a dictionary with all metrics.
        "coverage": coverage,                    # Coverage (%).
        "mean_compat": mean_compat,              # Mean C(v,p) score.
        "cancelled": cancelled,                  # Number of cancelled sessions.
        "unassigned": unassigned,                # Number of unassigned projects.
        "latencies_ms": latencies_ms,            # List of per‑project latencies.
        "mean_latency": mean_latency,            # Average latency.
        "all_scores": assigned_scores,           # All compatibility scores from assignments.
    }

def run_scenario_over_weeks(base_volunteers: int, num_projects: int,
                             weeks: int = SIMULATION_WEEKS) -> dict:
    """
    Ejecuta la simulación semana a semana durante `weeks` semanas.
    Churn: ±3 voluntarios por semana (Fig. 2 del PDF).
    """
    # Docstring: weekly simulation with volunteer churn.
    weekly_coverage   = []                       # List to store coverage per week.
    weekly_compat     = []                       # List to store mean compatibility per week.
    weekly_pool       = []                       # List to store volunteer pool size per week.
    all_scores_global = []                       # Accumulate all compatibility scores across weeks.

    current_pool = base_volunteers               # Start with the initial number of volunteers.
    projects = generate_projects(num_projects)   # Generate a fixed set of projects for the whole run.

    for week in range(1, weeks + 1):             # Loop over weeks 1..weeks.
        # Fluctuación estocástica del pool (±3)
        churn = int(rng.normal(0, VOLUNTEER_CHURN_STD))  # Random churn drawn from normal distribution.
        current_pool = max(5, current_pool + churn)     # Update pool size, never below 5 volunteers.

        volunteers = generate_volunteers(current_pool)  # Generate a new set of volunteers for this week.
        result = match_pipeline(volunteers, projects)   # Run the matching pipeline for this week.

        weekly_coverage.append(result["coverage"])      # Store this week's coverage.
        weekly_compat.append(result["mean_compat"])     # Store this week's mean compatibility.
        weekly_pool.append(current_pool)                # Store the current pool size.
        all_scores_global.extend(result["all_scores"])  # Extend the global list with this week's scores.

    return {                                         # Return aggregated results.
        "weekly_coverage": weekly_coverage,          # List of weekly coverage values.
        "weekly_compat":   weekly_compat,            # List of weekly mean compatibilities.
        "weekly_pool":     weekly_pool,              # List of weekly pool sizes.
        "all_scores":      all_scores_global,        # All compatibility scores from all weeks.
        "final_result":    result,                   # The result object of the last week (useful for final stats).
    }

# ── Análisis de sensibilidad ──────────────────────────────────────────────────

def sensitivity_latency_vs_pool() -> tuple:
    """Latencia vs. tamaño del pool (Fig. 3 izquierda)."""
    # Docstring: latency as a function of pool size.
    sizes = list(range(10, 105, 10))                 # Pool sizes: 10, 20, ..., 100.
    mean_latencies = []                              # List to hold mean latency for each pool size.
    for n in sizes:                                  # For each size.
        lats = [rng.normal(LATENCY_MEAN_MS, LATENCY_STD_MS) for _ in range(n)]  # Generate n latencies.
        mean_latencies.append(np.mean(lats))         # Compute and store the mean.
    return sizes, mean_latencies                     # Return the two lists.

def sensitivity_coverage_vs_volunteers() -> tuple:
    """Cobertura vs. número de voluntarios (Fig. 3 centro)."""
    # Docstring: coverage as a function of number of volunteers.
    sizes = list(range(5, 105, 5))                   # Volunteer counts: 5, 10, ..., 100.
    coverages = []                                   # List to hold coverage for each volunteer count.
    projects = generate_projects(NUM_PROJECTS)       # Generate a fixed set of projects.
    for n in sizes:                                  # For each volunteer count.
        volunteers = generate_volunteers(n)          # Generate that many volunteers.
        result = match_pipeline(volunteers, projects) # Run the matching pipeline.
        coverages.append(result["coverage"])         # Store the coverage.
    return sizes, coverages                          # Return the two lists.

def sensitivity_wskill_vs_quality() -> tuple:
    """Impacto de wskill en calidad media del match (Fig. 3 derecha)."""
    # Docstring: effect of skill weight on mean match quality.
    w_skills = np.linspace(0.1, 0.8, 20)             # 20 values from 0.1 to 0.8.
    mean_qualities = []                              # List to hold mean quality for each w_skill.
    projects = generate_projects(NUM_PROJECTS)       # Fixed set of projects.
    volunteers = generate_volunteers(50)             # Fixed pool of 50 volunteers.

    for ws in w_skills:                              # Loop over each skill weight.
        # Recalcular compatibilidad con peso variable, manteniendo suma = 1
        remaining = 1.0 - ws                         # Remaining total weight for other factors.
        wc = 0.30 / (1 - W_SKILL) * remaining        # Scale schedule weight proportionally.
        wl = 0.15 / (1 - W_SKILL) * remaining        # Scale location weight proportionally.
        we = 0.15 / (1 - W_SKILL) * remaining        # Scale experience weight proportionally.
        scores = []                                  # List to store best score per project.
        for project in projects:                     # For each project.
            best = max(                              # Find the maximum compatibility among all volunteers.
                ws * v["skill_score"] + wc * v["schedule_score"] +
                wl * v["location_score"] + we * v["experience_score"]
                for v in volunteers
            )
            scores.append(best)                      # Store the best score for this project.
        mean_qualities.append(np.mean(scores))       # Mean of best scores across projects.
    return w_skills, mean_qualities                  # Return the two lists.

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Main function: runs scenarios, generates figures 1,2,3."""
    print("=" * 60)                                  # Print a separator line.
    print("  Simulation 1: Discrete-Event Matching Pipeline")  # Print title.
    print("  Community Education Volunteer Coordination Platform")  # Print subtitle.
    print("=" * 60)                                  # Print separator.

    # ── Ejecutar los 3 escenarios ─────────────────────────────────────────────
    scenario_results = {}                            # Dictionary to store results for each scenario.
    for name, n_vol in SCENARIOS.items():            # Iterate over scenarios (Baseline, Optimistic, Stress).
        data = run_scenario_over_weeks(n_vol, NUM_PROJECTS, SIMULATION_WEEKS)  # Run weekly simulation.
        scenario_results[name] = data                # Store the data.

        # Resumen final (una corrida representativa del escenario)
        volunteers = generate_volunteers(n_vol)      # Generate volunteers for a single‑shot final match.
        projects   = generate_projects(NUM_PROJECTS) # Generate projects.
        final      = match_pipeline(volunteers, projects)  # Run one matching pipeline.

        print(f"\n{'─'*50}")                         # Print a dashed line.
        print(f"  Scenario: {name} ({n_vol} volunteers, {NUM_PROJECTS} projects)")  # Scenario header.
        print(f"    Coverage         : {final['coverage']:.0f}%")        # Print coverage.
        print(f"    C(v,p) mean      : {final['mean_compat']:.3f}")      # Print mean compatibility.
        print(f"    Cancellations    : {final['cancelled']}")            # Print cancellations.
        print(f"    Unassigned       : {final['unassigned']}")           # Print unassigned projects.
        print(f"    Mean latency     : {final['mean_latency']:.1f} ms")  # Print mean latency.
        print(f"    W2 target ≥70%   : {'✓ Validated' if final['coverage'] >= 70 else '✗ Not reached'}")  # Coverage target.
        print(f"    C(v,p) target>0.80: {'✓ Validated' if final['mean_compat'] > 0.80 else '✗ Not reached'}")  # Compatibility target.

    weeks_x = list(range(1, SIMULATION_WEEKS + 1))   # X‑axis values: weeks 1 to 12.

    # ── FIGURA 1: Comparación de escenarios (barras) ──────────────────────────
    fig1, axes1 = plt.subplots(1, 3, figsize=(14, 5))  # Create figure with 1 row, 3 columns.
    fig1.suptitle(                                    # Set overall title.
        "Figura 1 — Comparación de escenarios: Cobertura, Compatibilidad, Latencia",
        fontsize=13, fontweight="bold"
    )

    colors = {"Baseline": "#4472C4", "Optimistic": "#70AD47", "Stress": "#ED7D31"}  # Bar colors.
    names  = list(SCENARIOS.keys())                  # List of scenario names.

    # Cobertura
    ax = axes1[0]                                    # First subplot.
    coverages_bar = [np.mean(scenario_results[n]["weekly_coverage"]) for n in names]  # Mean coverage per scenario.
    bars = ax.bar(names, coverages_bar, color=[colors[n] for n in names])  # Create bar chart.
    ax.axhline(70, color="red", linestyle="--", linewidth=1.5, label="Target 70%")  # Target line.
    ax.set_ylim(0, 115)                              # Set y‑axis limits.
    ax.set_title("Cobertura (%)")                    # Subplot title.
    ax.set_ylabel("%")                               # Y‑axis label.
    ax.legend(fontsize=8)                            # Add legend.
    for bar, val in zip(bars, coverages_bar):        # Annotate each bar with its value.
        ax.text(bar.get_x() + bar.get_width()/2, val + 1, f"{val:.0f}%",
                ha="center", va="bottom", fontsize=9)

    # Compatibilidad
    ax = axes1[1]                                    # Second subplot.
    compats_bar = [np.mean(scenario_results[n]["weekly_compat"]) for n in names]  # Mean compatibility per scenario.
    bars = ax.bar(names, compats_bar, color=[colors[n] for n in names])  # Bar chart.
    ax.axhline(0.80, color="red", linestyle="--", linewidth=1.5, label="Target 0.80")  # Target line.
    ax.set_ylim(0.76, 0.92)                         # Set y‑axis limits.
    ax.set_title("Compatibilidad C(v,p) media")      # Title.
    ax.set_ylabel("Score medio")                     # Y‑axis label.
    ax.legend(fontsize=8)                            # Legend.
    for bar, val in zip(bars, compats_bar):          # Annotate bars.
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.001, f"{val:.3f}",
                ha="center", va="bottom", fontsize=9)

    # Latencia (simulada según pool)
    ax = axes1[2]                                    # Third subplot.
    lat_vals = {                                     # Compute mean latency for each scenario.
        "Baseline":   rng.normal(LATENCY_MEAN_MS, LATENCY_STD_MS, 50).mean(),
        "Optimistic": rng.normal(LATENCY_MEAN_MS, LATENCY_STD_MS, 80).mean(),
        "Stress":     rng.normal(LATENCY_MEAN_MS, LATENCY_STD_MS, 25).mean(),
    }
    bars = ax.bar(names, [lat_vals[n] for n in names], color=[colors[n] for n in names])  # Bar chart.
    ax.axhline(60000, color="red", linestyle="--", linewidth=1.5, label="NFR <60 s")  # NFR target line (60 s = 60000 ms).
    ax.set_title("Latencia media (ms)")              # Title.
    ax.set_ylabel("ms")                              # Y‑axis label.
    ax.legend(fontsize=8)                            # Legend.
    for bar, val in zip(bars, [lat_vals[n] for n in names]):  # Annotate bars.
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.3, f"{val:.1f}",
                ha="center", va="bottom", fontsize=9)

    plt.tight_layout()                               # Adjust layout to avoid overlap.
    plt.savefig("figura1_escenarios.png", dpi=150, bbox_inches="tight")  # Save figure.
    plt.close()                                      # Close the figure to free memory.

    # ── FIGURA 2: Dinámica temporal semanal (12 semanas) ─────────────────────
    fig2 = plt.figure(figsize=(14, 10))              # Create new figure.
    fig2.suptitle(                                   # Overall title.
        "Figura 2 — Dinámica temporal (12 semanas): cobertura, compatibilidad, "
        "pool y distribución de scores",
        fontsize=13, fontweight="bold"
    )
    gs = gridspec.GridSpec(2, 2, figure=fig2)        # Create 2x2 grid of subplots.

    line_styles = {"Baseline": "o-", "Optimistic": "s-", "Stress": "^-"}  # Markers and line styles.

    # Cobertura semanal
    ax = fig2.add_subplot(gs[0, 0])                  # Top‑left subplot.
    for name in names:                               # Plot coverage over weeks for each scenario.
        ax.plot(weeks_x, scenario_results[name]["weekly_coverage"],
                line_styles[name], label=name, markersize=5)
    ax.axhline(70, color="red", linestyle="--", linewidth=1.2, label="70% threshold")  # Target line.
    ax.set_title("Cobertura de proyectos (%)")       # Title.
    ax.set_xlabel("Semana")                          # X‑axis label.
    ax.set_ylabel("%")                               # Y‑axis label.
    ax.set_ylim(60, 105)                             # Y‑axis limits.
    ax.legend(fontsize=8)                            # Legend.
    ax.grid(True, alpha=0.3)                        # Light grid.

    # Compatibilidad semanal
    ax = fig2.add_subplot(gs[0, 1])                  # Top‑right subplot.
    for name in names:                               # Plot compatibility over weeks.
        ax.plot(weeks_x, scenario_results[name]["weekly_compat"],
                line_styles[name], label=name, markersize=5)
    ax.axhline(0.80, color="red", linestyle="--", linewidth=1.2)  # Target line.
    ax.set_title("Compatibilidad C(v,p) media")      # Title.
    ax.set_xlabel("Semana")                          # X‑axis label.
    ax.set_ylabel("Score")                           # Y‑axis label.
    ax.set_ylim(0.79, 0.92)                          # Y‑axis limits.
    ax.legend(fontsize=8)                            # Legend.
    ax.grid(True, alpha=0.3)                        # Light grid.

    # Fluctuación del pool (solo Baseline para claridad)
    ax = fig2.add_subplot(gs[1, 0])                  # Bottom‑left subplot.
    ax.plot(weeks_x, scenario_results["Baseline"]["weekly_pool"],
            "o-", color=colors["Baseline"], markersize=5, label="Baseline")  # Plot pool size.
    ax.set_title("Fluctuación del pool de voluntarios (Baseline)")  # Title.
    ax.set_xlabel("Semana")                          # X‑axis label.
    ax.set_ylabel("Voluntarios activos")             # Y‑axis label.
    ax.grid(True, alpha=0.3)                        # Light grid.
    ax.legend(fontsize=8)                            # Legend.

    # Distribución de scores (histograma Baseline)
    ax = fig2.add_subplot(gs[1, 1])                  # Bottom‑right subplot.
    all_s = scenario_results["Baseline"]["all_scores"]  # All compatibility scores.
    ax.hist(all_s, bins=20, color=colors["Baseline"], edgecolor="white", alpha=0.85)  # Histogram.
    ax.axvline(0.80, color="red", linestyle="--", linewidth=1.5, label="Target 0.80")  # Target line.
    ax.set_title("Distribución de compatibilidad (Baseline)")  # Title.
    ax.set_xlabel("C(v,p)")                          # X‑axis label.
    ax.set_ylabel("Frecuencia")                      # Y‑axis label.
    ax.legend(fontsize=8)                            # Legend.
    ax.grid(True, alpha=0.3)                        # Light grid.

    plt.tight_layout()                               # Adjust layout.
    plt.savefig("figura2_dinamica.png", dpi=150, bbox_inches="tight")  # Save figure.
    plt.close()                                      # Close figure.

    # ── FIGURA 3: Análisis de sensibilidad ───────────────────────────────────
    sizes_lat, lats         = sensitivity_latency_vs_pool()   # Get latency vs pool size data.
    sizes_cov, covs         = sensitivity_coverage_vs_volunteers()  # Get coverage vs volunteer count data.
    w_skills,  mean_quals   = sensitivity_wskill_vs_quality()  # Get quality vs w_skill data.

    fig3, axes3 = plt.subplots(1, 3, figsize=(15, 5))  # Create figure with 1 row, 3 columns.
    fig3.suptitle(                                    # Overall title.
        "Figura 3 — Análisis de sensibilidad: Latencia, Cobertura, Peso wskill",
        fontsize=13, fontweight="bold"
    )

    # Latencia vs pool
    axes3[0].plot(sizes_lat, lats, "o-", color="#4472C4")  # Plot latency vs pool size.
    axes3[0].axhline(60000, color="red", linestyle="--", linewidth=1.5, label="NFR <60 s")  # NFR line.
    axes3[0].set_title("Latencia vs. tamaño del pool")    # Title.
    axes3[0].set_xlabel("Voluntarios")                    # X‑axis label.
    axes3[0].set_ylabel("Latencia (ms)")                  # Y‑axis label.
    axes3[0].legend(fontsize=8)                           # Legend.
    axes3[0].grid(True, alpha=0.3)                       # Light grid.

    # Cobertura vs voluntarios
    axes3[1].plot(sizes_cov, covs, "o-", color="#70AD47")  # Plot coverage vs volunteer count.
    axes3[1].axhline(70, color="red", linestyle="--", linewidth=1.5, label="70% target")  # Target line.
    axes3[1].axvline(30, color="orange", linestyle=":", linewidth=1.5, label="Umbral crítico 30")  # Critical threshold.
    axes3[1].set_title("Sensibilidad de cobertura vs. voluntarios")  # Title.
    axes3[1].set_xlabel("Voluntarios")                    # X‑axis label.
    axes3[1].set_ylabel("Cobertura (%)")                  # Y‑axis label.
    axes3[1].legend(fontsize=8)                           # Legend.
    axes3[1].grid(True, alpha=0.3)                       # Light grid.

    # wskill vs calidad
    axes3[2].plot(w_skills, mean_quals, "-", color="#ED7D31", linewidth=2)  # Plot quality vs w_skill.
    axes3[2].axvline(0.40, color="blue", linestyle="--", linewidth=1.5, label="W2: wskill=0.40")  # W2 weight.
    axes3[2].axvline(0.55, color="red",  linestyle=":",  linewidth=1.5, label="Degradación >0.55")  # Degradation threshold.
    axes3[2].set_title("Impacto de wskill en calidad de match")  # Title.
    axes3[2].set_xlabel("wskill")                          # X‑axis label.
    axes3[2].set_ylabel("Calidad media")                   # Y‑axis label.
    axes3[2].legend(fontsize=8)                            # Legend.
    axes3[2].grid(True, alpha=0.3)                        # Light grid.

    plt.tight_layout()                                     # Adjust layout.
    plt.savefig("figura3_sensibilidad.png", dpi=150, bbox_inches="tight")  # Save figure.
    plt.close()                                            # Close figure.

    print("\n" + "=" * 60)                                 # Print separator.
    print("  Generated figures:")                          # Print message.
    print("    figura1_escenarios.png")               # List generated file.
    print("    figura2_dinamica.png")                 # List generated file.
    print("    figura3_sensibilidad.png")             # List generated file.
    print("=" * 60)                                        # Print separator.

if __name__ == "__main__":                               # Standard Python guard.
    main()                                               # Execute main function when script is run directly.