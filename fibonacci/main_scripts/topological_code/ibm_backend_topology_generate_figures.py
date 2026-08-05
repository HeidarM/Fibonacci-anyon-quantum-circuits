# fibonacci/main_scripts/topological_code/ibm_backend_topology_generate_figures.py

# Run from root folder as:
# python -m fibonacci.main_scripts.topological_code.ibm_backend_topology_generate_figures

import warnings

from qiskit_ibm_runtime import QiskitRuntimeService

from fibonacci.main_scripts.topological_code.ibm_backend_topology_study import (
    ANYON_PAIRS,
    SAVE_DIR,
    TOPOLOGICAL_GATE_SETS,
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
from fibonacci.visualization.braid_thumbnails import (
    BraidThumbnailError,
    render_braid_thumbnail,
)


BACKEND_DIR_NAMES = None  # None means every backend folder under SAVE_DIR.
FIGURE_THEMES = ("light",)  # Replace with "light" for a light-mode figure.
FIGURE_FORMATS = ("png",)  # Add "svg" to generate a vector variant.
TRANSPARENT_BACKGROUND = False  # False uses white for light mode and black for dark.
FIGURE_CONTEXT = f"{ANYON_PAIRS} Fibonacci-anyon pairs"

GATE_SET_ORDER = {
    f"{gate_set_name} {ANYON_PAIRS} pairs": index
    for index, (gate_set_name, _) in enumerate(TOPOLOGICAL_GATE_SETS)
}

BRAID_WORD_LABELS = {
    f"identity {ANYON_PAIRS} pairs": r"$I$",
    f"s2 {ANYON_PAIRS} pairs": r"$\sigma_2$",
    f"s2_s1 {ANYON_PAIRS} pairs": r"$\sigma_2\sigma_1$",
    f"s2_s1_s2 {ANYON_PAIRS} pairs": r"$\sigma_2\sigma_1\sigma_2$",
}

BRAID_WORD_GENERATORS = {
    f"{gate_set_name} {ANYON_PAIRS} pairs": tuple(generators)
    for gate_set_name, generators in TOPOLOGICAL_GATE_SETS
}

_BRAID_THUMBNAIL_WARNING_EMITTED = False

LOGICAL_QUBIT_LABELS = {
    0: r"$a_0$",
    1: r"$a_1$",
    2: r"$p_0$",
    3: r"$p_1$",
}


def circuit_sort_key(row):
    label = row["label"].lower()
    return (GATE_SET_ORDER.get(label, len(GATE_SET_ORDER)), label)


def cost_row_label(label):
    return BRAID_WORD_LABELS.get(label.lower(), label)


def logical_qubit_label(logical, _row):
    return LOGICAL_QUBIT_LABELS.get(logical, rf"$q_{{{logical}}}$")


def braid_word_thumbnail(label, theme_name):
    generators = BRAID_WORD_GENERATORS.get(label.lower())
    if generators is None:
        return None

    global _BRAID_THUMBNAIL_WARNING_EMITTED
    if _BRAID_THUMBNAIL_WARNING_EMITTED:
        return None

    try:
        return render_braid_thumbnail(
            generators,
            number_of_strands=2 * ANYON_PAIRS,
            theme_name=theme_name,
        )
    except BraidThumbnailError as error:
        if not _BRAID_THUMBNAIL_WARNING_EMITTED:
            warnings.warn(
                f"Braid thumbnails are unavailable; continuing without them: {error}",
                stacklevel=2,
            )
            _BRAID_THUMBNAIL_WARNING_EMITTED = True
        return None


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
            row_header="Braid word",
            title="Transpilation cost by braid word",
            context_label=FIGURE_CONTEXT,
            transparent_background=TRANSPARENT_BACKGROUND,
            row_thumbnail_for=braid_word_thumbnail,
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
            row_label=cost_row_label,
            context_label=FIGURE_CONTEXT,
            transparent_background=TRANSPARENT_BACKGROUND,
        )
        for path in layout_paths:
            print(f"Saved layout figure: {path}")
