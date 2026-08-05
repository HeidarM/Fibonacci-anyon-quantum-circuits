# fibonacci/main_scripts/topological_code/ibm_backend_topology_study.py

# Run from root folder as:
# python -m fibonacci.main_scripts.topological_code.ibm_backend_topology_study

from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

from fibonacci.models.topological_code import fibonacci_code
from fibonacci.transpilation.transpile_study import (
    backend_name,
    get_backend,
    optimize_circuit_suite,
    print_backend_results,
    save_best_transpile_results,
)


BACKEND_NAMES = ["kingston", "fez", "marrakesh"] # ["kingston", "fez", "marrakesh"]
MODEL_NAME = "topological_code"
TRANSPILED_CIRCUITS_DIR = Path(__file__).resolve().parents[2] / "transpiled_circuits"
SAVE_DIR = TRANSPILED_CIRCUITS_DIR / MODEL_NAME
SAVE_BEST_RESULTS = True
BEST_RESULTS_DIR = SAVE_DIR
OPTIMIZATION_LEVEL = 3
TRANSPILER_SEEDS = range(0, 200)
LAYOUTS_TO_OPTIMIZE = "both"  # "both", "auto", or "manual"

# Fixed for this topology study.
ANYON_PAIRS = 2

# Logical qubit order for num_pairs=2 is:
#   0 = a[0], 1 = a[1], 2 = p[0], 3 = p[1]
# Entry i means: logical qubit i -> this physical qubit.
MANUAL_LAYOUT = [126, 127, 109, 137]

TOPOLOGICAL_GATE_SETS = [
    ("identity", []),
    ("s2", ["s2"]),
    ("s2_s1", ["s2", "s1"]),
    ("s2_s1_s2", ["s2", "s1", "s2"]),
]


def circuit_cost_suite():
    circuits = []

    for gate_set_name, topological_gates in TOPOLOGICAL_GATE_SETS:
        qc = fibonacci_code(
            num_pairs=ANYON_PAIRS,
            topological_gates=topological_gates,
        )
        circuits.append((f"{gate_set_name}\n{ANYON_PAIRS} pairs", qc))

    if not circuits:
        raise ValueError("Choose at least one topological gate set to optimize.")

    return circuits


def validated_manual_layout():
    manual_layout = globals().get("MANUAL_LAYOUT")
    if manual_layout is None:
        raise ValueError("MANUAL_LAYOUT must be defined when manual optimization is enabled.")

    expected_qubits = 2 * ANYON_PAIRS
    if len(manual_layout) != expected_qubits:
        raise ValueError(f"MANUAL_LAYOUT must have exactly {expected_qubits} entries.")

    if len(set(manual_layout)) != len(manual_layout):
        raise ValueError("MANUAL_LAYOUT contains duplicate physical qubits.")

    return list(manual_layout)


def manual_initial_layout_for(qc):
    manual_layout = validated_manual_layout()

    if qc.num_qubits != len(manual_layout):
        raise ValueError(
            f"No manual layout configured for {qc.num_qubits} qubits. "
            f"MANUAL_LAYOUT has {len(manual_layout)} entries."
        )

    return manual_layout


def manual_initial_layout_for_saved_circuit(_circuit_label):
    return validated_manual_layout()


if __name__ == "__main__":
    service = QiskitRuntimeService()
    backend_runs = []

    for name in BACKEND_NAMES:
        backend = get_backend(service, name)
        name = backend_name(backend)

        print()
        print("=" * 80)
        print(f"Backend: {name}")
        print("=" * 80)
        print("Optimizing selected circuits...")

        rows = optimize_circuit_suite(
            backend,
            circuit_cost_suite(),
            seeds=TRANSPILER_SEEDS,
            layouts_to_optimize=LAYOUTS_TO_OPTIMIZE,
            optimization_level=OPTIMIZATION_LEVEL,
            manual_initial_layout_for=manual_initial_layout_for,
        )

        save_statuses = []
        if SAVE_BEST_RESULTS:
            save_statuses = save_best_transpile_results(
                name,
                rows,
                BEST_RESULTS_DIR,
                model_name=MODEL_NAME,
                optimization_level=OPTIMIZATION_LEVEL,
                seeds=TRANSPILER_SEEDS,
                manual_initial_layout_for_saved_circuit=manual_initial_layout_for_saved_circuit,
            )

        for result_path, saved in save_statuses:
            if saved:
                print(f"Saved better result: {result_path}")
            else:
                print(f"Kept saved result:   {result_path}")

        backend_runs.append((name, save_statuses, rows))

    print()
    print("#" * 80)
    print("Final optimization results")
    print("#" * 80)
    for name, _, rows in backend_runs:
        print_backend_results(name, rows)
