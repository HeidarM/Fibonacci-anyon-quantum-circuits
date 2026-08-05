"""Render compact TikZ braids as vector Matplotlib thumbnail artists."""

import hashlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

from matplotlib.offsetbox import DrawingArea
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MatplotlibPath


_GENERATOR_PATTERN = re.compile(r"s(i)?([1-9][0-9]*)\Z")
_SVG_TOKEN_PATTERN = re.compile(
    r"[MLCZ]|[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?"
)
_MATRIX_PATTERN = re.compile(r"matrix\(([^)]+)\)")
_THEMES = {"light", "dark"}


class BraidThumbnailError(RuntimeError):
    """Raised when a braid thumbnail cannot be rendered."""


@dataclass(frozen=True)
class BraidVectorGeometry:
    """Normalized vector paths extracted from a TikZ-generated SVG."""

    paths: tuple[MatplotlibPath, ...]
    aspect_ratio: float

    def drawing_area(self, theme_name, *, max_width=27, max_height=43):
        """Return a fixed-size vector artist suitable for ``AnnotationBbox``."""

        if theme_name not in _THEMES:
            raise ValueError(f"Unknown braid-thumbnail theme: {theme_name}")

        width = min(max_width, max_height * self.aspect_ratio)
        height = width / self.aspect_ratio
        ink = "white" if theme_name == "dark" else "black"
        drawing = DrawingArea(width, height, clip=False)

        for path in self.paths:
            vertices = [
                (x_coordinate * width, y_coordinate * height)
                for x_coordinate, y_coordinate in path.vertices
            ]
            scaled_path = MatplotlibPath(vertices, path.codes)
            drawing.add_artist(
                PathPatch(
                    scaled_path,
                    facecolor="none",
                    edgecolor=ink,
                    linewidth=1.05,
                    capstyle="round",
                    joinstyle="round",
                )
            )

        return drawing


def normalize_braid_word(word, number_of_strands):
    """Validate and normalize compact generators such as ``s2`` and ``si1``."""

    if isinstance(word, str):
        stripped = word.strip()
        if stripped.lower() in {"", "i", "identity"}:
            generators = ()
        else:
            generators = tuple(
                generator.strip()
                for generator in stripped.split(",")
                if generator.strip()
            )
    else:
        generators = tuple(str(generator).strip() for generator in word)

    if number_of_strands < 2:
        raise ValueError("A braid diagram needs at least two strands.")

    for generator in generators:
        match = _GENERATOR_PATTERN.fullmatch(generator)
        if match is None:
            raise ValueError(
                f"Invalid braid generator {generator!r}; use s1, s2, si1, si2, ..."
            )
        index = int(match.group(2))
        if index >= number_of_strands:
            raise ValueError(
                f"Generator {generator!r} is invalid for "
                f"{number_of_strands} strands."
            )

    return generators


def default_braid_thumbnail_cache():
    """Return the generated-thumbnail cache outside the repository."""

    return Path(tempfile.gettempdir()) / "fibonacci_braid_thumbnails"


def _template_path():
    return Path(__file__).with_name("latex") / "braid_thumbnail.tex"


def _cache_key(template, generators, number_of_strands):
    digest = hashlib.sha256()
    digest.update(template.read_bytes())
    digest.update(str(number_of_strands).encode())
    digest.update(",".join(generators).encode())
    digest.update(b"vector-svg-v1")
    return digest.hexdigest()[:20]


def _run(command, *, cwd):
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired as error:
        raise BraidThumbnailError(
            f"Braid-thumbnail command timed out: {' '.join(command)}"
        ) from error
    if completed.returncode == 0:
        return

    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    tail = "\n".join(output.splitlines()[-18:])
    raise BraidThumbnailError(
        f"Braid-thumbnail command failed: {' '.join(command)}\n{tail}"
    )


def _parse_svg_path(path_data):
    tokens = _SVG_TOKEN_PATTERN.findall(path_data)
    vertices = []
    codes = []
    index = 0
    command = None

    def coordinate_pair():
        nonlocal index
        if index + 1 >= len(tokens):
            raise BraidThumbnailError("Malformed coordinate pair in braid SVG.")
        pair = (float(tokens[index]), float(tokens[index + 1]))
        index += 2
        return pair

    while index < len(tokens):
        token = tokens[index]
        if token in {"M", "L", "C", "Z"}:
            command = token
            index += 1
        elif command is None:
            raise BraidThumbnailError("Malformed path command in braid SVG.")

        if command == "M":
            vertices.append(coordinate_pair())
            codes.append(MatplotlibPath.MOVETO)
            command = "L"
        elif command == "L":
            vertices.append(coordinate_pair())
            codes.append(MatplotlibPath.LINETO)
        elif command == "C":
            for _ in range(3):
                vertices.append(coordinate_pair())
                codes.append(MatplotlibPath.CURVE4)
        elif command == "Z":
            vertices.append((0.0, 0.0))
            codes.append(MatplotlibPath.CLOSEPOLY)
            command = None
        else:
            raise BraidThumbnailError(
                f"Unsupported path command {command!r} in braid SVG."
            )

    return vertices, codes


