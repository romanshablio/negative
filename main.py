from __future__ import annotations

import argparse
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WIDTH_MM = 120.0
DEFAULT_RELIEF_HEIGHT_MM = 2.0
DEFAULT_BASE_THICKNESS_MM = 0.8
DEFAULT_LINE_WIDTH_MM = 0.4
DEFAULT_LAYER_HEIGHT_MM = 0.2
DEFAULT_FILAMENT_DIAMETER_MM = 1.75
DEFAULT_PRINT_SPEED_MMPM = 1500.0
DEFAULT_FIRST_LAYER_SPEED_MMPM = 900.0
DEFAULT_TRAVEL_SPEED_MMPM = 4800.0
DEFAULT_Z_SPEED_MMPM = 600.0
DEFAULT_Z_HOP_MM = 0.2
DEFAULT_EXTRUSION_MULTIPLIER = 1.0
DEFAULT_ORIGIN_X_MM = 10.0
DEFAULT_ORIGIN_Y_MM = 10.0
DEFAULT_GAMMA = 1.0
DEFAULT_BLUR_RADIUS = 0.6
DEFAULT_NOZZLE_TEMPERATURE_C = 205
DEFAULT_BED_TEMPERATURE_C = 60
DEFAULT_FAN_SPEED = 255
_RUNTIME_DEPS: tuple[object, object, object, object] | None = None


@dataclass(frozen=True)
class HeightmapSettings:
    input_path: Path
    width_mm: float
    depth_mm: float | None
    relief_height_mm: float
    base_thickness_mm: float
    invert: bool
    autocontrast: bool
    gamma: float
    blur_radius: float
    resolution_x: int | None
    resolution_y: int | None


@dataclass(frozen=True)
class PrintSettings:
    line_width_mm: float
    layer_height_mm: float
    filament_diameter_mm: float
    print_speed_mmpm: float
    first_layer_speed_mmpm: float
    travel_speed_mmpm: float
    z_speed_mmpm: float
    z_hop_mm: float
    extrusion_multiplier: float
    origin_x_mm: float
    origin_y_mm: float
    nozzle_temperature_c: int | None
    bed_temperature_c: int | None
    fan_speed: int


@dataclass(frozen=True)
class HeightmapResult:
    relief_map: np.ndarray
    total_heights_mm: np.ndarray
    width_mm: float
    depth_mm: float
    pitch_x_mm: float
    pitch_y_mm: float
    total_height_mm: float


@dataclass(frozen=True)
class MeshData:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]


@dataclass(frozen=True)
class GCodeStats:
    layer_count: int
    print_segments: int
    travel_moves: int
    filament_mm: float


@dataclass(frozen=True)
class GenerationSummary:
    heightmap: HeightmapResult
    heightmap_path: Path
    gcode_path: Path | None
    obj_path: Path | None
    stl_path: Path | None
    gcode_stats: GCodeStats | None
    mesh_vertices: int | None
    mesh_faces: int | None


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero.")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Value must be zero or greater.")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero.")
    return parsed


def bounded_percent(value: str) -> int:
    parsed = int(value)
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("Value must be between 0 and 255.")
    return parsed


def optional_positive_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    parsed = float(value)
    if parsed <= 0:
        raise ValueError("Value must be greater than zero.")
    return parsed


def optional_positive_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("Value must be greater than zero.")
    return parsed


def normalize_temperature(value: int | None) -> int | None:
    if value is None or value <= 0:
        return None
    return value


