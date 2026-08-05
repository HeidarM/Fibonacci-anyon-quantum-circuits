import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetBox, OffsetImage
from matplotlib.patches import FancyBboxPatch

from fibonacci.transpilation.io import METADATA_FILENAME, path_slug


AUTO_QUBIT_COLOR = "#1976B9"
MANUAL_QUBIT_COLOR = "#D97721"

FIGURE_THEMES = {
    "light": {
        "background": "#FFFFFF",
        "ink": "#000000",
        "muted": "#000000",
        "grid": "#AEB7C1",
        "idle_node": "#B9C3CD",
        "idle_edge": "#99A6B2",
        "idle_edge_alpha": 0.72,
        "metric_bar_alpha": 0.34,
    },
    "dark": {
        "background": "#000000",
        "ink": "#FFFFFF",
        "muted": "#FFFFFF",
        "grid": "#66727F",
        "idle_node": "#6F7E8D",
        "idle_edge": "#768696",
        "idle_edge_alpha": 0.84,
        "metric_bar_alpha": 0.58,
    },
}

FIGURE_FORMATS = {"png", "svg"}

COST_METRICS = [
    ("Two-qubit gates", "two_qubit_gates"),
    ("Circuit depth", "depth"),
    ("One-qubit gates", "one_qubit_gates"),
]


@dataclass(frozen=True)
class BackendTopology:
    coordinates: dict[int, tuple[float, float]]
    edges: tuple[tuple[int, int], ...]


def num_qubits(backend):
    n = getattr(backend, "num_qubits", None)
    if n is not None:
        return int(n)
    return int(backend.configuration().num_qubits)


def backend_display_name(name):
    name = str(name).replace("_", " ").strip()
    if name.lower().startswith("ibm "):
        return f"IBM {name[4:].title()}"
    return name.title()


def backend_dirs_to_plot(save_dir, backend_dir_names=None):
    if backend_dir_names is None:
        if not save_dir.exists():
            return []
        return sorted(path for path in save_dir.iterdir() if path.is_dir())

    return [save_dir / path_slug(name) for name in backend_dir_names]


def load_metadata(result_dir):
    metadata_path = result_dir / METADATA_FILENAME
    if not metadata_path.exists():
        return None

    with metadata_path.open() as f:
        return json.load(f)


def metadata_choice(auto, manual, key):
    for metadata in (auto, manual):
        if metadata is None:
            continue
        value = metadata.get("extra_metadata", {}).get(key)
        if value is not None:
            return value
    return None


def circuit_label(circuit_dir, auto, manual):
    return metadata_choice(auto, manual, "circuit_label") or circuit_dir.name.replace(
        "_", " "
    )


def saved_circuit_rows(backend_dir, circuit_sort_key=None):
    rows = []
    for circuit_dir in sorted(path for path in backend_dir.iterdir() if path.is_dir()):
        auto = load_metadata(circuit_dir / "auto")
        manual = load_metadata(circuit_dir / "manual")

        if auto is None and manual is None:
            continue

        rows.append(
            {
                "dir": circuit_dir,
                "label": circuit_label(circuit_dir, auto, manual),
                "auto": auto,
                "manual": manual,
            }
        )

    if circuit_sort_key is None:
        return sorted(rows, key=lambda row: row["label"].lower())
    return sorted(rows, key=circuit_sort_key)


def best_stats(metadata):
    return metadata["best"]["stats"]


def best_mapping(metadata):
    return [
        (int(logical), int(physical))
        for logical, physical in metadata["best"]["mapping"]
    ]


def best_seed(metadata):
    return best_stats(metadata)["seed"]


def saved_variants(row):
    variants = []
    if row["auto"] is not None:
        variants.append(("auto", "Automatic", row["auto"], AUTO_QUBIT_COLOR))
    if row["manual"] is not None:
        variants.append(
            ("manual", "Specified initial", row["manual"], MANUAL_QUBIT_COLOR)
        )
    return variants


def default_cost_row_label(label):
    return label


def default_logical_label(logical, _row):
    return rf"$q_{{{logical}}}$"


def normalize_output_choices(values, allowed, name):
    if isinstance(values, str):
        values = (values,)
    else:
        values = tuple(values)

    if not values:
        raise ValueError(f"Choose at least one figure {name}.")

    invalid = [value for value in values if value not in allowed]
    if invalid:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"Unknown figure {name}: {invalid}. Choose from: {choices}.")

    return tuple(dict.fromkeys(values))