def _svg_matrix(transform):
    if not transform:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    match = _MATRIX_PATTERN.fullmatch(transform.strip())
    if match is None:
        raise BraidThumbnailError(f"Unsupported SVG transform: {transform}")
    values = tuple(float(value) for value in match.group(1).replace(",", " ").split())
    if len(values) != 6:
        raise BraidThumbnailError(f"Malformed SVG transform: {transform}")
    return values


@lru_cache(maxsize=128)
def _load_vector_geometry(svg_path):
    svg_path = Path(svg_path)
    root = ElementTree.parse(svg_path).getroot()
    view_box = root.get("viewBox")
    if view_box is None:
        raise BraidThumbnailError("The braid SVG does not define a viewBox.")

    x_min, y_min, width, height = (float(value) for value in view_box.split())
    if width <= 0 or height <= 0:
        raise BraidThumbnailError(f"Invalid braid SVG viewBox: {view_box}")

    namespace = root.tag.partition("}")[0].lstrip("{")
    path_tag = f"{{{namespace}}}path" if namespace else "path"
    paths = []
    for element in root.iter(path_tag):
        if element.get("stroke") is None:
            continue

        vertices, codes = _parse_svg_path(element.get("d", ""))
        a, b, c, d, e, f = _svg_matrix(element.get("transform"))
        normalized_vertices = []
        for x_coordinate, y_coordinate in vertices:
            transformed_x = a * x_coordinate + c * y_coordinate + e
            transformed_y = b * x_coordinate + d * y_coordinate + f
            normalized_vertices.append(
                (
                    (transformed_x - x_min) / width,
                    1.0 - (transformed_y - y_min) / height,
                )
            )
        paths.append(MatplotlibPath(normalized_vertices, codes))

    if not paths:
        raise BraidThumbnailError("The braid SVG contains no stroked paths.")
    return BraidVectorGeometry(tuple(paths), width / height)


def _render_svg(generators, number_of_strands, cache_dir):
    template = _template_path()
    if not template.exists():
        raise BraidThumbnailError(f"Missing TikZ braid template: {template}")

    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_path = cache_dir / (
        f"braid_{_cache_key(template, generators, number_of_strands)}.svg"
    )
    if cached_path.exists():
        return cached_path

    pdflatex = shutil.which("pdflatex")
    pdftocairo = shutil.which("pdftocairo")
    if pdflatex is None:
        raise BraidThumbnailError("pdflatex is required to render braid thumbnails.")
    if pdftocairo is None:
        raise BraidThumbnailError(
            "pdftocairo is required to convert braid thumbnails to SVG."
        )

    with tempfile.TemporaryDirectory(prefix="fibonacci_braid_") as build_dir:
        build_dir = Path(build_dir)
        wrapper_path = build_dir / "render_braid.tex"
        generated_svg_path = build_dir / "render_braid.svg"
        word_definition = ",".join(generators)
        border_height = "0.90cm" if not generators else "0.42cm"
        wrapper_path.write_text(
            f"\\def\\BraidNumberOfStrands{{{number_of_strands}}}\n"
            + f"\\def\\BraidWord{{{word_definition}}}\n"
            + f"\\def\\BraidBorderHeight{{{border_height}}}\n"
            + "\\input{braid_thumbnail.tex}\n"
        )

        _run(
            [
                pdflatex,
                "-no-shell-escape",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-output-directory={build_dir}",
                str(wrapper_path),
            ],
            cwd=template.parent,
        )
        _run(
            [
                pdftocairo,
                "-svg",
                str(build_dir / "render_braid.pdf"),
                str(generated_svg_path),
            ],
            cwd=build_dir,
        )
        generated_svg_path.replace(cached_path)

    return cached_path


def render_braid_thumbnail(
    word,
    *,
    number_of_strands=4,
    theme_name="light",
    cache_dir=None,
):
    """Compile a TikZ braid and return a crisp vector thumbnail artist."""

    if theme_name not in _THEMES:
        raise ValueError(f"Unknown braid-thumbnail theme: {theme_name}")
    generators = normalize_braid_word(word, number_of_strands)
    cache_dir = Path(cache_dir or default_braid_thumbnail_cache())
    svg_path = _render_svg(generators, number_of_strands, cache_dir)
    return _load_vector_geometry(str(svg_path)).drawing_area(theme_name)
