# fibonacci/main_scripts/topological_code/fibonacci_topological_computations_hardware.py

# Run from root folder as:
# python -m fibonacci.main_scripts.topological_code.fibonacci_topological_computations_hardware

import json
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

from fibonacci.diagnostics.state_inspection import print_fusion_stats_bits
from fibonacci.measurements.distributions import postselect_distribution
from fibonacci.measurements.sampling import sample_circuit
from fibonacci.models.topological_code import fibonacci_code
from fibonacci.transpilation.circuit_info import one_qubit_gate_count, two_qubit_gate_count
from fibonacci.transpilation.io import load_saved_best_circuit
from fibonacci.transpilation.optimization import transpile_for_backend
from fibonacci.transpilation.transpile_study import backend_name, get_backend


MODEL_NAME = "topological_code"
TRANSPILED_CIRCUITS_DIR = Path(__file__).resolve().parents[2] / "transpiled_circuits"
SAVE_DIR = TRANSPILED_CIRCUITS_DIR / MODEL_NAME
DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_FILE = DATA_DIR / "topological_computations.jsonl"

BACKEND_NAME = None  # Set to a backend name like "kingston", or None for least busy.
SHOTS = 4000
OPTIMIZATION_LEVEL = 3
SAVED_LAYOUT = "auto"  # "auto" or "manual"
ANYON_PAIRS = 2
TOPOLOGICAL_GATES = ["s2"] # use s1, s2... and si1 and si2 for inverse gates. Empty list [], just creates and annihilates anyons.


# --- Gates from Fibonacci braidings ---

# Approximation to Hadamard gate
hadamard = [
    "s1", "s1", "s1", "s1",
    "si2", "si2",
    "s1", "s1",
    "si2", "si2",
    "s1", "s1",
    "s2", "s2",
    "si1", "si1",
    "s2", "s2", "s2", "s2",
    "s1", "s1",
    "si2", "si2",
    "si1", "si1",
    "s2", "s2",
    "s1", "s1",
]

Z_gate = ["s1"] * 5
X_gate = hadamard + Z_gate + hadamard


def choose_backend():
    service = QiskitRuntimeService()
    if BACKEND_NAME is not None:
        return get_backend(service, BACKEND_NAME)
    return service.least_busy(
        simulator=False,
        operational=True,
        min_num_qubits=2 * ANYON_PAIRS,
    )


def topological_gate_set_name(topological_gates):
    if not topological_gates:
        return "identity"
    return "_".join(topological_gates)


def hardware_circuit_label(topological_gates, anyon_pairs):
    return f"{topological_gate_set_name(topological_gates)}\n{anyon_pairs} pairs"


def circuit_for_hardware(qc, backend, circuit_label):
    tqc = load_saved_best_circuit(
        SAVE_DIR,
        backend,
        circuit_label,
        layout=SAVED_LAYOUT,
    )

    clean_label = circuit_label.replace("\n", " ")
    if tqc is not None:
        print(f"Loaded saved {SAVED_LAYOUT} transpilation: {clean_label}")
        return tqc

    print(f"No saved {SAVED_LAYOUT} transpilation found: {clean_label}")
    print("Transpiling for backend now.")
    return transpile_for_backend(
        qc,
        backend,
        optimization_level=OPTIMIZATION_LEVEL,
    )


def save_data(result):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS_FILE.open("a") as f:
        f.write(json.dumps(result) + "\n")


if __name__ == "__main__":

    backend = choose_backend()

    print("Chosen backend:", backend_name(backend))
    print("Status:", backend.status())

    circuit_label = hardware_circuit_label(TOPOLOGICAL_GATES, ANYON_PAIRS)
    qc = fibonacci_code(num_pairs=ANYON_PAIRS, topological_gates=TOPOLOGICAL_GATES)

    tqc = circuit_for_hardware(qc, backend, circuit_label)
    print("Depth:", tqc.depth())
    print("2Q gates:", two_qubit_gate_count(tqc))
    print("1Q gates:", one_qubit_gate_count(tqc))

    # --- This part runs on quantum computer ---
    P_raw, job_id = sample_circuit(tqc, backend, shots=SHOTS)
    P = postselect_distribution(P_raw, qubit_index=-1, value=0)

    save_data(
        {
            "backend": backend_name(backend),
            "shots": SHOTS,
            "anyon_pairs": ANYON_PAIRS,
            "topological_gates": TOPOLOGICAL_GATES,
            "circuit_label": circuit_label,
            "job_id": job_id,
            "saved_layout": SAVED_LAYOUT,
            "depth": tqc.depth(),
            "two_qubit_gates": two_qubit_gate_count(tqc),
            "one_qubit_gates": one_qubit_gate_count(tqc),
            "raw_distribution": P_raw,
            "postselected_distribution": P,
        }
    )
    print("Saved:", RESULTS_FILE)

    print("Fusion statistics (total fusion -> vacuum):")
    print_fusion_stats_bits(P, numbered=True)
    print()