def save_themed_figure(
    fig,
    light_stem,
    theme_name,
    formats=("png", "svg"),
    dpi=220,
    transparent_background=True,
):
    if theme_name not in FIGURE_THEMES:
        raise ValueError(f"Unknown figure theme: {theme_name}")

    formats = normalize_output_choices(formats, FIGURE_FORMATS, "format")
    background = FIGURE_THEMES[theme_name]["background"]
    light_stem = Path(light_stem)
    stem = (
        light_stem
        if theme_name == "light"
        else light_stem.with_name(f"{light_stem.name}_{theme_name}")
    )
    stem.parent.mkdir(parents=True, exist_ok=True)

    if transparent_background:
        fig.patch.set_alpha(0)
    else:
        fig.patch.set_facecolor(background)
        fig.patch.set_alpha(1)

    paths = []
    try:
        for figure_format in formats:
            figure_path = stem.with_suffix(f".{figure_format}")
            save_kwargs = {
                "dpi": dpi,
                "transparent": transparent_background,
                "bbox_inches": "tight",
            }
            if not transparent_background:
                save_kwargs["facecolor"] = background
            fig.savefig(figure_path, **save_kwargs)
            paths.append(figure_path)
    finally:
        plt.close(fig)

    return paths


def metadata_values(rows, key):
    values = set()
    for row in rows:
        for _, _, metadata, _ in saved_variants(row):
            value = metadata.get("extra_metadata", {}).get(key)
            if value is not None:
                values.add(value)
    return values


def cost_footer(backend_name, backend_qubit_count, rows):
    parts = [backend_display_name(backend_name)]
    if backend_qubit_count is not None:
        parts.append(f"{backend_qubit_count} qubits")

    optimization_levels = metadata_values(rows, "optimization_level")
    if len(optimization_levels) == 1:
        parts.append(f"optimization level {optimization_levels.pop()}")
    elif len(optimization_levels) > 1:
        levels = ", ".join(str(level) for level in sorted(optimization_levels))
        parts.append(f"optimization levels {levels}")

    return " · ".join(parts)


