# fibonacci/main_scripts/levin_wen_lattice/levin_wen_hardware_groundstate_checks.py

# Run from root folder as:
# python -m fibonacci.main_scripts.levin_wen_lattice.levin_wen_hardware_groundstate_checks

from pathlib import Path

from fibonacci.constraints.plaquette import measure_Bp_sampling
from fibonacci.constraints.vertex import compute_all_Qv_from_probs
from fibonacci.geometry.three_plaquette import vertices
from fibonacci.measurements.sampling import sample_circuit
from fibonacci.models.levin_wen_lattice import fibonacci_ground_state
from fibonacci.transpilation.optimization import transpile_for_backend
from fibonacci.visualization.constraint_plot import plot_three_plaquette_constraints


# Set this to False if you only want to load saved data and plot/print it.
RUN_HARDWARE = False

BACKEND_NAME = None       # If None, choose least busy.
SHOTS = 20_000
OPTIMIZATION_LEVEL = 3
RUNS_TO_PRINT = 5

DATA_DIR = Path(__file__).resolve().parent / "data"
VERTEX_FILE = DATA_DIR / "vertex_constraints.csv"
PLAQUETTE_FILE = DATA_DIR / "plaquette_constraints.csv"


def choose_backend():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    if BACKEND_NAME is not None:
        return service.backend(BACKEND_NAME)
    return service.least_busy(simulator=False, operational=True, min_num_qubits=19)


def measure_vertex_constraints(qc, backend):
    qc_vertices = qc.copy()
    qc_vertices.measure_all()
    tqc_vertices = transpile_for_backend(
        qc_vertices,
        backend,
        optimization_level=OPTIMIZATION_LEVEL,
    )

    P, job_id = sample_circuit(tqc_vertices, backend, shots=SHOTS)
    P = {bits[::-1]: p for bits, p in P.items()}

    return compute_all_Qv_from_probs(P, vertices)


def measure_plaquette_constraints(qc, backend):
    Bp_values = []
    for plaquette in ["A", "B", "C"]:
        Bp, _ = measure_Bp_sampling(
            qc,
            backend,
            plaquette=plaquette,
            shots=SHOTS,
            optimization_level=OPTIMIZATION_LEVEL,
        )
        Bp_values.append(Bp)
    return Bp_values


def save_data(Qv, Bp_values):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with VERTEX_FILE.open("a") as f:
        f.write(",".join(str(value) for value in Qv) + "\n")
    with PLAQUETTE_FILE.open("a") as f:
        f.write(",".join(str(value) for value in Bp_values) + "\n")


def load_data():
    Qv_runs = [
        [float(x) for x in line.split(",")]
        for line in VERTEX_FILE.read_text().splitlines()[-RUNS_TO_PRINT:]
    ]
    Bp_runs = [
        [float(x) for x in line.split(",")]
        for line in PLAQUETTE_FILE.read_text().splitlines()[-RUNS_TO_PRINT:]
    ]
    return Qv_runs, Bp_runs


if __name__ == "__main__":

    if RUN_HARDWARE:
        backend = choose_backend()
        qc = fibonacci_ground_state()

        print("Backend:", backend.name)

        print("Running vertex measurements...")
        Qv = measure_vertex_constraints(qc, backend)

        print("Running plaquette measurements...")
        Bp_values = measure_plaquette_constraints(qc, backend)
        save_data(Qv, Bp_values)

        print("Saved:", VERTEX_FILE)
        print("Saved:", PLAQUETTE_FILE)

    Qv_runs, Bp_runs = load_data()
    Qv = Qv_runs[-1]
    Bp_values = Bp_runs[-1]

    title = "Hardware ground-state constraints"
    print("\n" + title)
    print("=" * len(title))

    title = "1. Vertex constraints Q_v:"
    print("\n" + title)
    print("-" * len(title))
    for v in range(len(Qv)):
        values = " ".join(f"{run[v]:.4f}" for run in Qv_runs)
        print(f"<Q_{v}> \t= {values}")
    print("-" * len(title))

    title = "2. Plaquette constraints B_p:"
    print("\n" + title)
    print("-" * len(title))
    for i, p in enumerate(["A", "B", "C"]):
        values = " ".join(f"{run[i]:.4f}" for run in Bp_runs)
        print(f"⟨ψ|B_{p}|ψ⟩ = {values}")
        print()
    print("-" * len(title))

    plot_three_plaquette_constraints(
        Qv,
        Bp_values,
        title="Levin-Wen Fibonacci Hardware Ground-State Check",
        show_edge_labels=True,
    )
