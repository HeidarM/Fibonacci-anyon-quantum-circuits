# For plotting the three-plaquette honeycomb and placing <Q_v> and <B_p> ground-state constraint values on it.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, to_rgba
from matplotlib.patches import Circle, Polygon
from matplotlib.lines import Line2D


SQRT3 = np.sqrt(3.0)

VERTEX_COORDS = {
    0: (-0.5, 1.5 * SQRT3),
    1: (0.5, 1.5 * SQRT3),
    2: (-2.0, SQRT3),
    3: (-1.0, SQRT3),
    4: (1.0, SQRT3),
    5: (-2.5, 0.5 * SQRT3),
    6: (-0.5, 0.5 * SQRT3),
    7: (0.5, 0.5 * SQRT3),
    8: (-2.0, 0.0),
    9: (-1.0, 0.0),
    10: (1.0, 0.0),
    11: (-0.5, -0.5 * SQRT3),
    12: (0.5, -0.5 * SQRT3),
}

EDGE_VERTEX_PAIRS = {
    0: (0, 1),
    1: (0, 3),
    2: (1, 4),
    3: (2, 3),
    4: (2, 5),
    5: (3, 6),
    6: (4, 7),
    7: (6, 7),
    8: (5, 8),
    9: (6, 9),
    10: (7, 10),
    11: (8, 9),
    12: (9, 11),
    13: (10, 12),
    14: (11, 12),
}

PLAQUETTE_VERTEX_CYCLES = (
    (2, 3, 6, 9, 8, 5),      # A, left plaquette
    (6, 7, 10, 12, 11, 9),   # B, lower-right plaquette
    (0, 1, 4, 7, 6, 3),      # C, top plaquette
)

BOUNDARY_LEG_DIRECTIONS = {
    0: (-0.5, SQRT3 / 2.0),
    1: (0.5, SQRT3 / 2.0),
    2: (-0.5, SQRT3 / 2.0),
    4: (1.0, 0.0),
    5: (-1.0, 0.0),
    8: (-0.5, -SQRT3 / 2.0),
    10: (1.0, 0.0),
    11: (-0.5, -SQRT3 / 2.0),
    12: (0.5, -SQRT3 / 2.0),
}


def plot_three_plaquette_constraints(
    Qv,
    Bp,
    *,
    ax=None,
    title="Levin-Wen Fibonacci Ground-State Check",
    missing_value=-1,
    show=True,
    save_path=None,
    dpi=200,
    show_edge_labels=True,
):

    qv_values = _as_value_list(Qv, 13, "Qv")
    bp_values = _as_value_list(Bp, 3, "Bp")

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 7), dpi=120)
    else:
        fig = ax.figure

    norm = Normalize(vmin=0.0, vmax=1.0, clip=True)
    vertex_cmap = plt.get_cmap("Greens")
    plaquette_cmap = plt.get_cmap("Blues")

    edge_color = "#e31a1c"
    edge_label_color = "#ffe900"
    plaquette_face = "#9b95ff"
    boundary_color = "#0b4b8f"
    missing_color = "#d6d6d6"
    vertex_legend_color = vertex_cmap(norm(0.8))
    plaquette_legend_color = plaquette_cmap(norm(0.8))

    _draw_boundary_legs(ax, boundary_color)
    _draw_plaquette_backgrounds(ax, Polygon, plaquette_face)
    _draw_edges(ax, edge_color, edge_label_color, show_edge_labels)

    for vertices, value in zip(PLAQUETTE_VERTEX_CYCLES, bp_values):
        center = np.mean(np.array([VERTEX_COORDS[v] for v in vertices]), axis=0)
        _draw_value_marker(
            ax,
            center,
            value,
            radius=0.29,
            cmap=plaquette_cmap,
            norm=norm,
            missing_value=missing_value,
            missing_color=missing_color,
            Circle=Circle,
            to_rgba=to_rgba,
            zorder=4,
        )

    for vertex, value in enumerate(qv_values):
        _draw_value_marker(
            ax,
            VERTEX_COORDS[vertex],
            value,
            radius=0.22,
            cmap=vertex_cmap,
            norm=norm,
            missing_value=missing_value,
            missing_color=missing_color,
            Circle=Circle,
            to_rgba=to_rgba,
            zorder=6,
        )

    ax.set_aspect("equal")
    ax.set_axis_off()
    _set_lattice_limits(ax)

    if title:
        ax.set_title(title, pad=12, fontsize=16, weight="semibold")

    _add_legend(ax, vertex_legend_color, plaquette_legend_color)

    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight", dpi=dpi)

    if show:
        plt.show()

    return fig, ax