def make_circuit_cost_comparison(
    backend_name,
    rows,
    cost_row_label=None,
    *,
    backend_qubit_count=None,
    theme_name="light",
    row_header="Circuit",
    title="Transpilation cost by circuit",
    context_label=None,
    row_thumbnail_for=None,
):
    if theme_name not in FIGURE_THEMES:
        raise ValueError(f"Unknown figure theme: {theme_name}")
    if not rows:
        raise ValueError("Cannot draw a cost comparison without saved circuit rows.")

    theme = FIGURE_THEMES[theme_name]
    cost_row_label = cost_row_label or default_cost_row_label
    grouped_variants = [(row, saved_variants(row)) for row in rows]
    grouped_variants = [
        (row, variants) for row, variants in grouped_variants if variants
    ]
    line_count = sum(len(variants) for _, variants in grouped_variants)
    if line_count == 0:
        raise ValueError("No saved automatic or specified-layout results were found.")

    row_thumbnails = {}
    if row_thumbnail_for is not None:
        for row, _ in grouped_variants:
            thumbnail = row_thumbnail_for(row["label"], theme_name)
            if thumbnail is None:
                continue
            if isinstance(thumbnail, (str, Path)):
                thumbnail = plt.imread(thumbnail)
            row_thumbnails[id(row)] = thumbnail

    metric_maxima = {}
    for _, metric_key in COST_METRICS:
        values = [
            int(best_stats(metadata)[metric_key])
            for _, variants in grouped_variants
            for _, _, metadata, _ in variants
        ]
        metric_maxima[metric_key] = max(values, default=1) or 1

    figure_height = max(4.65, 2.20 + 0.38 * line_count)
    with plt.rc_context({"text.color": theme["ink"], "font.size": 10.5}):
        fig, ax = plt.subplots(figsize=(13.5, figure_height))
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        header_y = 0.945
        if line_count == 1:
            line_centers = [0.49]
        else:
            step = min(0.095, 0.67 / (line_count - 1))
            line_top = 0.49 + step * (line_count - 1) / 2
            line_centers = [line_top - step * index for index in range(line_count)]

        has_row_thumbnails = bool(row_thumbnails)
        group_label_x = 0.038 if has_row_thumbnails else 0.065
        group_thumbnail_x = 0.108
        group_header_x = 0.080 if has_row_thumbnails else group_label_x
        strategy_dot_x = 0.172
        strategy_text_x = 0.189
        seed_x = 0.435
        metric_cells = {
            "two_qubit_gates": (0.505, 0.125),
            "depth": (0.675, 0.125),
            "one_qubit_gates": (0.845, 0.125),
        }

        ax.text(
            group_header_x,
            header_y,
            row_header,
            ha="center",
            va="center",
            color=theme["muted"],
            fontsize=9,
            fontweight="semibold",
        )
        ax.text(
            strategy_text_x,
            header_y,
            "Qubit placement",
            ha="left",
            va="center",
            color=theme["muted"],
            fontsize=9,
            fontweight="semibold",
        )
        ax.text(
            seed_x,
            header_y,
            "Seed",
            ha="center",
            va="center",
            color=theme["muted"],
            fontsize=9,
            fontweight="semibold",
        )
        for metric_title, metric_key in COST_METRICS:
            x_start, width = metric_cells[metric_key]
            ax.text(
                x_start + width / 2,
                header_y,
                metric_title,
                ha="center",
                va="center",
                color=theme["muted"],
                fontsize=9,
                fontweight="semibold",
            )

        ax.plot([0.015, 0.985], [0.895, 0.895], color=theme["grid"], linewidth=1.0)
        for x_value in (0.145, 0.405, 0.475, 0.655, 0.825):
            ax.plot(
                [x_value, x_value],
                [0.105, 0.975],
                color=theme["grid"],
                linewidth=0.65,
                alpha=0.72,
            )

        line_index = 0
        for group_index, (row, variants) in enumerate(grouped_variants):
            group_centers = line_centers[line_index : line_index + len(variants)]
            group_center = sum(group_centers) / len(group_centers)
            ax.text(
                group_label_x,
                group_center,
                cost_row_label(row["label"]),
                ha="center",
                va="center",
                fontsize=10.8 if has_row_thumbnails else 12,
                color=theme["ink"],
            )

            thumbnail = row_thumbnails.get(id(row))
            if thumbnail is not None:
                if isinstance(thumbnail, OffsetBox):
                    thumbnail_box = thumbnail
                else:
                    thumbnail_box = OffsetImage(
                        thumbnail,
                        zoom=0.15,
                        interpolation="lanczos",
                        resample=True,
                    )
                thumbnail_artist = AnnotationBbox(
                    thumbnail_box,
                    (group_thumbnail_x, group_center),
                    xycoords=ax.transData,
                    frameon=False,
                    pad=0,
                    box_alignment=(0.5, 0.5),
                    zorder=4,
                )
                ax.add_artist(thumbnail_artist)

            for _, variant_label, metadata, color in variants:
                stats = best_stats(metadata)
                row_y = line_centers[line_index]
                line_index += 1

                ax.scatter(
                    [strategy_dot_x],
                    [row_y],
                    s=34,
                    color=color,
                    edgecolors="none",
                    zorder=3,
                )
                ax.text(
                    strategy_text_x,
                    row_y,
                    variant_label,
                    ha="left",
                    va="center",
                    fontsize=9.8,
                    color=theme["ink"],
                )
                ax.text(
                    seed_x,
                    row_y,
                    str(stats["seed"]),
                    ha="center",
                    va="center",
                    fontsize=9.8,
                    color=theme["ink"],
                    fontweight="semibold",
                )

                for _, metric_key in COST_METRICS:
                    x_start, width = metric_cells[metric_key]
                    value = int(stats[metric_key])
                    cell_height = 0.052
                    ax.add_patch(
                        FancyBboxPatch(
                            (x_start, row_y - cell_height / 2),
                            width,
                            cell_height,
                            boxstyle="round,pad=0,rounding_size=0.008",
                            facecolor=theme["grid"],
                            edgecolor="none",
                            alpha=0.22,
                        )
                    )
                    ax.add_patch(
                        FancyBboxPatch(
                            (x_start, row_y - cell_height / 2),
                            width * value / metric_maxima[metric_key],
                            cell_height,
                            boxstyle="round,pad=0,rounding_size=0.008",
                            facecolor=color,
                            edgecolor="none",
                            alpha=theme["metric_bar_alpha"],
                        )
                    )
                    ax.text(
                        x_start + width - 0.008,
                        row_y,
                        f"{value:,}",
                        ha="right",
                        va="center",
                        fontsize=9.6,
                        color=theme["ink"],
                        fontweight="semibold",
                    )

            if group_index < len(grouped_variants) - 1:
                previous_center = line_centers[line_index - 1]
                next_center = line_centers[line_index]
                separator_y = (previous_center + next_center) / 2
                ax.plot(
                    [0.015, 0.985],
                    [separator_y, separator_y],
                    color=theme["grid"],
                    linewidth=0.72,
                    alpha=0.82,
                )

        fig.suptitle(
            title,
            x=0.5,
            y=0.985,
            fontsize=16,
            fontweight="semibold",
            color=theme["ink"],
        )
        variant_kinds = {
            variant_kind
            for row, variants in grouped_variants
            for variant_kind, _, _, _ in variants
        }
        if variant_kinds == {"auto", "manual"}:
            placement_description = (
                "Automatic qubit placement versus a specified initial layout"
            )
        elif variant_kinds == {"auto"}:
            placement_description = "Automatic qubit placement"
        else:
            placement_description = "Specified initial layout"

        subtitle_parts = [placement_description]
        if context_label:
            subtitle_parts.append(context_label)
        subtitle_parts.append("lower is better")
        fig.text(
            0.5,
            0.925,
            " · ".join(subtitle_parts),
            ha="center",
            va="center",
            fontsize=10.5,
            color=theme["muted"],
        )
        fig.text(
            0.5,
            0.025,
            cost_footer(backend_name, backend_qubit_count, rows),
            ha="center",
            va="center",
            fontsize=8.5,
            color=theme["muted"],
        )
        fig.subplots_adjust(left=0.045, right=0.98, top=0.84, bottom=0.11)
        return fig


