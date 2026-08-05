# fibonacci/main_scripts/levin_wen_lattice/ibm_backend_topology_generate_figures.py

# Run from root folder as:
# python -m fibonacci.main_scripts.levin_wen_lattice.ibm_backend_topology_generate_figures

from qiskit_ibm_runtime import QiskitRuntimeService

from fibonacci.main_scripts.levin_wen_lattice.ibm_backend_topology_study import (
    SAVE_DIR,
    manual_initial_layout_for_saved_circuit,
)
from fibonacci.transpilation.transpile_figures import (
    backend_dirs_to_plot,
    num_qubits,
    save_cost_figures,
    save_layout_figures,
    saved_circuit_rows,
)
from fibonacci.transpilation.transpile_study import get_backend


BACKEND_DIR_NAMES = None  # None means every backend folder under SAVE_DIR.
FIGURE_THEMES = ("light",)  # Replace with "light" for a light-mode figure.
FIGURE_FORMATS = ("png",)  # Add "svg" to generate a vector variant.
TRANSPARENT_BACKGROUND = False  # False uses white for light mode and black for dark.
FIGURE_CONTEXT = "Fibonacci Levin–Wen lattice"

MEASUREMENT_LABELS = {
    "vertex constraints measurement": "Vertex constraints",
    "plaquette a measurement": "Plaquette A",
    "plaquette b measurement": "Plaquette B",
    "plaquette c measurement": "Plaquette C",
}

COST_MEASUREMENT_LABELS = {
    "vertex constraints measurement": "Vertex constraints\n$\\langle Q_v\\rangle$",
    "plaquette a measurement": "Plaquette A\n$\\langle B_A\\rangle$",
    "plaquette b measurement": "Plaquette B\n$\\langle B_B\\rangle$",
    "plaquette c measurement": "Plaquette C\n$\\langle B_C\\rangle$",
}


def circuit_sort_key(row):
    label = row["label"].lower()
    if "vertex" in label:
        return (0, label)
    if "plaquette a" in label:
        return (1, label)
    if "plaquette b" in label:
        return (2, label)
    if "plaquette c" in label:
        return (3, label)
    return (4, label)


def cost_row_label(label):
    return COST_MEASUREMENT_LABELS.get(label.lower(), label)


def layout_row_label(label):
    return MEASUREMENT_LABELS.get(label.lower(), label)


def logical_qubit_label(logical, _row):
    if logical < 15:
        return rf"$e_{{{logical}}}$"
    if logical < 18:
        return rf"$u_{{{logical - 15}}}$"
    if logical == 18:
        return r"$h$"
    return rf"$q_{{{logical}}}$"


if __name__ == "__main__":
    service = None
    backend_dirs = backend_dirs_to_plot(SAVE_DIR, BACKEND_DIR_NAMES)
    if not backend_dirs:
        print(f"No saved transpile results found in {SAVE_DIR}")

    for backend_dir in backend_dirs:
        if not backend_dir.exists():
            print(f"Missing saved backend folder: {backend_dir}")
            continue

        print()
        print("=" * 80)
        print(f"Backend folder: {backend_dir.name}")
        print("=" * 80)

        rows = saved_circuit_rows(backend_dir, circuit_sort_key=circuit_sort_key)
        if not rows:
            print(f"No saved circuit results found in {backend_dir}")
            continue

        if service is None:
            service = QiskitRuntimeService()
        backend = get_backend(service, backend_dir.name)

        cost_paths = save_cost_figures(
            SAVE_DIR,
            backend_dir.name,
            num_qubits(backend),
            rows,
            cost_row_label=cost_row_label,
            themes=FIGURE_THEMES,
            formats=FIGURE_FORMATS,
            row_header="Measurement",
            title="Transpilation cost by measurement circuit",
            context_label=FIGURE_CONTEXT,
            transparent_background=TRANSPARENT_BACKGROUND,
        )
        for path in cost_paths:
            print(f"Saved cost figure:   {path}")

        layout_paths = save_layout_figures(
            backend,
            backend_dir,
            rows,
            manual_initial_layout_for_saved_circuit,
            themes=FIGURE_THEMES,
            formats=FIGURE_FORMATS,
            logical_label_for=logical_qubit_label,
            row_label=layout_row_label,
            context_label=FIGURE_CONTEXT,
            transparent_background=TRANSPARENT_BACKGROUND,
        )
        for path in layout_paths:
            print(f"Saved layout figure: {path}")