def _as_value_list(values, expected_length, name):
    values = [_as_float(value) for value in values]
    if len(values) != expected_length:
        raise ValueError(f"Expected {expected_length} {name} values, got {len(values)}.")
    return values


def _as_float(value):
    value = np.real_if_close(value)
    return float(value)


def _draw_boundary_legs(ax, boundary_color):
    for vertex, direction in BOUNDARY_LEG_DIRECTIONS.items():
        x, y = VERTEX_COORDS[vertex]
        dx, dy = direction
        length = 0.8
        ax.plot(
            [x, x + length * dx],
            [y, y + length * dy],
            color=boundary_color,
            lw=3,
            solid_capstyle="round",
            zorder=0,
        )


def _add_legend(ax, vertex_color, plaquette_color):
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=10,
            markerfacecolor=vertex_color,
            markeredgecolor="none",
            label=r"Vertices: $\langle Q_v \rangle$",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=12,
            markerfacecolor=plaquette_color,
            markeredgecolor="none",
            label=r"Plaquettes: $\langle B_p \rangle$",
        ),
    ]

    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.02, 0.98),
        frameon=True,
        fancybox=True,
        framealpha=0.92,
        facecolor="white",
        edgecolor="#d9d9d9",
        fontsize=10,
        borderpad=0.6,
        handletextpad=0.7,
    )


def _draw_plaquette_backgrounds(ax, Polygon, plaquette_face):
    for vertices in PLAQUETTE_VERTEX_CYCLES:
        xy = np.array([VERTEX_COORDS[v] for v in vertices])
        ax.add_patch(
            Polygon(
                xy,
                closed=True,
                facecolor=plaquette_face,
                edgecolor="none",
                alpha=0.35,
                zorder=1,
            )
        )


def _draw_edges(ax, edge_color, edge_label_color, show_edge_labels):
    for edge, (v0, v1) in EDGE_VERTEX_PAIRS.items():
        x0, y0 = VERTEX_COORDS[v0]
        x1, y1 = VERTEX_COORDS[v1]
        ax.plot(
            [x0, x1],
            [y0, y1],
            color=edge_color,
            lw=10,
            solid_capstyle="round",
            zorder=2,
        )

        if show_edge_labels:
            ax.text(
                0.5 * (x0 + x1),
                0.5 * (y0 + y1),
                str(edge + 1),
                ha="center",
                va="center",
                fontsize=10,
                weight="bold",
                color=edge_label_color,
                zorder=3,
            )


def _draw_value_marker(
    ax,
    center,
    value,
    *,
    radius,
    cmap,
    norm,
    missing_value,
    missing_color,
    Circle,
    to_rgba,
    zorder,
):
    facecolor = _value_color(value, cmap, norm, missing_value, missing_color)
    text = _value_text(value, missing_value)
    halo_radius = radius * 1.12

    ax.add_patch(
        Circle(
            center,
            halo_radius,
            facecolor=(1.0, 1.0, 1.0, 0.22),
            edgecolor="none",
            zorder=zorder - 0.2,
        )
    )

    ax.add_patch(
        Circle(
            center,
            radius,
            facecolor=facecolor,
            edgecolor="none",
            zorder=zorder,
        )
    )
    ax.text(
        center[0],
        center[1],
        text,
        ha="center",
        va="center",
        fontsize=8.5,
        weight="bold",
        color=_text_color(to_rgba(facecolor)),
        zorder=zorder + 1,
    )


def _value_color(value, cmap, norm, missing_value, missing_color):
    if _is_missing(value, missing_value):
        return missing_color
    return cmap(norm(value))


def _value_text(value, missing_value):
    if _is_missing(value, missing_value):
        return "-"
    rounded = f"{value:.2f}".rstrip("0").rstrip(".")
    if "." not in rounded:
        rounded += ".0"
    return rounded


def _is_missing(value, missing_value):
    return value == missing_value or not np.isfinite(value)


def _text_color(rgba):
    red, green, blue, _ = rgba
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "black" if luminance > 0.55 else "white"


def _set_lattice_limits(ax):
    coords = np.array(list(VERTEX_COORDS.values()))
    ax.set_xlim(coords[:, 0].min() - 0.9, coords[:, 0].max() + 0.9)
    ax.set_ylim(coords[:, 1].min() - 0.8, coords[:, 1].max() + 0.8)
