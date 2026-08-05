# fibonacci/main_scripts/levin_wen_lattice/ibm_backend_topology_study.py

# Run from root folder as:
# python -m fibonacci.main_scripts.levin_wen_lattice.ibm_backend_topology_study

from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

from circuits.hadamard_test import hadamard_test
from fibonacci.gates.anyonic_gates import Bp_tau_gate
from fibonacci.models.levin_wen_lattice import fibonacci_ground_state
from fibonacci.transpilation.transpile_study import (
    backend_name,
    get_backend,
    optimize_circuit_suite,
    print_backend_results,
    save_best_transpile_results,
)


BACKEND_NAMES = ["kingston", "fez", "marrakesh"] # ["kingston"] # ["kingston", "fez", "marrakesh"]
MODEL_NAME = "levin_wen_lattice"
TRANSPILED_CIRCUITS_DIR = Path(__file__).resolve().parents[2] / "transpiled_circuits"
SAVE_DIR = TRANSPILED_CIRCUITS_DIR / MODEL_NAME
SAVE_BEST_RESULTS = True
BEST_RESULTS_DIR = SAVE_DIR
OPTIMIZATION_LEVEL = 3
TRANSPILER_SEEDS = range(0, 50)
RUN_VERTEX_CIRCUIT = True
PLAQUETTES_TO_OPTIMIZE = ["A", "B", "C"]  # e.g. ["A"], ["B", "C"], or []
LAYOUTS_TO_OPTIMIZE = "both"  # "both", "auto", or "manual"

# Manual qubit mapping layout.
# Entry i means: logical qubit i -> this physical qubit.
# MANUAL_VERTEX_LAYOUT = [
#     52, 53, 54, 55, 59, 39,
#     33, 34, 35, 19, 15, 14,
#     12, 11, 10, 18, 30, 31,
# ]

# Try 1
# MANUAL_VERTEX_LAYOUT = [
#     96, 104, 84, 117, 126, 106,
#     86, 97, 128, 108, 88, 118,
#     110, 90, 98, 107, 109, 87,
# ]

# # Try 2
# MANUAL_VERTEX_LAYOUT = [
#     117, 105, 86, 126, 127, 106,
#     87, 97, 128, 108, 88, 118,
#     110, 89, 111, 129, 109, 107
# ]

# Layout for optimized circuit (no center qubit)
MANUAL_VERTEX_LAYOUT = [
    126, 127, 109, 137, 147, 128,
    118, 129, 148, 130, 110, 131,
    132, 111, 133, 119, 113, 112
]


# Auto final
# MANUAL_VERTEX_LAYOUT = [
#     57, 50, 26, 38, 51, 44,
#     25, 46, 58, 37, 41, 47,
#     45, 42, 56, 49, 43, 48,
# ]


# Extra physical qubit for the Hadamard-test ancilla in plaquette measurements.
MANUAL_HADAMARD_ANCILLA = 32


def normalized_plaquettes():
    plaquettes = [plaquette.upper() for plaquette in PLAQUETTES_TO_OPTIMIZE]
    invalid = [plaquette for plaquette in plaquettes if plaquette not in ("A", "B", "C")]
    if invalid:
        raise ValueError(f"Unknown plaquette labels: {invalid}. Use only A, B, and C.")

    if len(set(plaquettes)) != len(plaquettes):
        raise ValueError("PLAQUETTES_TO_OPTIMIZE contains duplicate plaquettes.")

    return plaquettes


def manual_initial_layout_for_saved_circuit(circuit_label):
    manual_layout = validated_manual_vertex_layout()
    if "plaquette" in circuit_label:
        return manual_layout + [MANUAL_HADAMARD_ANCILLA]
    return manual_layout


def circuit_cost_suite():
    circuits = []

    if RUN_VERTEX_CIRCUIT:
        qc_vertex = fibonacci_ground_state()
        qc_vertex.measure_all()
        circuits.append(("vertex constraints\nmeasurement", qc_vertex))

    for plaquette in normalized_plaquettes():
        qc_plaquette = hadamard_test(
            fibonacci_ground_state(),
            Bp_tau_gate(plaquette=plaquette),
        )
        circuits.append((f"plaquette {plaquette}\nmeasurement", qc_plaquette))

    if not circuits:
        raise ValueError("Choose at least one circuit to optimize.")

    return circuits


def validated_manual_vertex_layout():
    manual_vertex_layout = globals().get("MANUAL_VERTEX_LAYOUT")
    if manual_vertex_layout is None:
        raise ValueError("MANUAL_VERTEX_LAYOUT must be defined when manual optimization is enabled.")

    if len(manual_vertex_layout) != 18:
        raise ValueError("MANUAL_VERTEX_LAYOUT must have exactly 18 entries.")

    if len(set(manual_vertex_layout)) != len(manual_vertex_layout):
        raise ValueError("MANUAL_VERTEX_LAYOUT contains duplicate physical qubits.")

    return list(manual_vertex_layout)


def manual_initial_layout_for(qc):
    manual_vertex_layout = validated_manual_vertex_layout()

    if qc.num_qubits == 18:
        return manual_vertex_layout

    if qc.num_qubits == 19:
        if MANUAL_HADAMARD_ANCILLA in manual_vertex_layout:
            raise ValueError("MANUAL_HADAMARD_ANCILLA is already used in MANUAL_VERTEX_LAYOUT.")
        return manual_vertex_layout + [MANUAL_HADAMARD_ANCILLA]

    raise ValueError(f"No manual layout configured for {qc.num_qubits} qubits.")


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