def save_cost_figures(
    save_dir,
    backend_name,
    backend_qubit_count,
    rows,
    cost_row_label=None,
    *,
    themes=("light", "dark"),
    formats=("png", "svg"),
    row_header="Circuit",
    title="Transpilation cost by circuit",
    context_label=None,
    transparent_background=True,
    row_thumbnail_for=None,
):
    if not rows:
        return []

    themes = normalize_output_choices(themes, FIGURE_THEMES, "theme")
    formats = normalize_output_choices(formats, FIGURE_FORMATS, "format")
    light_stem = Path(save_dir) / f"{backend_name}_circuit_cost_comparison"
    paths = []

    for theme_name in themes:
        fig = make_circuit_cost_comparison(
            backend_name,
            rows,
            cost_row_label=cost_row_label,
            backend_qubit_count=backend_qubit_count,
            theme_name=theme_name,
            row_header=row_header,
            title=title,
            context_label=context_label,
            row_thumbnail_for=row_thumbnail_for,
        )
        paths.extend(
            save_themed_figure(
                fig,
                light_stem,
                theme_name,
                formats=formats,
                transparent_background=transparent_background,
            )
        )

    return paths


def save_cost_figure(save_dir, backend_name, rows, cost_row_label=None):
    """Compatibility wrapper that writes the historical light PNG output."""

    paths = save_cost_figures(
        save_dir,
        backend_name,
        None,
        rows,
        cost_row_label=cost_row_label,
        themes=("light",),
        formats=("png",),
    )
    return paths[0] if paths else None


