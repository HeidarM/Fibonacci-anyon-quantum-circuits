from fibonacci.transpilation.formatting import (
    format_layout,
    format_spread,
    format_stats,
)
from fibonacci.transpilation.io import path_slug, save_transpile_result_if_better
from fibonacci.transpilation.optimization import optimize_circuit


def get_backend(service, name):
    """Accept either short backend names like 'fez' or full names like 'ibm_fez'."""

    try:
        return service.backend(name)
    except Exception:
        if not name.startswith("ibm_"):
            return service.backend(f"ibm_{name}")
        raise


def backend_name(backend):
    name = getattr(backend, "name", None)
    return name() if callable(name) else str(name)


def available_results(auto_result, manual_result):
    results = []
    if auto_result is not None:
        results.append(("auto", auto_result))
    if manual_result is not None:
        results.append(("manual", manual_result))
    return results


def seed_metadata(seeds):
    if isinstance(seeds, range):
        return {
            "type": "range",
            "start": seeds.start,
            "stop": seeds.stop,
            "step": seeds.step,
        }

    return {
        "type": "explicit",
        "values": list(seeds),
    }


def optimize_circuit_suite(
    backend,
    circuits,
    seeds,
    layouts_to_optimize="both",
    optimization_level=3,
    manual_initial_layout_for=None,
):
    if layouts_to_optimize not in ("both", "auto", "manual"):
        raise ValueError('layouts_to_optimize must be "both", "auto", or "manual".')

    if layouts_to_optimize in ("both", "manual") and manual_initial_layout_for is None:
        raise ValueError("manual_initial_layout_for is required for manual optimization.")

    rows = []
    for circuit_label, qc in circuits:
        clean_label = circuit_label.replace("\n", " ")
        auto_result = None
        manual_result = None

        if layouts_to_optimize in ("both", "auto"):
            auto_result = optimize_circuit(
                qc,
                backend,
                seeds=seeds,
                optimization_level=optimization_level,
                progress_label=f"{clean_label} / auto",
            )

        if layouts_to_optimize in ("both", "manual"):
            manual_result = optimize_circuit(
                qc,
                backend,
                seeds=seeds,
                initial_layout=manual_initial_layout_for(qc),
                optimization_level=optimization_level,
                progress_label=f"{clean_label} / manual",
            )

        rows.append((circuit_label, auto_result, manual_result))

    return rows


def save_best_transpile_results(
    backend_name,
    rows,
    best_results_dir,
    model_name,
    optimization_level,
    seeds,
    manual_initial_layout_for_saved_circuit=None,
):
    save_statuses = []
    backend_dir = best_results_dir / path_slug(backend_name)

    for circuit_label, auto_result, manual_result in rows:
        circuit_dir = backend_dir / path_slug(circuit_label)
        for layout_label, result in available_results(auto_result, manual_result):
            result_dir = circuit_dir / layout_label
            extra_metadata = {
                "model_name": model_name,
                "backend": backend_name,
                "circuit_label": circuit_label.replace("\n", " "),
                "layout": layout_label,
                "optimization_level": optimization_level,
                "transpiler_seeds": seed_metadata(seeds),
            }
            if manual_initial_layout_for_saved_circuit is not None:
                extra_metadata["manual_initial_layout"] = (
                    manual_initial_layout_for_saved_circuit(circuit_label)
                )

            saved = save_transpile_result_if_better(
                result,
                result_dir,
                extra_metadata=extra_metadata,
            )
            save_statuses.append((result_dir, saved))

    return save_statuses


def print_transpile_result(label, result):
    print(f"    {label}")
    print(f"      best : {format_stats(result.best.stats)}")
    print(f"      worst: {format_stats(result.worst.stats)}")
    print(f"      spread: {format_spread(result.best.stats, result.worst.stats)}")
    print(f"      seeds tried: {result.seeds_tried}")
    print("      layout:")
    print(format_layout(result.best.mapping))


def print_backend_results(name, rows):
    print()
    print("=" * 80)
    print(f"Backend: {name}")
    print("=" * 80)

    for circuit_label, auto_result, manual_result in rows:
        print()
        print(f"  {circuit_label.replace(chr(10), ' ')}")
        for label, result in available_results(auto_result, manual_result):
            print_transpile_result(label, result)