def required_positive_float(value: str, label: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return parsed


def required_non_negative_float(value: str, label: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise ValueError(f"{label} must be zero or greater.")
    return parsed


def load_runtime_dependencies() -> tuple[object, object, object, object]:
    global _RUNTIME_DEPS
    if _RUNTIME_DEPS is None:
        try:
            import numpy as np
            from PIL import Image, ImageFilter, ImageOps
        except ImportError as exc:
            missing_package = "Pillow" if exc.name == "PIL" else exc.name
            raise SystemExit(
                "Missing dependency: "
                f"{missing_package}. Install requirements with `python3 -m pip install -r requirements.txt`."
            ) from exc
        _RUNTIME_DEPS = (np, Image, ImageFilter, ImageOps)
    return _RUNTIME_DEPS


def preflight_python_imports() -> None:
    command = [
        sys.executable,
        "-c",
        "import numpy; from PIL import Image, ImageFilter, ImageOps",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return

    details = (result.stderr or result.stdout).strip()
    message = (
        "Python can start, but runtime dependencies cannot be loaded safely.\n"
        "This is often caused by binary wheels of numpy/Pillow that require a newer macOS.\n"
        "Try one of these options:\n"
        "1. Reinstall from source: `python3 -m pip install --no-binary=:all: --force-reinstall numpy pillow`\n"
        "2. Use Python 3.13 instead of 3.14 on older macOS.\n"
        "3. If you only need the GUI, fix the dependency install first and retry.\n"
    )
    if details:
        message += f"\nImport check output:\n{details}"
    raise SystemExit(message)


def preflight_gui() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import tkinter as tk; "
            "root = tk.Tk(); "
            "root.withdraw(); "
            "root.update_idletasks(); "
            "root.destroy()"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return

    details = (result.stderr or result.stdout).strip()
    message = (
        "GUI could not start safely.\n"
        "This usually means Tk is missing or the local Python/Tk build is incompatible with your macOS.\n"
        "You can still use CLI mode: `python3 main.py <image>`.\n"
        "For GUI mode, the most reliable fix is a Python build with working Tk support, often Python.org 3.13/3.14."
    )
    if details:
        message += f"\n\nGUI check output:\n{details}"
    raise SystemExit(message)


def default_heightmap_output(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_heightmap.png")


def default_gcode_output(input_path: Path) -> Path:
    return input_path.with_suffix(".gcode")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a negative image into a printable heightmap, mesh and layered G-code "
            "for an FDM printer."
        )
    )
    parser.add_argument(
        "input_image",
        nargs="?",
        type=Path,
        help="Path to the source image. If omitted, the GUI starts.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical interface even if an input image is provided.",
    )
    parser.add_argument(
        "--heightmap-out",
        type=Path,
        help="Output PNG with the processed heightmap preview. Defaults to <input>_heightmap.png.",
    )
    parser.add_argument(
        "--gcode-out",
        type=Path,
        help="Output G-code path. Defaults to <input>.gcode.",
    )
    parser.add_argument(
        "--obj-out",
        type=Path,
        help="Output OBJ mesh path. Not generated unless this flag is set.",
    )
    parser.add_argument(
        "--stl-out",
        type=Path,
        help="Output STL mesh path. Not generated unless this flag is set.",
    )
    parser.add_argument(
        "--no-gcode",
        action="store_true",
        help="Skip G-code generation and only export the heightmap preview and optional meshes.",
    )
    parser.add_argument(
        "--width-mm",
        type=positive_float,
        default=DEFAULT_WIDTH_MM,
        help="Physical print width in millimeters.",
    )
    parser.add_argument(
        "--depth-mm",
        type=positive_float,
        help="Physical print depth in millimeters. Defaults to image aspect ratio.",
    )
    parser.add_argument(
        "--relief-height-mm",
        type=positive_float,
        default=DEFAULT_RELIEF_HEIGHT_MM,
        help="Maximum additional relief height above the base.",
    )
    parser.add_argument(
        "--base-thickness-mm",
        type=non_negative_float,
        default=DEFAULT_BASE_THICKNESS_MM,
        help="Solid base thickness under the relief.",
    )
    parser.add_argument(
        "--line-width-mm",
        type=positive_float,
        default=DEFAULT_LINE_WIDTH_MM,
        help="Extrusion line width.",
    )
    parser.add_argument(
        "--layer-height-mm",
        type=positive_float,
        default=DEFAULT_LAYER_HEIGHT_MM,
        help="Layer height for the generated print.",
    )
    parser.add_argument(
        "--filament-diameter-mm",
        type=positive_float,
        default=DEFAULT_FILAMENT_DIAMETER_MM,
        help="Filament diameter used for extrusion calculations.",
    )
    parser.add_argument(
        "--print-speed",
        type=positive_float,
        default=DEFAULT_PRINT_SPEED_MMPM,
        help="Printing speed in mm/min for regular layers.",
    )
    parser.add_argument(
        "--first-layer-speed",
        type=positive_float,
        default=DEFAULT_FIRST_LAYER_SPEED_MMPM,
        help="Printing speed in mm/min for the first layer.",
    )
    parser.add_argument(
        "--travel-speed",
        type=positive_float,
        default=DEFAULT_TRAVEL_SPEED_MMPM,
        help="Travel speed in mm/min.",
    )
    parser.add_argument(
        "--z-speed",
        type=positive_float,
        default=DEFAULT_Z_SPEED_MMPM,
        help="Z movement speed in mm/min.",
    )
    parser.add_argument(
        "--z-hop-mm",
        type=non_negative_float,
        default=DEFAULT_Z_HOP_MM,
        help="Z-hop applied before travel moves.",
    )
    parser.add_argument(
        "--extrusion-multiplier",
        type=positive_float,
        default=DEFAULT_EXTRUSION_MULTIPLIER,
        help="Multiplier applied to extrusion volume.",
    )
    parser.add_argument(
        "--origin-x-mm",
        type=non_negative_float,
        default=DEFAULT_ORIGIN_X_MM,
        help="X origin of the print on the bed.",
    )
    parser.add_argument(
        "--origin-y-mm",
        type=non_negative_float,
        default=DEFAULT_ORIGIN_Y_MM,
        help="Y origin of the print on the bed.",
    )
    parser.add_argument(
        "--resolution-x",
        type=positive_int,
        help="Sampling columns for the heightmap. Defaults to width / line width.",
    )
    parser.add_argument(
        "--resolution-y",
        type=positive_int,
        help="Sampling rows for the heightmap. Defaults to depth / line width.",
    )
    parser.add_argument(
        "--gamma",
        type=positive_float,
        default=DEFAULT_GAMMA,
        help="Gamma correction applied after inversion.",
    )
    parser.add_argument(
        "--blur-radius",
        type=non_negative_float,
        default=DEFAULT_BLUR_RADIUS,
        help="Optional Gaussian blur radius to smooth noisy negatives.",
    )
    parser.add_argument(
        "--autocontrast",
        action="store_true",
        help="Stretch tonal range before heightmap conversion.",
    )
    parser.add_argument(
        "--no-invert",
        action="store_true",
        help="Disable inversion if the source image is already a positive heightmap.",
    )
    parser.add_argument(
        "--nozzle-temperature",
        type=int,
        default=DEFAULT_NOZZLE_TEMPERATURE_C,
        help="Nozzle temperature in Celsius. Use 0 to skip heating commands.",
    )
    parser.add_argument(
        "--bed-temperature",
        type=int,
        default=DEFAULT_BED_TEMPERATURE_C,
        help="Bed temperature in Celsius. Use 0 to skip heating commands.",
    )
    parser.add_argument(
        "--fan-speed",
        type=bounded_percent,
        default=DEFAULT_FAN_SPEED,
        help="Cooling fan PWM value from 0 to 255.",
    )
    return parser


def open_grayscale_image(input_path: Path) -> tuple[Image.Image, Image.Image]:
    _, Image, _, ImageOps = load_runtime_dependencies()
    with Image.open(input_path) as image:
        rgba = image.convert("RGBA")
    grayscale = ImageOps.grayscale(rgba.convert("RGB"))
    alpha = rgba.getchannel("A")
    return grayscale, alpha


def resolve_grid(
    image_size: tuple[int, int],
    width_mm: float,
    depth_mm: float | None,
    resolution_x: int | None,
    resolution_y: int | None,
    line_width_mm: float,
) -> tuple[int, int, float]:
    image_width_px, image_height_px = image_size
    aspect_ratio = image_height_px / image_width_px
    resolved_depth_mm = depth_mm if depth_mm is not None else width_mm * aspect_ratio

    cols = resolution_x or max(1, math.ceil(width_mm / line_width_mm))
    rows = resolution_y or max(1, math.ceil(resolved_depth_mm / line_width_mm))

    if resolution_x and not resolution_y:
        rows = max(1, round(cols * aspect_ratio))
    elif resolution_y and not resolution_x:
        cols = max(1, round(rows / aspect_ratio))

    if depth_mm is None:
        resolved_depth_mm = width_mm * rows / cols

    return cols, rows, resolved_depth_mm


def build_heightmap(
    settings: HeightmapSettings,
    line_width_mm: float,
) -> HeightmapResult:
    np, Image, ImageFilter, ImageOps = load_runtime_dependencies()
    grayscale, alpha = open_grayscale_image(settings.input_path)
    cols, rows, resolved_depth_mm = resolve_grid(
        image_size=grayscale.size,
        width_mm=settings.width_mm,
        depth_mm=settings.depth_mm,
        resolution_x=settings.resolution_x,
        resolution_y=settings.resolution_y,
        line_width_mm=line_width_mm,
    )

    if settings.blur_radius > 0:
        grayscale = grayscale.filter(ImageFilter.GaussianBlur(settings.blur_radius))

    if settings.autocontrast:
        grayscale = ImageOps.autocontrast(grayscale)

    if settings.invert:
        grayscale = ImageOps.invert(grayscale)

    grayscale = grayscale.resize((cols, rows), Image.Resampling.LANCZOS)
    alpha = alpha.resize((cols, rows), Image.Resampling.LANCZOS)

    relief_map = np.asarray(grayscale, dtype=np.float32) / 255.0
    alpha_map = np.asarray(alpha, dtype=np.float32) / 255.0
    relief_map *= alpha_map

    if settings.gamma != 1.0:
        relief_map = np.power(relief_map, settings.gamma).astype(np.float32, copy=False)

    total_heights_mm = settings.base_thickness_mm + relief_map * settings.relief_height_mm
    total_height_mm = float(total_heights_mm.max())
    pitch_x_mm = settings.width_mm / cols
    pitch_y_mm = resolved_depth_mm / rows

    return HeightmapResult(
        relief_map=relief_map,
        total_heights_mm=total_heights_mm,
        width_mm=settings.width_mm,
        depth_mm=resolved_depth_mm,
        pitch_x_mm=pitch_x_mm,
        pitch_y_mm=pitch_y_mm,
        total_height_mm=total_height_mm,
    )


def save_heightmap_preview(relief_map: np.ndarray, output_path: Path) -> None:
    np, Image, _, _ = load_runtime_dependencies()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    preview = np.clip(np.rint(relief_map * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(preview, mode="L").save(output_path)


def corner_heights_from_cells(cell_heights: np.ndarray) -> np.ndarray:
    np, _, _, _ = load_runtime_dependencies()
    corners = np.zeros((cell_heights.shape[0] + 1, cell_heights.shape[1] + 1), dtype=np.float32)
    counts = np.zeros_like(corners)

    corners[:-1, :-1] += cell_heights
    corners[:-1, 1:] += cell_heights
    corners[1:, :-1] += cell_heights
    corners[1:, 1:] += cell_heights

    counts[:-1, :-1] += 1
    counts[:-1, 1:] += 1
    counts[1:, :-1] += 1
    counts[1:, 1:] += 1

    return corners / counts


def triangle_area(vertices: list[tuple[float, float, float]], face: tuple[int, int, int]) -> float:
    ax, ay, az = vertices[face[0]]
    bx, by, bz = vertices[face[1]]
    cx, cy, cz = vertices[face[2]]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    cross_x = uy * vz - uz * vy
    cross_y = uz * vx - ux * vz
    cross_z = ux * vy - uy * vx
    return math.sqrt(cross_x**2 + cross_y**2 + cross_z**2) / 2.0


def add_face(
    faces: list[tuple[int, int, int]],
    vertices: list[tuple[float, float, float]],
    a: int,
    b: int,
    c: int,
) -> None:
    face = (a, b, c)
    if triangle_area(vertices, face) > 1e-9:
        faces.append(face)


def build_mesh(heightmap: HeightmapResult) -> MeshData:
    np, _, _, _ = load_runtime_dependencies()
    rows, cols = heightmap.total_heights_mm.shape
    corner_heights = corner_heights_from_cells(heightmap.total_heights_mm)
    x_coords = np.linspace(0.0, heightmap.width_mm, cols + 1)
    y_coords = np.linspace(0.0, heightmap.depth_mm, rows + 1)

    top_vertices: list[tuple[float, float, float]] = []
    for row_index, y_mm in enumerate(y_coords):
        for col_index, x_mm in enumerate(x_coords):
            top_vertices.append((float(x_mm), float(y_mm), float(corner_heights[row_index, col_index])))

    bottom_vertices = [(x_mm, y_mm, 0.0) for x_mm, y_mm, _ in top_vertices]
    vertices = top_vertices + bottom_vertices

    top_indices = np.arange((rows + 1) * (cols + 1), dtype=np.int32).reshape(rows + 1, cols + 1)
    bottom_indices = top_indices + len(top_vertices)
    faces: list[tuple[int, int, int]] = []

    for row_index in range(rows):
        for col_index in range(cols):
            t00 = int(top_indices[row_index, col_index])
            t10 = int(top_indices[row_index, col_index + 1])
            t01 = int(top_indices[row_index + 1, col_index])
            t11 = int(top_indices[row_index + 1, col_index + 1])
            b00 = int(bottom_indices[row_index, col_index])
            b10 = int(bottom_indices[row_index, col_index + 1])
            b01 = int(bottom_indices[row_index + 1, col_index])
            b11 = int(bottom_indices[row_index + 1, col_index + 1])

            add_face(faces, vertices, t00, t10, t11)
            add_face(faces, vertices, t00, t11, t01)
            add_face(faces, vertices, b00, b11, b10)
            add_face(faces, vertices, b00, b01, b11)

    for col_index in range(cols):
        t0 = int(top_indices[0, col_index])
        t1 = int(top_indices[0, col_index + 1])
        b0 = int(bottom_indices[0, col_index])
        b1 = int(bottom_indices[0, col_index + 1])
        add_face(faces, vertices, t0, b0, b1)
        add_face(faces, vertices, t0, b1, t1)

    for col_index in range(cols):
        t0 = int(top_indices[rows, col_index])
        t1 = int(top_indices[rows, col_index + 1])
        b0 = int(bottom_indices[rows, col_index])
        b1 = int(bottom_indices[rows, col_index + 1])
        add_face(faces, vertices, t0, b1, b0)
        add_face(faces, vertices, t0, t1, b1)

    for row_index in range(rows):
        t0 = int(top_indices[row_index, 0])
        t1 = int(top_indices[row_index + 1, 0])
        b0 = int(bottom_indices[row_index, 0])
        b1 = int(bottom_indices[row_index + 1, 0])
        add_face(faces, vertices, t0, b1, b0)
        add_face(faces, vertices, t0, t1, b1)

    for row_index in range(rows):
        t0 = int(top_indices[row_index, cols])
        t1 = int(top_indices[row_index + 1, cols])
        b0 = int(bottom_indices[row_index, cols])
        b1 = int(bottom_indices[row_index + 1, cols])
        add_face(faces, vertices, t0, b0, b1)
        add_face(faces, vertices, t0, b1, t1)

    return MeshData(vertices=vertices, faces=faces)


def write_obj(mesh: MeshData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# Generated by negative-to-relief tool\n")
        for x_mm, y_mm, z_mm in mesh.vertices:
            handle.write(f"v {x_mm:.6f} {y_mm:.6f} {z_mm:.6f}\n")
        for a, b, c in mesh.faces:
            handle.write(f"f {a + 1} {b + 1} {c + 1}\n")


def face_normal(
    vertices: list[tuple[float, float, float]],
    face: tuple[int, int, int],
) -> tuple[float, float, float]:
    ax, ay, az = vertices[face[0]]
    bx, by, bz = vertices[face[1]]
    cx, cy, cz = vertices[face[2]]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    normal_x = uy * vz - uz * vy
    normal_y = uz * vx - ux * vz
    normal_z = ux * vy - uy * vx
    length = math.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    if length == 0:
        return 0.0, 0.0, 0.0
    return normal_x / length, normal_y / length, normal_z / length


def write_ascii_stl(mesh: MeshData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    solid_name = "".join(ch if ch.isalnum() else "_" for ch in output_path.stem) or "relief"
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(f"solid {solid_name}\n")
        for face in mesh.faces:
            nx, ny, nz = face_normal(mesh.vertices, face)
            handle.write(f"  facet normal {nx:.6f} {ny:.6f} {nz:.6f}\n")
            handle.write("    outer loop\n")
            for vertex_index in face:
                x_mm, y_mm, z_mm = mesh.vertices[vertex_index]
                handle.write(f"      vertex {x_mm:.6f} {y_mm:.6f} {z_mm:.6f}\n")
            handle.write("    endloop\n")
            handle.write("  endfacet\n")
        handle.write(f"endsolid {solid_name}\n")


def extrusion_for_segment(
    segment_length_mm: float,
    line_width_mm: float,
    layer_height_mm: float,
    filament_diameter_mm: float,
    extrusion_multiplier: float,
) -> float:
    deposited_volume = segment_length_mm * line_width_mm * layer_height_mm * extrusion_multiplier
    filament_area = math.pi * (filament_diameter_mm / 2.0) ** 2
    return deposited_volume / filament_area


def contiguous_runs(mask_row: np.ndarray) -> list[tuple[int, int]]:
    np, _, _, _ = load_runtime_dependencies()
    padded = np.concatenate((np.array([False]), mask_row, np.array([False])))
    transitions = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1) - 1
    return list(zip(starts.tolist(), ends.tolist()))


def travel_move(
    gcode: list[str],
    x_mm: float,
    y_mm: float,
    layer_z_mm: float,
    settings: PrintSettings,
) -> None:
    if settings.z_hop_mm > 0:
        gcode.append(f"G0 Z{layer_z_mm + settings.z_hop_mm:.3f} F{settings.z_speed_mmpm:.0f}")
    gcode.append(f"G0 X{x_mm:.3f} Y{y_mm:.3f} F{settings.travel_speed_mmpm:.0f}")
    if settings.z_hop_mm > 0:
        gcode.append(f"G0 Z{layer_z_mm:.3f} F{settings.z_speed_mmpm:.0f}")


def generate_gcode(heightmap: HeightmapResult, settings: PrintSettings) -> tuple[str, GCodeStats]:
    np, _, _, _ = load_runtime_dependencies()
    layer_count = max(1, math.ceil(heightmap.total_height_mm / settings.layer_height_mm))
    gcode: list[str] = [
        "; Generated by negative-to-relief tool",
        "G21",
        "G90",
        "M83",
    ]

    if settings.bed_temperature_c is not None:
        gcode.append(f"M140 S{settings.bed_temperature_c}")
    if settings.nozzle_temperature_c is not None:
        gcode.append(f"M104 S{settings.nozzle_temperature_c}")

    gcode.extend(["G28", "G92 E0"])

    if settings.bed_temperature_c is not None:
        gcode.append(f"M190 S{settings.bed_temperature_c}")
    if settings.nozzle_temperature_c is not None:
        gcode.append(f"M109 S{settings.nozzle_temperature_c}")

    gcode.extend([f"M106 S{settings.fan_speed}", "G0 Z5.000 F600"])

    x_edges = settings.origin_x_mm + np.linspace(
        0.0, heightmap.width_mm, heightmap.total_heights_mm.shape[1] + 1
    )
    y_centers = settings.origin_y_mm + (
        np.arange(heightmap.total_heights_mm.shape[0]) + 0.5
    ) * heightmap.pitch_y_mm

    filament_mm = 0.0
    print_segments = 0
    travel_moves = 0

    for layer_index in range(layer_count):
        layer_number = layer_index + 1
        layer_z_mm = layer_number * settings.layer_height_mm
        layer_speed = (
            settings.first_layer_speed_mmpm if layer_number == 1 else settings.print_speed_mmpm
        )
        mask = heightmap.total_heights_mm >= (layer_z_mm - 1e-9)
        gcode.append(f"; Layer {layer_number}/{layer_count}")
        gcode.append(f"G0 Z{layer_z_mm:.3f} F{settings.z_speed_mmpm:.0f}")

        for row_index, row in enumerate(mask):
            runs = contiguous_runs(row)
            if not runs:
                continue

            row_reverse = row_index % 2 == 1
            if row_reverse:
                runs = list(reversed(runs))

            y_mm = float(y_centers[row_index])

            for start_idx, end_idx in runs:
                x_start_mm = float(x_edges[start_idx])
                x_end_mm = float(x_edges[end_idx + 1])
                if row_reverse:
                    move_x_mm, draw_x_mm = x_end_mm, x_start_mm
                else:
                    move_x_mm, draw_x_mm = x_start_mm, x_end_mm

                travel_move(gcode, move_x_mm, y_mm, layer_z_mm, settings)
                travel_moves += 1

                segment_length_mm = abs(draw_x_mm - move_x_mm)
                extrusion_mm = extrusion_for_segment(
                    segment_length_mm=segment_length_mm,
                    line_width_mm=settings.line_width_mm,
                    layer_height_mm=settings.layer_height_mm,
                    filament_diameter_mm=settings.filament_diameter_mm,
                    extrusion_multiplier=settings.extrusion_multiplier,
                )
                gcode.append(
                    f"G1 X{draw_x_mm:.3f} Y{y_mm:.3f} E{extrusion_mm:.5f} F{layer_speed:.0f}"
                )
                filament_mm += extrusion_mm
                print_segments += 1

    end_z_mm = layer_count * settings.layer_height_mm + max(settings.z_hop_mm, 5.0)
    gcode.extend(
        [
            f"G0 Z{end_z_mm:.3f} F{settings.z_speed_mmpm:.0f}",
            f"G0 X{settings.origin_x_mm:.3f} Y{settings.origin_y_mm:.3f} F{settings.travel_speed_mmpm:.0f}",
            "M107",
            "M104 S0",
            "M140 S0",
            "M84",
        ]
    )

    stats = GCodeStats(
        layer_count=layer_count,
        print_segments=print_segments,
        travel_moves=travel_moves,
        filament_mm=filament_mm,
    )
    return "\n".join(gcode) + "\n", stats


def write_text_file(output_path: Path, contents: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(contents, encoding="utf-8")


def generate_outputs(
    heightmap_settings: HeightmapSettings,
    print_settings: PrintSettings,
    heightmap_out: Path,
    gcode_out: Path | None,
    obj_out: Path | None,
    stl_out: Path | None,
) -> GenerationSummary:
    preflight_python_imports()
    heightmap = build_heightmap(heightmap_settings, line_width_mm=print_settings.line_width_mm)
    if heightmap.total_height_mm <= 0:
        raise ValueError("Heightmap is empty. Increase relief height or provide a non-empty image.")

    save_heightmap_preview(heightmap.relief_map, heightmap_out)

    gcode_stats: GCodeStats | None = None
    if gcode_out is not None:
        gcode, gcode_stats = generate_gcode(heightmap, print_settings)
        write_text_file(gcode_out, gcode)

    mesh: MeshData | None = None
    if obj_out is not None or stl_out is not None:
        mesh = build_mesh(heightmap)
        if obj_out is not None:
            write_obj(mesh, obj_out)
        if stl_out is not None:
            write_ascii_stl(mesh, stl_out)

    return GenerationSummary(
        heightmap=heightmap,
        heightmap_path=heightmap_out,
        gcode_path=gcode_out,
        obj_path=obj_out,
        stl_path=stl_out,
        gcode_stats=gcode_stats,
        mesh_vertices=len(mesh.vertices) if mesh is not None else None,
        mesh_faces=len(mesh.faces) if mesh is not None else None,
    )


def build_settings_from_args(
    args: argparse.Namespace,
    input_path: Path,
) -> tuple[HeightmapSettings, PrintSettings]:
    heightmap_settings = HeightmapSettings(
        input_path=input_path,
        width_mm=args.width_mm,
        depth_mm=args.depth_mm,
        relief_height_mm=args.relief_height_mm,
        base_thickness_mm=args.base_thickness_mm,
        invert=not args.no_invert,
        autocontrast=args.autocontrast,
        gamma=args.gamma,
        blur_radius=args.blur_radius,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
    )
    print_settings = PrintSettings(
        line_width_mm=args.line_width_mm,
        layer_height_mm=args.layer_height_mm,
        filament_diameter_mm=args.filament_diameter_mm,
        print_speed_mmpm=args.print_speed,
        first_layer_speed_mmpm=args.first_layer_speed,
        travel_speed_mmpm=args.travel_speed,
        z_speed_mmpm=args.z_speed,
        z_hop_mm=args.z_hop_mm,
        extrusion_multiplier=args.extrusion_multiplier,
        origin_x_mm=args.origin_x_mm,
        origin_y_mm=args.origin_y_mm,
        nozzle_temperature_c=normalize_temperature(args.nozzle_temperature),
        bed_temperature_c=normalize_temperature(args.bed_temperature),
        fan_speed=args.fan_speed,
    )
    return heightmap_settings, print_settings


def print_summary(summary: GenerationSummary) -> None:
    print(f"Heightmap preview: {summary.heightmap_path}")
    print(
        "Print size: "
        f"{summary.heightmap.width_mm:.2f} x {summary.heightmap.depth_mm:.2f} x "
        f"{summary.heightmap.total_height_mm:.2f} mm"
    )
    print(
        "Grid: "
        f"{summary.heightmap.total_heights_mm.shape[1]} x {summary.heightmap.total_heights_mm.shape[0]} "
        f"(pitch {summary.heightmap.pitch_x_mm:.3f} x {summary.heightmap.pitch_y_mm:.3f} mm)"
    )

    if summary.gcode_path is not None and summary.gcode_stats is not None:
        print(f"G-code: {summary.gcode_path}")
        print(
            f"Layers: {summary.gcode_stats.layer_count}, "
            f"print segments: {summary.gcode_stats.print_segments}, "
            f"travel moves: {summary.gcode_stats.travel_moves}"
        )
        print(f"Estimated filament: {summary.gcode_stats.filament_mm / 1000:.3f} m")

    if summary.obj_path is not None:
        print(f"OBJ mesh: {summary.obj_path}")
    if summary.stl_path is not None:
        print(f"STL mesh: {summary.stl_path}")
    if summary.mesh_vertices is not None and summary.mesh_faces is not None:
        print(f"Mesh: {summary.mesh_vertices} vertices, {summary.mesh_faces} triangles")


def launch_gui(initial_input: Path | None = None) -> None:
    preflight_gui()
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:
        raise SystemExit("Tkinter is unavailable in this Python build. Use the CLI mode instead.") from exc

    class ReliefApp:
        def __init__(self, root: tk.Tk, preset_input: Path | None) -> None:
            self.root = root
            self.root.title("Negative To Relief")
            self.root.geometry("920x760")
            self.root.minsize(820, 640)

            self.input_path_var = tk.StringVar(value=str(preset_input) if preset_input else "")
            default_output_dir = str(preset_input.parent) if preset_input else str(Path.cwd())
            self.output_dir_var = tk.StringVar(value=default_output_dir)
            self.export_gcode_var = tk.BooleanVar(value=True)
            self.export_obj_var = tk.BooleanVar(value=True)
            self.export_stl_var = tk.BooleanVar(value=True)
            self.width_mm_var = tk.StringVar(value=str(DEFAULT_WIDTH_MM))
            self.depth_mm_var = tk.StringVar(value="")
            self.relief_height_var = tk.StringVar(value=str(DEFAULT_RELIEF_HEIGHT_MM))
            self.base_thickness_var = tk.StringVar(value=str(DEFAULT_BASE_THICKNESS_MM))
            self.line_width_var = tk.StringVar(value=str(DEFAULT_LINE_WIDTH_MM))
            self.layer_height_var = tk.StringVar(value=str(DEFAULT_LAYER_HEIGHT_MM))
            self.gamma_var = tk.StringVar(value=str(DEFAULT_GAMMA))
            self.blur_radius_var = tk.StringVar(value=str(DEFAULT_BLUR_RADIUS))
            self.resolution_x_var = tk.StringVar(value="")
            self.resolution_y_var = tk.StringVar(value="")
            self.origin_x_var = tk.StringVar(value=str(DEFAULT_ORIGIN_X_MM))
            self.origin_y_var = tk.StringVar(value=str(DEFAULT_ORIGIN_Y_MM))
            self.print_speed_var = tk.StringVar(value=str(DEFAULT_PRINT_SPEED_MMPM))
            self.first_layer_speed_var = tk.StringVar(value=str(DEFAULT_FIRST_LAYER_SPEED_MMPM))
            self.travel_speed_var = tk.StringVar(value=str(DEFAULT_TRAVEL_SPEED_MMPM))
            self.z_speed_var = tk.StringVar(value=str(DEFAULT_Z_SPEED_MMPM))
            self.z_hop_var = tk.StringVar(value=str(DEFAULT_Z_HOP_MM))
            self.extrusion_multiplier_var = tk.StringVar(value=str(DEFAULT_EXTRUSION_MULTIPLIER))
            self.filament_diameter_var = tk.StringVar(value=str(DEFAULT_FILAMENT_DIAMETER_MM))
            self.nozzle_temperature_var = tk.StringVar(value=str(DEFAULT_NOZZLE_TEMPERATURE_C))
            self.bed_temperature_var = tk.StringVar(value=str(DEFAULT_BED_TEMPERATURE_C))
            self.fan_speed_var = tk.StringVar(value=str(DEFAULT_FAN_SPEED))
            self.autocontrast_var = tk.BooleanVar(value=False)
            self.invert_var = tk.BooleanVar(value=True)

            self.status_text = tk.Text(root, height=14, wrap="word", state="disabled")
            self.preview_label: ttk.Label | None = None
            self.preview_image = None

            self.build_layout(ttk, filedialog, messagebox)

        def build_layout(self, ttk_module, filedialog_module, messagebox_module) -> None:
            container = ttk_module.Frame(self.root, padding=14)
            container.pack(fill="both", expand=True)
            container.columnconfigure(0, weight=1)
            container.rowconfigure(0, weight=1)
            container.rowconfigure(1, weight=0)

            canvas = tk.Canvas(container, highlightthickness=0)
            scrollbar = ttk_module.Scrollbar(container, orient="vertical", command=canvas.yview)
            content = ttk_module.Frame(canvas, padding=(0, 0, 6, 0))
            content.bind(
                "<Configure>",
                lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=content, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
            content.columnconfigure(0, weight=1)
            content.columnconfigure(1, weight=1)

            files_frame = ttk_module.LabelFrame(content, text="Files", padding=12)
            files_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            files_frame.columnconfigure(1, weight=1)

            ttk_module.Label(files_frame, text="Input image").grid(row=0, column=0, sticky="w", padx=(0, 8))
            ttk_module.Entry(files_frame, textvariable=self.input_path_var).grid(
                row=0, column=1, sticky="ew"
            )
            ttk_module.Button(
                files_frame,
                text="Browse",
                command=lambda: self.pick_input_file(filedialog_module),
            ).grid(row=0, column=2, padx=(8, 0))

            ttk_module.Label(files_frame, text="Output folder").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0)
            )
            ttk_module.Entry(files_frame, textvariable=self.output_dir_var).grid(
                row=1, column=1, sticky="ew", pady=(8, 0)
            )
            ttk_module.Button(
                files_frame,
                text="Browse",
                command=lambda: self.pick_output_dir(filedialog_module),
            ).grid(row=1, column=2, padx=(8, 0), pady=(8, 0))

            outputs_frame = ttk_module.LabelFrame(content, text="Exports", padding=12)
            outputs_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            ttk_module.Checkbutton(outputs_frame, text="G-code", variable=self.export_gcode_var).grid(
                row=0, column=0, sticky="w"
            )
            ttk_module.Checkbutton(outputs_frame, text="OBJ mesh", variable=self.export_obj_var).grid(
                row=1, column=0, sticky="w"
            )
            ttk_module.Checkbutton(outputs_frame, text="STL mesh", variable=self.export_stl_var).grid(
                row=2, column=0, sticky="w"
            )

            tone_frame = ttk_module.LabelFrame(content, text="Image Processing", padding=12)
            tone_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            ttk_module.Checkbutton(
                tone_frame, text="Invert source image", variable=self.invert_var
            ).grid(row=0, column=0, sticky="w")
            ttk_module.Checkbutton(
                tone_frame, text="Auto contrast", variable=self.autocontrast_var
            ).grid(row=1, column=0, sticky="w")
            self.add_labeled_entry(ttk_module, tone_frame, "Gamma", self.gamma_var, 2)
            self.add_labeled_entry(ttk_module, tone_frame, "Blur radius", self.blur_radius_var, 3)

            geometry_frame = ttk_module.LabelFrame(content, text="Geometry", padding=12)
            geometry_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            geometry_frame.columnconfigure(1, weight=1)
            self.add_labeled_entry(ttk_module, geometry_frame, "Width (mm)", self.width_mm_var, 0)
            self.add_labeled_entry(ttk_module, geometry_frame, "Depth (mm)", self.depth_mm_var, 1)
            self.add_labeled_entry(
                ttk_module, geometry_frame, "Relief height (mm)", self.relief_height_var, 2
            )
            self.add_labeled_entry(
                ttk_module, geometry_frame, "Base thickness (mm)", self.base_thickness_var, 3
            )
            self.add_labeled_entry(ttk_module, geometry_frame, "Resolution X", self.resolution_x_var, 4)
            self.add_labeled_entry(ttk_module, geometry_frame, "Resolution Y", self.resolution_y_var, 5)

            print_frame = ttk_module.LabelFrame(content, text="Print", padding=12)
            print_frame.grid(row=2, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            print_frame.columnconfigure(1, weight=1)
            self.add_labeled_entry(ttk_module, print_frame, "Line width (mm)", self.line_width_var, 0)
            self.add_labeled_entry(ttk_module, print_frame, "Layer height (mm)", self.layer_height_var, 1)
            self.add_labeled_entry(
                ttk_module, print_frame, "Filament dia. (mm)", self.filament_diameter_var, 2
            )
            self.add_labeled_entry(ttk_module, print_frame, "Origin X (mm)", self.origin_x_var, 3)
            self.add_labeled_entry(ttk_module, print_frame, "Origin Y (mm)", self.origin_y_var, 4)
            self.add_labeled_entry(
                ttk_module, print_frame, "Extrusion multiplier", self.extrusion_multiplier_var, 5
            )

            speeds_frame = ttk_module.LabelFrame(content, text="Speed And Temperatures", padding=12)
            speeds_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            for col_index in (1, 3, 5):
                speeds_frame.columnconfigure(col_index, weight=1)
            self.add_grid_entry(ttk_module, speeds_frame, "Print", self.print_speed_var, 0, 0)
            self.add_grid_entry(
                ttk_module, speeds_frame, "First layer", self.first_layer_speed_var, 0, 2
            )
            self.add_grid_entry(ttk_module, speeds_frame, "Travel", self.travel_speed_var, 0, 4)
            self.add_grid_entry(ttk_module, speeds_frame, "Z speed", self.z_speed_var, 1, 0)
            self.add_grid_entry(ttk_module, speeds_frame, "Z hop", self.z_hop_var, 1, 2)
            self.add_grid_entry(
                ttk_module, speeds_frame, "Nozzle C", self.nozzle_temperature_var, 1, 4
            )
            self.add_grid_entry(ttk_module, speeds_frame, "Bed C", self.bed_temperature_var, 2, 0)
            self.add_grid_entry(ttk_module, speeds_frame, "Fan 0-255", self.fan_speed_var, 2, 2)

            preview_frame = ttk_module.LabelFrame(content, text="Heightmap Preview", padding=12)
            preview_frame.grid(row=4, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            self.preview_label = ttk_module.Label(preview_frame, text="Preview appears after generation.")
            self.preview_label.pack(fill="both", expand=True)

            log_frame = ttk_module.LabelFrame(content, text="Log", padding=12)
            log_frame.grid(row=4, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            self.status_text.pack(in_=log_frame, fill="both", expand=True)

            actions = ttk_module.Frame(container)
            actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            actions.columnconfigure(0, weight=1)
            ttk_module.Button(
                actions,
                text="Generate",
                command=lambda: self.generate(messagebox_module),
            ).grid(row=0, column=0, sticky="e")

        def add_labeled_entry(self, ttk_module, parent, label: str, variable: tk.StringVar, row: int) -> None:
            ttk_module.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
            ttk_module.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

        def add_grid_entry(
            self,
            ttk_module,
            parent,
            label: str,
            variable: tk.StringVar,
            row: int,
            column: int,
        ) -> None:
            ttk_module.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
            ttk_module.Entry(parent, textvariable=variable, width=12).grid(
                row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=4
            )

        def append_status(self, message: str) -> None:
            self.status_text.configure(state="normal")
            self.status_text.insert("end", message + "\n")
            self.status_text.see("end")
            self.status_text.configure(state="disabled")

        def clear_status(self) -> None:
            self.status_text.configure(state="normal")
            self.status_text.delete("1.0", "end")
            self.status_text.configure(state="disabled")

        def pick_input_file(self, filedialog_module) -> None:
            path = filedialog_module.askopenfilename(
                title="Choose an input image",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
                    ("All files", "*.*"),
                ],
            )
            if path:
                self.input_path_var.set(path)
                self.output_dir_var.set(str(Path(path).resolve().parent))

        def pick_output_dir(self, filedialog_module) -> None:
            path = filedialog_module.askdirectory(title="Choose output folder")
            if path:
                self.output_dir_var.set(path)

        def build_settings(self) -> tuple[HeightmapSettings, PrintSettings, Path, Path | None, Path | None, Path | None]:
            input_path = Path(self.input_path_var.get()).expanduser().resolve()
            if not input_path.exists():
                raise ValueError(f"Input image does not exist: {input_path}")

            output_dir = Path(self.output_dir_var.get()).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

            stem = input_path.stem
            heightmap_out = output_dir / f"{stem}_heightmap.png"
            gcode_out = output_dir / f"{stem}.gcode" if self.export_gcode_var.get() else None
            obj_out = output_dir / f"{stem}.obj" if self.export_obj_var.get() else None
            stl_out = output_dir / f"{stem}.stl" if self.export_stl_var.get() else None

            heightmap_settings = HeightmapSettings(
                input_path=input_path,
                width_mm=required_positive_float(self.width_mm_var.get(), "Width"),
                depth_mm=optional_positive_float(self.depth_mm_var.get()),
                relief_height_mm=required_positive_float(
                    self.relief_height_var.get(), "Relief height"
                ),
                base_thickness_mm=required_non_negative_float(
                    self.base_thickness_var.get(), "Base thickness"
                ),
                invert=self.invert_var.get(),
                autocontrast=self.autocontrast_var.get(),
                gamma=required_positive_float(self.gamma_var.get(), "Gamma"),
                blur_radius=required_non_negative_float(self.blur_radius_var.get(), "Blur radius"),
                resolution_x=optional_positive_int(self.resolution_x_var.get()),
                resolution_y=optional_positive_int(self.resolution_y_var.get()),
            )

            fan_speed = int(self.fan_speed_var.get())
            if not 0 <= fan_speed <= 255:
                raise ValueError("Fan speed must be between 0 and 255.")

            print_settings = PrintSettings(
                line_width_mm=required_positive_float(self.line_width_var.get(), "Line width"),
                layer_height_mm=required_positive_float(self.layer_height_var.get(), "Layer height"),
                filament_diameter_mm=required_positive_float(
                    self.filament_diameter_var.get(), "Filament diameter"
                ),
                print_speed_mmpm=required_positive_float(self.print_speed_var.get(), "Print speed"),
                first_layer_speed_mmpm=required_positive_float(
                    self.first_layer_speed_var.get(), "First layer speed"
                ),
                travel_speed_mmpm=required_positive_float(
                    self.travel_speed_var.get(), "Travel speed"
                ),
                z_speed_mmpm=required_positive_float(self.z_speed_var.get(), "Z speed"),
                z_hop_mm=required_non_negative_float(self.z_hop_var.get(), "Z hop"),
                extrusion_multiplier=required_positive_float(
                    self.extrusion_multiplier_var.get(), "Extrusion multiplier"
                ),
                origin_x_mm=required_non_negative_float(self.origin_x_var.get(), "Origin X"),
                origin_y_mm=required_non_negative_float(self.origin_y_var.get(), "Origin Y"),
                nozzle_temperature_c=normalize_temperature(int(self.nozzle_temperature_var.get())),
                bed_temperature_c=normalize_temperature(int(self.bed_temperature_var.get())),
                fan_speed=fan_speed,
            )

            return heightmap_settings, print_settings, heightmap_out, gcode_out, obj_out, stl_out

        def update_preview(self, heightmap_path: Path) -> None:
            if self.preview_label is None:
                return
            _, Image, _, _ = load_runtime_dependencies()
            preview_image = Image.open(heightmap_path)
            preview_image.thumbnail((360, 360), Image.Resampling.NEAREST)
            try:
                from PIL import ImageTk
            except ImportError:
                preview_image.close()
                self.preview_label.configure(text=f"Preview saved to:\n{heightmap_path}")
                return
            self.preview_image = ImageTk.PhotoImage(preview_image)
            self.preview_label.configure(image=self.preview_image, text="")
            preview_image.close()

        def generate(self, messagebox_module) -> None:
            self.clear_status()
            try:
                settings = self.build_settings()
                summary = generate_outputs(*settings)
            except Exception as exc:
                self.append_status(str(exc))
                messagebox_module.showerror("Generation failed", str(exc))
                return

            self.update_preview(summary.heightmap_path)
            self.append_status(f"Heightmap preview: {summary.heightmap_path}")
            self.append_status(
                "Print size: "
                f"{summary.heightmap.width_mm:.2f} x {summary.heightmap.depth_mm:.2f} x "
                f"{summary.heightmap.total_height_mm:.2f} mm"
            )
            if summary.gcode_path is not None and summary.gcode_stats is not None:
                self.append_status(f"G-code: {summary.gcode_path}")
                self.append_status(
                    f"Layers: {summary.gcode_stats.layer_count}, "
                    f"segments: {summary.gcode_stats.print_segments}, "
                    f"filament: {summary.gcode_stats.filament_mm / 1000:.3f} m"
                )
            if summary.obj_path is not None:
                self.append_status(f"OBJ mesh: {summary.obj_path}")
            if summary.stl_path is not None:
                self.append_status(f"STL mesh: {summary.stl_path}")
            if summary.mesh_vertices is not None and summary.mesh_faces is not None:
                self.append_status(
                    f"Mesh: {summary.mesh_vertices} vertices, {summary.mesh_faces} triangles"
                )

            message_lines = [f"Heightmap saved to {summary.heightmap_path}"]
            if summary.gcode_path is not None:
                message_lines.append(f"G-code saved to {summary.gcode_path}")
            if summary.obj_path is not None:
                message_lines.append(f"OBJ saved to {summary.obj_path}")
            if summary.stl_path is not None:
                message_lines.append(f"STL saved to {summary.stl_path}")
            messagebox_module.showinfo("Generation completed", "\n".join(message_lines))

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise SystemExit(
            "GUI could not start. Check that a graphical display is available, or use CLI mode."
        ) from exc
    ReliefApp(root, initial_input)
    root.mainloop()


def run_cli(args: argparse.Namespace) -> None:
    if args.input_image is None:
        raise SystemExit("Input image is required in CLI mode. Use --gui to start the interface.")

    input_path = args.input_image.expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input image does not exist: {input_path}")

    heightmap_settings, print_settings = build_settings_from_args(args, input_path)
    heightmap_out = (
        args.heightmap_out.expanduser().resolve()
        if args.heightmap_out
        else default_heightmap_output(input_path)
    )
    gcode_out = None
    if not args.no_gcode:
        gcode_out = args.gcode_out.expanduser().resolve() if args.gcode_out else default_gcode_output(input_path)
    obj_out = args.obj_out.expanduser().resolve() if args.obj_out else None
    stl_out = args.stl_out.expanduser().resolve() if args.stl_out else None

    summary = generate_outputs(
        heightmap_settings=heightmap_settings,
        print_settings=print_settings,
        heightmap_out=heightmap_out,
        gcode_out=gcode_out,
        obj_out=obj_out,
        stl_out=stl_out,
    )
    print_summary(summary)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.gui or args.input_image is None:
        initial_input = args.input_image.expanduser().resolve() if args.input_image else None
        launch_gui(initial_input)
        return

    run_cli(args)


if __name__ == "__main__":
    main()