def backend_topology(backend):
    try:
        configuration = backend.configuration()
    except (AttributeError, TypeError) as error:
        raise ValueError(
            "The backend does not expose a configuration with qubit coordinates."
        ) from error

    raw_coordinates = getattr(configuration, "coords", None)
    if raw_coordinates is None and hasattr(configuration, "to_dict"):
        raw_coordinates = configuration.to_dict().get("coords")
    if not raw_coordinates:
        name = getattr(backend, "name", "backend")
        name = name() if callable(name) else name
        raise ValueError(f"{name} does not expose fixed qubit coordinates.")

    coordinates = {}
    for index, coordinate in enumerate(raw_coordinates):
        if len(coordinate) != 2:
            raise ValueError(f"Qubit {index} has invalid coordinates: {coordinate}")
        coordinates[index] = (float(coordinate[0]), float(coordinate[1]))

    expected_qubits = num_qubits(backend)
    if len(coordinates) != expected_qubits:
        raise ValueError(
            f"The backend has {expected_qubits} qubits but exposes "
            f"{len(coordinates)} coordinate pairs."
        )
    if len(set(coordinates.values())) != len(coordinates):
        raise ValueError("The backend exposes duplicate qubit coordinates.")

    coupling_map = getattr(backend, "coupling_map", None)
    if coupling_map is not None and hasattr(coupling_map, "get_edges"):
        raw_edges = coupling_map.get_edges()
    else:
        raw_edges = getattr(configuration, "coupling_map", None)
    if raw_edges is None and hasattr(configuration, "to_dict"):
        raw_edges = configuration.to_dict().get("coupling_map")
    if raw_edges is None:
        raise ValueError("The backend does not expose a coupling map.")

    edges = set()
    for raw_edge in raw_edges:
        if len(raw_edge) != 2:
            raise ValueError(f"Invalid coupling-map edge: {raw_edge}")
        source, target = (int(raw_edge[0]), int(raw_edge[1]))
        if source == target:
            continue
        if source not in coordinates or target not in coordinates:
            raise ValueError(
                f"Coupling-map edge {(source, target)} references an unknown qubit."
            )
        edges.add(tuple(sorted((source, target))))

    return BackendTopology(coordinates=coordinates, edges=tuple(sorted(edges)))


def mapping_dict(mapping, topology):
    normalized = {int(logical): int(physical) for logical, physical in mapping}
    if len(normalized) != len(mapping):
        raise ValueError("A saved mapping contains duplicate logical qubits.")
    if len(set(normalized.values())) != len(normalized):
        raise ValueError("A saved mapping contains duplicate physical qubits.")

    missing = sorted(set(normalized.values()) - set(topology.coordinates))
    if missing:
        raise ValueError(
            f"A saved mapping references unknown physical qubits: {missing}"
        )
    return normalized


def manual_initial_layout(row, manual_initial_layout_for_saved_circuit):
    return metadata_choice(
        row["auto"], row["manual"], "manual_initial_layout"
    ) or manual_initial_layout_for_saved_circuit(row["dir"].name)


def draw_mapping_panel(
    ax,
    topology,
    mapping,
    color,
    theme,
    title,
    details,
    bounds,
    row,
    logical_label_for,
):
    coordinates = topology.coordinates
    active_physical = set(mapping.values())

    for source, target in topology.edges:
        x_values = [coordinates[source][0], coordinates[target][0]]
        y_values = [coordinates[source][1], coordinates[target][1]]
        ax.plot(
            x_values,
            y_values,
            color=theme["idle_edge"],
            linewidth=0.72,
            alpha=theme["idle_edge_alpha"],
            zorder=1,
        )
        if source in active_physical and target in active_physical:
            ax.plot(
                x_values,
                y_values,
                color=color,
                linewidth=2.25,
                solid_capstyle="round",
                zorder=2,
            )

    nodes = sorted(coordinates)
    ax.scatter(
        [coordinates[node][0] for node in nodes],
        [coordinates[node][1] for node in nodes],
        s=16,
        color=theme["idle_node"],
        edgecolors="none",
        zorder=3,
    )

    active_size = 112 if len(mapping) <= 6 else 68
    active_font_size = 6.2 if len(mapping) <= 6 else 4.8
    for logical, physical in sorted(mapping.items()):
        x_value, y_value = coordinates[physical]
        ax.scatter(
            [x_value],
            [y_value],
            s=active_size,
            color=color,
            edgecolors=theme["ink"],
            linewidths=0.65,
            zorder=5,
        )
        ax.text(
            x_value,
            y_value,
            logical_label_for(logical, row),
            ha="center",
            va="center",
            fontsize=active_font_size,
            color="white",
            fontweight="semibold",
            zorder=6,
        )

    x_min, x_max, y_min, y_max = bounds
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(title, fontsize=12.2, color=color, fontweight="semibold", pad=27)
    ax.text(
        0.5,
        1.015,
        details,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.2,
        color=theme["muted"],
    )


