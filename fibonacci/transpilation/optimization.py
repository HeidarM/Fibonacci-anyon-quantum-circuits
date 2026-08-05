from qiskit import transpile
from tqdm import tqdm

from fibonacci.transpilation.circuit_info import (
    TranspileResult,
    TranspiledCircuit,
    circuit_stats,
    final_logical_to_physical_mapping,
)


def transpile_for_backend(
    qc,
    backend,
    initial_layout=None,
    seed=None,
    optimization_level=3,
    routing_method="sabre",
    layout_method="sabre",
):
    """Transpile circuit qc with the chosen settings."""

    kwargs = {
        "backend": backend,
        "initial_layout": initial_layout,
        "optimization_level": optimization_level,
        "routing_method": routing_method,
    }

    if seed is not None:
        kwargs["seed_transpiler"] = seed

    if initial_layout is None and layout_method is not None:
        kwargs["layout_method"] = layout_method

    return transpile(qc, **kwargs)


def transpiled_circuit(qc, tqc, seed):
    """Attach mapping and stats to a transpiled circuit."""

    return TranspiledCircuit(
        circuit=tqc,
        mapping=final_logical_to_physical_mapping(qc, tqc),
        stats=circuit_stats(tqc, seed),
    )


def optimize_circuit(
    qc,
    backend,
    seeds,
    initial_layout=None,
    progress_label=None,
    optimization_level=3,
    routing_method="sabre",
    layout_method="sabre",
):
    """Try many seeds and keep the best and worst circuits."""

    seeds = list(seeds)
    if not seeds:
        raise ValueError("At least one transpiler seed is required.")

    best = None
    worst = None

    seed_iterator = seeds
    if progress_label is not None:
        seed_iterator = tqdm(
            seeds,
            desc=progress_label,
            unit="seed",
            dynamic_ncols=True,
        )

    for seed in seed_iterator:
        tqc = transpile_for_backend(
            qc,
            backend,
            initial_layout=initial_layout,
            seed=seed,
            optimization_level=optimization_level,
            routing_method=routing_method,
            layout_method=layout_method,
        )
        candidate = transpiled_circuit(qc, tqc, seed)

        if best is None or candidate.stats.score < best.stats.score:
            best = candidate
        if worst is None or candidate.stats.score > worst.stats.score:
            worst = candidate

    return TranspileResult(
        best=best,
        worst=worst,
        seeds_tried=len(seeds),
    )
