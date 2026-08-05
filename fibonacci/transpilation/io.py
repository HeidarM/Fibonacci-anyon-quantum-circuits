import json
from dataclasses import asdict
from pathlib import Path

from qiskit import qpy

from fibonacci.transpilation.circuit_info import (
    TranspileResult,
    TranspileStats,
    TranspiledCircuit,
)


QPY_FILENAME = "circuits.qpy"
METADATA_FILENAME = "metadata.json"


def path_slug(text):
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    return "_".join(part for part in slug.split("_") if part)


def _backend_label(backend):
    if isinstance(backend, str):
        return backend

    name = getattr(backend, "name", None)
    return name() if callable(name) else str(name)


def _stats_to_dict(stats):
    return asdict(stats)


def _stats_from_dict(data):
    return TranspileStats(
        seed=data["seed"],
        two_qubit_gates=data["two_qubit_gates"],
        depth=data["depth"],
        one_qubit_gates=data["one_qubit_gates"],
    )


def _mapping_to_json(mapping):
    return [[logical, physical] for logical, physical in mapping]


def _mapping_from_json(mapping):
    return [(logical, physical) for logical, physical in mapping]


def _transpiled_circuit_to_dict(transpiled):
    """Convert a TranspiledCircuit into a metadata dict."""

    return {
        "stats": _stats_to_dict(transpiled.stats),
        "mapping": _mapping_to_json(transpiled.mapping),
    }


def _transpiled_circuit_from_dict(circuit, data):
    """Make a TranspiledCircuit from a QPY circuit and metadata dict."""

    return TranspiledCircuit(
        circuit=circuit,
        mapping=_mapping_from_json(data["mapping"]),
        stats=_stats_from_dict(data["stats"]),
    )


def saved_best_score(directory):
    """Read the best saved score, or return None if no saved result exists."""

    directory = Path(directory)
    metadata_path = directory / METADATA_FILENAME
    qpy_path = directory / QPY_FILENAME

    if not metadata_path.exists() or not qpy_path.exists():
        return None

    try:
        with metadata_path.open() as f:
            metadata = json.load(f)
        return _stats_from_dict(metadata["best"]["stats"]).score
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def save_transpile_result(result, directory, extra_metadata=None):
    """Save best and worst circuits with a readable metadata file."""

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    with (directory / QPY_FILENAME).open("wb") as f:
        qpy.dump([result.best.circuit, result.worst.circuit], f)

    metadata = {
        "best": _transpiled_circuit_to_dict(result.best),
        "worst": _transpiled_circuit_to_dict(result.worst),
        "seeds_tried": result.seeds_tried,
        "extra_metadata": extra_metadata or {},
    }

    with (directory / METADATA_FILENAME).open("w") as f:
        json.dump(metadata, f, indent=2)


def save_transpile_result_if_better(result, directory, extra_metadata=None):
    """Save result only when its best circuit beats the saved best circuit."""

    current_score = result.best.stats.score
    previous_score = saved_best_score(directory)

    if previous_score is not None and current_score >= previous_score:
        return False

    save_transpile_result(result, directory, extra_metadata=extra_metadata)
    return True


def load_transpile_result(directory):
    """Load a saved best and worst transpilation result."""

    directory = Path(directory)

    with (directory / METADATA_FILENAME).open() as f:
        metadata = json.load(f)

    with (directory / QPY_FILENAME).open("rb") as f:
        circuits = qpy.load(f)

    if len(circuits) != 2:
        raise ValueError(f"Expected two circuits in {QPY_FILENAME}, found {len(circuits)}.")

    return TranspileResult(
        best=_transpiled_circuit_from_dict(circuits[0], metadata["best"]),
        worst=_transpiled_circuit_from_dict(circuits[1], metadata["worst"]),
        seeds_tried=metadata["seeds_tried"],
    )


def saved_circuit_dir(save_dir, backend, circuit_label, layout="auto"):
    """Return the saved transpilation directory for a circuit."""

    if layout not in ("auto", "manual"):
        raise ValueError('layout must be "auto" or "manual".')

    return (
        Path(save_dir)
        / path_slug(_backend_label(backend))
        / path_slug(circuit_label)
        / layout
    )


def load_saved_best_circuit(save_dir, backend, circuit_label, layout="auto"):
    """Load a saved best circuit, or return None when no saved result exists."""

    result_dir = saved_circuit_dir(
        save_dir,
        backend,
        circuit_label,
        layout=layout,
    )

    if not (result_dir / METADATA_FILENAME).exists() or not (result_dir / QPY_FILENAME).exists():
        return None

    return load_transpile_result(result_dir).best.circuit