def make_layout_comparison(
    backend_name,
    backend_qubit_count,
    topology,
    row,
    manual_initial_layout_for_saved_circuit,
    *,
    theme_name="light",
    logical_label_for=None,
    row_label=None,
    context_label=None,
):
    if theme_name not in FIGURE_THEMES:
        raise ValueError(f"Unknown figure theme: {theme_name}")
    logical_label_for = logical_label_for or default_logical_label
    row_label = row_label or default_cost_row_label
    theme = FIGURE_THEMES[theme_name]

    panels = []
    if row["manual"] is not None:
        initial_layout = manual_initial_layout(
            row,
            manual_initial_layout_for_saved_circuit,
        )
        initial_mapping = mapping_dict(list(enumerate(initial_layout)), topology)
        panels.append(
            (
                initial_mapping,
                MANUAL_QUBIT_COLOR,
                "Specified input layout",
                "before transpilation",
            )
        )

    if row["auto"] is not None:
        auto_stats = best_stats(row["auto"])
        panels.append(
            (
                mapping_dict(best_mapping(row["auto"]), topology),
                AUTO_QUBIT_COLOR,
                "Automatic placement result",
                f"seed {auto_stats['seed']} · {auto_stats['two_qubit_gates']} 2Q gates · depth {auto_stats['depth']}",
            )
        )

    if row["manual"] is not None:
        manual_stats = best_stats(row["manual"])
        panels.append(
            (
                mapping_dict(best_mapping(row["manual"]), topology),
                MANUAL_QUBIT_COLOR,
                "Result from specified input",
                f"seed {manual_stats['seed']} · {manual_stats['two_qubit_gates']} 2Q gates · depth {manual_stats['depth']}",
            )
        )

    if not panels:
        raise ValueError("No saved automatic or specified-layout result was found.")

    x_coordinates = [coordinate[0] for coordinate in topology.coordinates.values()]
    y_coordinates = [coordinate[1] for coordinate in topology.coordinates.values()]
    bounds = (
        min(x_coordinates) - 0.55,
        max(x_coordinates) + 0.55,
        min(y_coordinates) - 0.55,
        max(y_coordinates) + 0.55,
    )

    with plt.rc_context({"text.color": theme["ink"], "font.size": 10.5}):
        fig, axes = plt.subplots(
            1, len(panels), figsize=(4.9 * len(panels), 5.75), squeeze=False
        )
        fig.patch.set_alpha(0)
        for ax, (mapping, color, panel_title, details) in zip(axes.flat, panels):
            ax.set_facecolor("none")
            draw_mapping_panel(
                ax,
                topology,
                mapping,
                color,
                theme,
                panel_title,
                details,
                bounds,
                row,
                logical_label_for,
            )

        title_parts = [backend_display_name(backend_name), row_label(row["label"])]
        if context_label:
            title_parts.append(context_label)
        fig.suptitle(
            " · ".join(title_parts),
            y=0.975,
            fontsize=15.5,
            fontweight="semibold",
            color=theme["ink"],
        )
        fig.text(
            0.5,
            0.020,
            f"Complete {backend_qubit_count}-qubit backend topology",
            ha="center",
            va="center",
            fontsize=8.7,
            color=theme["muted"],
        )
        fig.subplots_adjust(
            left=0.018, right=0.992, top=0.78, bottom=0.075, wspace=0.09
        )
        return fig


def save_layout_figures(
    backend,
    backend_dir,
    rows,
    manual_initial_layout_for_saved_circuit,
    *,
    themes=("light", "dark"),
    formats=("png", "svg"),
    logical_label_for=None,
    row_label=None,
    context_label=None,
    transparent_background=True,
):
    if not rows:
        return []

    themes = normalize_output_choices(themes, FIGURE_THEMES, "theme")
    formats = normalize_output_choices(formats, FIGURE_FORMATS, "format")
    topology = backend_topology(backend)
    backend_qubit_count = num_qubits(backend)
    paths = []

    for row in rows:
        light_stem = backend_dir / f"{row['dir'].name}_layout_comparison"
        for theme_name in themes:
            fig = make_layout_comparison(
                backend_dir.name,
                backend_qubit_count,
                topology,
                row,
                manual_initial_layout_for_saved_circuit,
                theme_name=theme_name,
                logical_label_for=logical_label_for,
                row_label=row_label,
                context_label=context_label,
            )
            paths.extend(
                save_themed_figure(
                    fig,
                    light_stem,
                    theme_name,
                    formats=formats,
                    transparent_background=transparent_background,
                )
            )

    return paths
