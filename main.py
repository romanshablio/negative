from __future__ import annotations

import argparse
import locale
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
GUI_LANGUAGE_NAMES = {"en": "English", "ru": "Русский"}
GUI_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "Negative To Relief",
        "help_default_title": "Parameter Help",
        "help_default_text": "Hover over a parameter or click into a field to see a short explanation here.",
        "frame_files": "Files",
        "frame_exports": "Exports",
        "frame_processing": "Image Processing",
        "frame_geometry": "Geometry",
        "frame_print": "Print",
        "frame_speed": "Speed And Temperatures",
        "frame_description": "Description",
        "frame_preview": "Heightmap Preview",
        "frame_log": "Log",
        "label_input_image": "Input image",
        "label_output_folder": "Output folder",
        "label_language": "Language",
        "button_browse": "Browse",
        "button_generate": "Generate",
        "toggle_gcode": "G-code",
        "toggle_obj": "OBJ mesh",
        "toggle_stl": "STL mesh",
        "toggle_invert": "Invert source image",
        "toggle_autocontrast": "Auto contrast",
        "field_gamma": "Gamma",
        "field_blur_radius": "Blur radius",
        "field_width_mm": "Width (mm)",
        "field_depth_mm": "Depth (mm)",
        "field_relief_height": "Relief height (mm)",
        "field_base_thickness": "Base thickness (mm)",
        "field_resolution_x": "Resolution X",
        "field_resolution_y": "Resolution Y",
        "field_line_width": "Line width (mm)",
        "field_layer_height": "Layer height (mm)",
        "field_filament_diameter": "Filament dia. (mm)",
        "field_origin_x": "Origin X (mm)",
        "field_origin_y": "Origin Y (mm)",
        "field_extrusion_multiplier": "Extrusion multiplier",
        "field_print_speed": "Print",
        "field_first_layer_speed": "First layer",
        "field_travel_speed": "Travel",
        "field_z_speed": "Z speed",
        "field_z_hop": "Z hop",
        "field_nozzle_temperature": "Nozzle C",
        "field_bed_temperature": "Bed C",
        "field_fan_speed": "Fan 0-255",
        "preview_placeholder": "Preview appears after generation.",
        "preview_saved_to": "Preview saved to:",
        "dialog_input_title": "Choose an input image",
        "dialog_output_title": "Choose output folder",
        "filetype_images": "Images",
        "filetype_all": "All files",
        "error_generation_failed": "Generation failed",
        "info_generation_completed": "Generation completed",
        "status_heightmap_preview": "Heightmap preview: {path}",
        "status_print_size": "Print size: {width:.2f} x {depth:.2f} x {height:.2f} mm",
        "status_gcode": "G-code: {path}",
        "status_layers": "Layers: {layers}, segments: {segments}, filament: {filament:.3f} m",
        "status_obj": "OBJ mesh: {path}",
        "status_stl": "STL mesh: {path}",
        "status_mesh": "Mesh: {vertices} vertices, {triangles} triangles",
        "msg_heightmap_saved": "Heightmap saved to {path}",
        "msg_gcode_saved": "G-code saved to {path}",
        "msg_obj_saved": "OBJ saved to {path}",
        "msg_stl_saved": "STL saved to {path}",
        "label_width": "Width",
        "label_relief_height_short": "Relief height",
        "label_base_thickness_short": "Base thickness",
        "label_gamma_short": "Gamma",
        "label_blur_radius_short": "Blur radius",
        "label_line_width": "Line width",
        "label_layer_height_short": "Layer height",
        "label_filament_diameter_short": "Filament diameter",
        "label_print_speed_short": "Print speed",
        "label_first_layer_speed_short": "First layer speed",
        "label_travel_speed_short": "Travel speed",
        "label_z_speed_short": "Z speed",
        "label_z_hop_short": "Z hop",
        "label_extrusion_multiplier_short": "Extrusion multiplier",
        "label_origin_x_short": "Origin X",
        "label_origin_y_short": "Origin Y",
        "error_input_missing": "Input image does not exist: {path}",
        "error_fan_speed": "Fan speed must be between 0 and 255.",
    },
    "ru": {
        "app_title": "Negative To Relief",
        "help_default_title": "Описание параметра",
        "help_default_text": "Наведите курсор на параметр или перейдите в поле, чтобы увидеть краткое описание.",
        "frame_files": "Файлы",
        "frame_exports": "Экспорт",
        "frame_processing": "Обработка изображения",
        "frame_geometry": "Геометрия",
        "frame_print": "Печать",
        "frame_speed": "Скорости и температуры",
        "frame_description": "Описание",
        "frame_preview": "Превью карты высот",
        "frame_log": "Журнал",
        "label_input_image": "Исходное изображение",
        "label_output_folder": "Папка вывода",
        "label_language": "Язык",
        "button_browse": "Выбрать",
        "button_generate": "Сгенерировать",
        "toggle_gcode": "G-code",
        "toggle_obj": "OBJ mesh",
        "toggle_stl": "STL mesh",
        "toggle_invert": "Инвертировать изображение",
        "toggle_autocontrast": "Автоконтраст",
        "field_gamma": "Гамма",
        "field_blur_radius": "Размытие",
        "field_width_mm": "Ширина (мм)",
        "field_depth_mm": "Глубина (мм)",
        "field_relief_height": "Высота рельефа (мм)",
        "field_base_thickness": "Толщина базы (мм)",
        "field_resolution_x": "Разрешение X",
        "field_resolution_y": "Разрешение Y",
        "field_line_width": "Ширина линии (мм)",
        "field_layer_height": "Высота слоя (мм)",
        "field_filament_diameter": "Диаметр филамента (мм)",
        "field_origin_x": "Смещение X (мм)",
        "field_origin_y": "Смещение Y (мм)",
        "field_extrusion_multiplier": "Множитель экструзии",
        "field_print_speed": "Печать",
        "field_first_layer_speed": "Первый слой",
        "field_travel_speed": "Перемещения",
        "field_z_speed": "Скорость Z",
        "field_z_hop": "Подъем Z",
        "field_nozzle_temperature": "Сопло C",
        "field_bed_temperature": "Стол C",
        "field_fan_speed": "Обдув 0-255",
        "preview_placeholder": "Превью появится после генерации.",
        "preview_saved_to": "Превью сохранено в:",
        "dialog_input_title": "Выберите входное изображение",
        "dialog_output_title": "Выберите папку вывода",
        "filetype_images": "Изображения",
        "filetype_all": "Все файлы",
        "error_generation_failed": "Ошибка генерации",
        "info_generation_completed": "Генерация завершена",
        "status_heightmap_preview": "Превью карты высот: {path}",
        "status_print_size": "Размер модели: {width:.2f} x {depth:.2f} x {height:.2f} мм",
        "status_gcode": "G-code: {path}",
        "status_layers": "Слоев: {layers}, сегментов: {segments}, филамента: {filament:.3f} м",
        "status_obj": "OBJ mesh: {path}",
        "status_stl": "STL mesh: {path}",
        "status_mesh": "Сетка: {vertices} вершин, {triangles} треугольников",
        "msg_heightmap_saved": "Карта высот сохранена в {path}",
        "msg_gcode_saved": "G-code сохранен в {path}",
        "msg_obj_saved": "OBJ сохранен в {path}",
        "msg_stl_saved": "STL сохранен в {path}",
        "label_width": "Ширина",
        "label_relief_height_short": "Высота рельефа",
        "label_base_thickness_short": "Толщина базы",
        "label_gamma_short": "Гамма",
        "label_blur_radius_short": "Размытие",
        "label_line_width": "Ширина линии",
        "label_layer_height_short": "Высота слоя",
        "label_filament_diameter_short": "Диаметр филамента",
        "label_print_speed_short": "Скорость печати",
        "label_first_layer_speed_short": "Скорость первого слоя",
        "label_travel_speed_short": "Скорость перемещений",
        "label_z_speed_short": "Скорость Z",
        "label_z_hop_short": "Подъем Z",
        "label_extrusion_multiplier_short": "Множитель экструзии",
        "label_origin_x_short": "Смещение X",
        "label_origin_y_short": "Смещение Y",
        "error_input_missing": "Исходное изображение не найдено: {path}",
        "error_fan_speed": "Значение обдува должно быть в диапазоне от 0 до 255.",
    },
}
GUI_FIELD_HELP: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "input_image": (
            "Input image",
            "Source image that will be converted into a heightmap. By default the app expects a negative.",
        ),
        "output_folder": (
            "Output folder",
            "Directory where the app will save the preview PNG, G-code and optional OBJ or STL files.",
        ),
        "language": (
            "Language",
            "Switches the language of the GUI labels, hints and dialog messages.",
        ),
        "export_gcode": (
            "G-code export",
            "Creates layered G-code for an FDM printer based on the generated heightmap.",
        ),
        "export_obj": (
            "OBJ export",
            "Creates an OBJ mesh of the relief. Useful for 3D editors and mesh-based workflows.",
        ),
        "export_stl": (
            "STL export",
            "Creates an STL mesh of the relief. Useful for slicers and CAD or printing workflows.",
        ),
        "invert": (
            "Invert source image",
            "Turns a negative into a positive heightmap. Bright areas become taller after inversion.",
        ),
        "autocontrast": (
            "Auto contrast",
            "Stretches the tonal range of the image so the heightmap uses more of the available relief range.",
        ),
        "gamma": (
            "Gamma",
            "Adjusts how strongly midtones affect height. Lower values lift midtones, higher values compress them.",
        ),
        "blur_radius": (
            "Blur radius",
            "Applies Gaussian smoothing before building the heightmap. Useful for reducing noise and harsh steps.",
        ),
        "width_mm": ("Width (mm)", "Final physical size of the model along the X axis, in millimeters."),
        "depth_mm": (
            "Depth (mm)",
            "Final physical size of the model along the Y axis, in millimeters. Leave empty to keep image proportions.",
        ),
        "relief_height": (
            "Relief height (mm)",
            "Maximum extra height of the relief above the base. Larger values produce stronger depth.",
        ),
        "base_thickness": (
            "Base thickness (mm)",
            "Thickness of the solid backing under the relief. This helps the print stay rigid and printable.",
        ),
        "resolution_x": (
            "Resolution X",
            "Number of sampling columns used to build the heightmap. Higher values add detail but also create heavier files.",
        ),
        "resolution_y": (
            "Resolution Y",
            "Number of sampling rows used to build the heightmap. Higher values increase detail and processing cost.",
        ),
        "line_width": (
            "Line width (mm)",
            "Extrusion width used for G-code generation. It should roughly match your slicer or nozzle setup.",
        ),
        "layer_height": (
            "Layer height (mm)",
            "Vertical step between printed layers. Smaller values improve detail but increase print time.",
        ),
        "filament_diameter": (
            "Filament dia. (mm)",
            "Diameter of the filament used for extrusion calculations. For most hobby printers this is 1.75 mm.",
        ),
        "origin_x": ("Origin X (mm)", "X position on the print bed where the generated G-code will place the model."),
        "origin_y": ("Origin Y (mm)", "Y position on the print bed where the generated G-code will place the model."),
        "extrusion_multiplier": (
            "Extrusion multiplier",
            "Scales the amount of material extruded. Increase slightly for under-extrusion, decrease for over-extrusion.",
        ),
        "print_speed": ("Print speed", "Main printing speed in millimeters per minute for regular layers."),
        "first_layer_speed": (
            "First layer",
            "Printing speed of the first layer. Slower values usually improve bed adhesion.",
        ),
        "travel_speed": (
            "Travel speed",
            "Speed of non-printing moves. Higher values reduce travel time but can stress the machine.",
        ),
        "z_speed": ("Z speed", "Vertical movement speed on the Z axis, in millimeters per minute."),
        "z_hop": (
            "Z hop",
            "Temporary lift before travel moves to reduce collisions with already printed areas.",
        ),
        "nozzle_temperature": (
            "Nozzle C",
            "Nozzle temperature in Celsius used in the generated G-code. Set to 0 to skip heating commands.",
        ),
        "bed_temperature": (
            "Bed C",
            "Bed temperature in Celsius used in the generated G-code. Set to 0 to skip heating commands.",
        ),
        "fan_speed": ("Fan 0-255", "Cooling fan PWM value used in G-code. 0 is off, 255 is maximum speed."),
    },
    "ru": {
        "input_image": (
            "Исходное изображение",
            "Файл изображения, из которого строится карта высот. По умолчанию приложение считает, что это негатив.",
        ),
        "output_folder": (
            "Папка вывода",
            "Сюда будут сохранены превью PNG, G-code и при необходимости файлы OBJ или STL.",
        ),
        "language": (
            "Язык",
            "Переключает язык подписей интерфейса, подсказок и сообщений диалоговых окон.",
        ),
        "export_gcode": (
            "Экспорт G-code",
            "Создает послойный G-code для FDM-принтера по построенной карте высот.",
        ),
        "export_obj": (
            "Экспорт OBJ",
            "Создает OBJ-модель рельефа. Полезно для 3D-редакторов и работы с мешами.",
        ),
        "export_stl": (
            "Экспорт STL",
            "Создает STL-модель рельефа. Удобно для слайсеров и подготовки к печати.",
        ),
        "invert": (
            "Инвертировать изображение",
            "Преобразует негатив в позитивную карту высот. Светлые области после инверсии становятся выше.",
        ),
        "autocontrast": (
            "Автоконтраст",
            "Растягивает тональный диапазон изображения, чтобы рельеф использовал больше доступной высоты.",
        ),
        "gamma": (
            "Гамма",
            "Меняет влияние средних тонов на высоту. Меньшие значения поднимают полутона, большие делают их слабее.",
        ),
        "blur_radius": (
            "Размытие",
            "Добавляет гауссово сглаживание перед построением карты высот. Полезно для уменьшения шума.",
        ),
        "width_mm": ("Ширина (мм)", "Физический размер модели по оси X в миллиметрах."),
        "depth_mm": (
            "Глубина (мм)",
            "Физический размер модели по оси Y в миллиметрах. Если оставить пустым, пропорции изображения сохранятся автоматически.",
        ),
        "relief_height": (
            "Высота рельефа (мм)",
            "Максимальная дополнительная высота рельефа над базой. Чем больше значение, тем глубже эффект.",
        ),
        "base_thickness": (
            "Толщина базы (мм)",
            "Толщина сплошной подложки под рельефом. Делает модель более жесткой и удобной для печати.",
        ),
        "resolution_x": (
            "Разрешение X",
            "Количество столбцов выборки при построении карты высот. Больше значение — выше детализация и тяжелее файлы.",
        ),
        "resolution_y": (
            "Разрешение Y",
            "Количество строк выборки при построении карты высот. Больше значение — выше детализация и больше нагрузка.",
        ),
        "line_width": (
            "Ширина линии (мм)",
            "Ширина экструзии для генерации G-code. Обычно должна соответствовать настройкам сопла и печати.",
        ),
        "layer_height": (
            "Высота слоя (мм)",
            "Вертикальный шаг между слоями. Меньшие значения улучшают детализацию, но увеличивают время печати.",
        ),
        "filament_diameter": (
            "Диаметр филамента (мм)",
            "Диаметр прутка, используемый в расчете экструзии. Для большинства принтеров это 1.75 мм.",
        ),
        "origin_x": ("Смещение X (мм)", "Положение модели по оси X на столе в сгенерированном G-code."),
        "origin_y": ("Смещение Y (мм)", "Положение модели по оси Y на столе в сгенерированном G-code."),
        "extrusion_multiplier": (
            "Множитель экструзии",
            "Масштабирует количество подаваемого материала. Полезно для тонкой коррекции недо- или переэкструзии.",
        ),
        "print_speed": ("Скорость печати", "Основная скорость печати обычных слоев в миллиметрах в минуту."),
        "first_layer_speed": (
            "Первый слой",
            "Скорость печати первого слоя. Более низкие значения обычно улучшают прилипание к столу.",
        ),
        "travel_speed": (
            "Скорость перемещений",
            "Скорость холостых перемещений без печати. Большие значения сокращают время, но сильнее нагружают механику.",
        ),
        "z_speed": ("Скорость Z", "Скорость движения по оси Z в миллиметрах в минуту."),
        "z_hop": (
            "Подъем Z",
            "Временный подъем сопла перед перемещением, чтобы уменьшить риск задевания уже напечатанных участков.",
        ),
        "nozzle_temperature": (
            "Сопло C",
            "Температура сопла в градусах Цельсия для G-code. Установите 0, чтобы не добавлять команды нагрева.",
        ),
        "bed_temperature": (
            "Стол C",
            "Температура стола в градусах Цельсия для G-code. Установите 0, чтобы не добавлять команды нагрева.",
        ),
        "fan_speed": ("Обдув 0-255", "Мощность вентилятора в G-code. 0 — выключено, 255 — максимум."),
    },
}


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


def default_gui_language() -> str:
    try:
        locale_name = locale.getlocale()[0]
    except (ValueError, IndexError, TypeError):
        locale_name = None
    if locale_name and locale_name.lower().startswith("ru"):
        return "ru"
    return "en"


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
            self.current_language = default_gui_language()
            self.root.title(GUI_TRANSLATIONS[self.current_language]["app_title"])
            self.root.geometry("920x760")
            self.root.minsize(820, 640)

            self.input_path_var = tk.StringVar(value=str(preset_input) if preset_input else "")
            self.language_var = tk.StringVar(value=GUI_LANGUAGE_NAMES[self.current_language])
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
            self.help_title_var = tk.StringVar(value="")
            self.help_body_var = tk.StringVar(value="")
            self.current_help_key: str | None = None
            self.translatable_widgets: list[tuple[object, str, str]] = []

            self.status_text = tk.Text(root, height=14, wrap="word", state="disabled")
            self.preview_label: ttk.Label | None = None
            self.preview_image = None

            self.build_layout(ttk, filedialog, messagebox)
            self.apply_language()

        def build_layout(self, ttk_module, filedialog_module, messagebox_module) -> None:
            container = ttk_module.Frame(self.root, padding=14)
            container.pack(fill="both", expand=True)
            container.columnconfigure(0, weight=1)
            container.rowconfigure(0, weight=1)
            container.rowconfigure(1, weight=0)
            container.rowconfigure(2, weight=0)

            canvas = tk.Canvas(container, highlightthickness=0)
            v_scrollbar = ttk_module.Scrollbar(container, orient="vertical", command=canvas.yview)
            h_scrollbar = ttk_module.Scrollbar(container, orient="horizontal", command=canvas.xview)
            content = ttk_module.Frame(canvas, padding=(0, 0, 6, 0))
            content.bind(
                "<Configure>",
                lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=content, anchor="nw")
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            content.columnconfigure(0, weight=1)
            content.columnconfigure(1, weight=1)
            content.columnconfigure(2, weight=0)

            files_frame = ttk_module.LabelFrame(content, text="", padding=12)
            files_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            files_frame.columnconfigure(1, weight=1)
            self.register_translatable(files_frame, "frame_files")

            input_label = ttk_module.Label(files_frame, text="")
            input_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
            input_entry = ttk_module.Entry(files_frame, textvariable=self.input_path_var)
            input_entry.grid(row=0, column=1, sticky="ew")
            input_button = ttk_module.Button(
                files_frame,
                text="",
                command=lambda: self.pick_input_file(filedialog_module),
            )
            input_button.grid(row=0, column=2, padx=(8, 0))
            self.register_translatable(input_label, "label_input_image")
            self.register_translatable(input_button, "button_browse")
            self.register_help(input_label, "input_image")
            self.register_help(input_entry, "input_image")
            self.register_help(input_button, "input_image")

            output_label = ttk_module.Label(files_frame, text="")
            output_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
            output_entry = ttk_module.Entry(files_frame, textvariable=self.output_dir_var)
            output_entry.grid(row=1, column=1, sticky="ew", pady=(8, 0))
            output_button = ttk_module.Button(
                files_frame,
                text="",
                command=lambda: self.pick_output_dir(filedialog_module),
            )
            output_button.grid(row=1, column=2, padx=(8, 0), pady=(8, 0))
            self.register_translatable(output_label, "label_output_folder")
            self.register_translatable(output_button, "button_browse")
            self.register_help(output_label, "output_folder")
            self.register_help(output_entry, "output_folder")
            self.register_help(output_button, "output_folder")

            language_label = ttk_module.Label(files_frame, text="")
            language_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
            language_box = ttk_module.Combobox(
                files_frame,
                textvariable=self.language_var,
                state="readonly",
                values=[GUI_LANGUAGE_NAMES["en"], GUI_LANGUAGE_NAMES["ru"]],
                width=18,
            )
            language_box.grid(row=2, column=1, sticky="w", pady=(8, 0))
            language_box.bind("<<ComboboxSelected>>", self.on_language_change, add="+")
            self.register_translatable(language_label, "label_language")
            self.register_help(language_label, "language")
            self.register_help(language_box, "language")

            outputs_frame = ttk_module.LabelFrame(content, text="", padding=12)
            outputs_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            self.register_translatable(outputs_frame, "frame_exports")
            export_gcode = ttk_module.Checkbutton(outputs_frame, text="", variable=self.export_gcode_var)
            export_gcode.grid(row=0, column=0, sticky="w")
            export_obj = ttk_module.Checkbutton(outputs_frame, text="", variable=self.export_obj_var)
            export_obj.grid(row=1, column=0, sticky="w")
            export_stl = ttk_module.Checkbutton(outputs_frame, text="", variable=self.export_stl_var)
            export_stl.grid(row=2, column=0, sticky="w")
            self.register_translatable(export_gcode, "toggle_gcode")
            self.register_translatable(export_obj, "toggle_obj")
            self.register_translatable(export_stl, "toggle_stl")
            self.register_help(export_gcode, "export_gcode")
            self.register_help(export_obj, "export_obj")
            self.register_help(export_stl, "export_stl")

            tone_frame = ttk_module.LabelFrame(content, text="", padding=12)
            tone_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            self.register_translatable(tone_frame, "frame_processing")
            invert_toggle = ttk_module.Checkbutton(
                tone_frame, text="", variable=self.invert_var
            )
            invert_toggle.grid(row=0, column=0, sticky="w")
            autocontrast_toggle = ttk_module.Checkbutton(
                tone_frame, text="", variable=self.autocontrast_var
            )
            autocontrast_toggle.grid(row=1, column=0, sticky="w")
            self.register_translatable(invert_toggle, "toggle_invert")
            self.register_translatable(autocontrast_toggle, "toggle_autocontrast")
            self.register_help(invert_toggle, "invert")
            self.register_help(autocontrast_toggle, "autocontrast")
            self.add_labeled_entry(ttk_module, tone_frame, "field_gamma", self.gamma_var, 2, "gamma")
            self.add_labeled_entry(
                ttk_module, tone_frame, "field_blur_radius", self.blur_radius_var, 3, "blur_radius"
            )

            geometry_frame = ttk_module.LabelFrame(content, text="", padding=12)
            geometry_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            geometry_frame.columnconfigure(1, weight=1)
            self.register_translatable(geometry_frame, "frame_geometry")
            self.add_labeled_entry(
                ttk_module, geometry_frame, "field_width_mm", self.width_mm_var, 0, "width_mm"
            )
            self.add_labeled_entry(
                ttk_module, geometry_frame, "field_depth_mm", self.depth_mm_var, 1, "depth_mm"
            )
            self.add_labeled_entry(
                ttk_module,
                geometry_frame,
                "field_relief_height",
                self.relief_height_var,
                2,
                "relief_height",
            )
            self.add_labeled_entry(
                ttk_module,
                geometry_frame,
                "field_base_thickness",
                self.base_thickness_var,
                3,
                "base_thickness",
            )
            self.add_labeled_entry(
                ttk_module, geometry_frame, "field_resolution_x", self.resolution_x_var, 4, "resolution_x"
            )
            self.add_labeled_entry(
                ttk_module, geometry_frame, "field_resolution_y", self.resolution_y_var, 5, "resolution_y"
            )

            print_frame = ttk_module.LabelFrame(content, text="", padding=12)
            print_frame.grid(row=2, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            print_frame.columnconfigure(1, weight=1)
            self.register_translatable(print_frame, "frame_print")
            self.add_labeled_entry(
                ttk_module, print_frame, "field_line_width", self.line_width_var, 0, "line_width"
            )
            self.add_labeled_entry(
                ttk_module, print_frame, "field_layer_height", self.layer_height_var, 1, "layer_height"
            )
            self.add_labeled_entry(
                ttk_module,
                print_frame,
                "field_filament_diameter",
                self.filament_diameter_var,
                2,
                "filament_diameter",
            )
            self.add_labeled_entry(
                ttk_module, print_frame, "field_origin_x", self.origin_x_var, 3, "origin_x"
            )
            self.add_labeled_entry(
                ttk_module, print_frame, "field_origin_y", self.origin_y_var, 4, "origin_y"
            )
            self.add_labeled_entry(
                ttk_module,
                print_frame,
                "field_extrusion_multiplier",
                self.extrusion_multiplier_var,
                5,
                "extrusion_multiplier",
            )

            speeds_frame = ttk_module.LabelFrame(content, text="", padding=12)
            speeds_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            self.register_translatable(speeds_frame, "frame_speed")
            for col_index in (1, 3, 5):
                speeds_frame.columnconfigure(col_index, weight=1)
            self.add_grid_entry(ttk_module, speeds_frame, "field_print_speed", self.print_speed_var, 0, 0, "print_speed")
            self.add_grid_entry(
                ttk_module,
                speeds_frame,
                "field_first_layer_speed",
                self.first_layer_speed_var,
                0,
                2,
                "first_layer_speed",
            )
            self.add_grid_entry(
                ttk_module, speeds_frame, "field_travel_speed", self.travel_speed_var, 0, 4, "travel_speed"
            )
            self.add_grid_entry(ttk_module, speeds_frame, "field_z_speed", self.z_speed_var, 1, 0, "z_speed")
            self.add_grid_entry(ttk_module, speeds_frame, "field_z_hop", self.z_hop_var, 1, 2, "z_hop")
            self.add_grid_entry(
                ttk_module,
                speeds_frame,
                "field_nozzle_temperature",
                self.nozzle_temperature_var,
                1,
                4,
                "nozzle_temperature",
            )
            self.add_grid_entry(
                ttk_module, speeds_frame, "field_bed_temperature", self.bed_temperature_var, 2, 0, "bed_temperature"
            )
            self.add_grid_entry(
                ttk_module, speeds_frame, "field_fan_speed", self.fan_speed_var, 2, 2, "fan_speed"
            )

            help_frame = ttk_module.LabelFrame(content, text="", padding=12)
            help_frame.grid(row=0, column=2, rowspan=5, sticky="nsew", padx=(12, 0), pady=(0, 10))
            help_frame.columnconfigure(0, weight=1)
            self.register_translatable(help_frame, "frame_description")
            help_title_label = ttk_module.Label(
                help_frame,
                textvariable=self.help_title_var,
                font=("TkDefaultFont", 11, "bold"),
                anchor="w",
                justify="left",
            )
            help_title_label.grid(row=0, column=0, sticky="ew")
            help_body_label = ttk_module.Label(
                help_frame,
                textvariable=self.help_body_var,
                wraplength=260,
                anchor="nw",
                justify="left",
            )
            help_body_label.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

            preview_frame = ttk_module.LabelFrame(content, text="", padding=12)
            preview_frame.grid(row=4, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
            self.register_translatable(preview_frame, "frame_preview")
            self.preview_label = ttk_module.Label(preview_frame, text="")
            self.preview_label.pack(fill="both", expand=True)
            self.register_translatable(self.preview_label, "preview_placeholder")

            log_frame = ttk_module.LabelFrame(content, text="", padding=12)
            log_frame.grid(row=4, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
            self.register_translatable(log_frame, "frame_log")
            self.status_text.pack(in_=log_frame, fill="both", expand=True)

            actions = ttk_module.Frame(container)
            actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            actions.columnconfigure(0, weight=1)
            generate_button = ttk_module.Button(
                actions,
                text="",
                command=lambda: self.generate(messagebox_module),
            )
            generate_button.grid(row=0, column=0, sticky="e")
            self.register_translatable(generate_button, "button_generate")

        def tr(self, key: str, **kwargs) -> str:
            text = GUI_TRANSLATIONS[self.current_language].get(key, key)
            if kwargs:
                return text.format(**kwargs)
            return text

        def register_translatable(self, widget, key: str, option: str = "text") -> None:
            self.translatable_widgets.append((widget, option, key))

        def apply_language(self) -> None:
            self.root.title(self.tr("app_title"))
            for widget, option, key in self.translatable_widgets:
                widget.configure(**{option: self.tr(key)})
            if self.preview_label is not None:
                if self.preview_image is None:
                    self.preview_label.configure(text=self.tr("preview_placeholder"))
                else:
                    self.preview_label.configure(text="")
            if self.current_help_key is None:
                self.help_title_var.set(self.tr("help_default_title"))
                self.help_body_var.set(self.tr("help_default_text"))
            else:
                self.set_help(self.current_help_key)

        def on_language_change(self, _event=None) -> None:
            selected_name = self.language_var.get()
            for code, display_name in GUI_LANGUAGE_NAMES.items():
                if display_name == selected_name:
                    self.current_language = code
                    break
            self.apply_language()

        def set_help(self, help_key: str) -> None:
            self.current_help_key = help_key
            title, body = GUI_FIELD_HELP[self.current_language].get(
                help_key,
                (self.tr("help_default_title"), self.tr("help_default_text")),
            )
            self.help_title_var.set(title)
            self.help_body_var.set(body)

        def register_help(self, widget, help_key: str) -> None:
            widget.bind("<Enter>", lambda event, key=help_key: self.set_help(key), add="+")
            widget.bind("<FocusIn>", lambda event, key=help_key: self.set_help(key), add="+")

        def add_labeled_entry(
            self,
            ttk_module,
            parent,
            label_key: str,
            variable: tk.StringVar,
            row: int,
            help_key: str,
        ) -> None:
            label_widget = ttk_module.Label(parent, text="")
            label_widget.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
            entry_widget = ttk_module.Entry(parent, textvariable=variable)
            entry_widget.grid(row=row, column=1, sticky="ew", pady=4)
            self.register_translatable(label_widget, label_key)
            self.register_help(label_widget, help_key)
            self.register_help(entry_widget, help_key)

        def add_grid_entry(
            self,
            ttk_module,
            parent,
            label_key: str,
            variable: tk.StringVar,
            row: int,
            column: int,
            help_key: str,
        ) -> None:
            label_widget = ttk_module.Label(parent, text="")
            label_widget.grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
            entry_widget = ttk_module.Entry(parent, textvariable=variable, width=12)
            entry_widget.grid(row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=4)
            self.register_translatable(label_widget, label_key)
            self.register_help(label_widget, help_key)
            self.register_help(entry_widget, help_key)

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
                title=self.tr("dialog_input_title"),
                filetypes=[
                    (self.tr("filetype_images"), "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
                    (self.tr("filetype_all"), "*.*"),
                ],
            )
            if path:
                self.input_path_var.set(path)
                self.output_dir_var.set(str(Path(path).resolve().parent))

        def pick_output_dir(self, filedialog_module) -> None:
            path = filedialog_module.askdirectory(title=self.tr("dialog_output_title"))
            if path:
                self.output_dir_var.set(path)

        def build_settings(self) -> tuple[HeightmapSettings, PrintSettings, Path, Path | None, Path | None, Path | None]:
            input_path = Path(self.input_path_var.get()).expanduser().resolve()
            if not input_path.exists():
                raise ValueError(self.tr("error_input_missing", path=input_path))

            output_dir = Path(self.output_dir_var.get()).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

            stem = input_path.stem
            heightmap_out = output_dir / f"{stem}_heightmap.png"
            gcode_out = output_dir / f"{stem}.gcode" if self.export_gcode_var.get() else None
            obj_out = output_dir / f"{stem}.obj" if self.export_obj_var.get() else None
            stl_out = output_dir / f"{stem}.stl" if self.export_stl_var.get() else None

            heightmap_settings = HeightmapSettings(
                input_path=input_path,
                width_mm=required_positive_float(self.width_mm_var.get(), self.tr("label_width")),
                depth_mm=optional_positive_float(self.depth_mm_var.get()),
                relief_height_mm=required_positive_float(
                    self.relief_height_var.get(), self.tr("label_relief_height_short")
                ),
                base_thickness_mm=required_non_negative_float(
                    self.base_thickness_var.get(), self.tr("label_base_thickness_short")
                ),
                invert=self.invert_var.get(),
                autocontrast=self.autocontrast_var.get(),
                gamma=required_positive_float(self.gamma_var.get(), self.tr("label_gamma_short")),
                blur_radius=required_non_negative_float(
                    self.blur_radius_var.get(), self.tr("label_blur_radius_short")
                ),
                resolution_x=optional_positive_int(self.resolution_x_var.get()),
                resolution_y=optional_positive_int(self.resolution_y_var.get()),
            )

            fan_speed = int(self.fan_speed_var.get())
            if not 0 <= fan_speed <= 255:
                raise ValueError(self.tr("error_fan_speed"))

            print_settings = PrintSettings(
                line_width_mm=required_positive_float(self.line_width_var.get(), self.tr("label_line_width")),
                layer_height_mm=required_positive_float(
                    self.layer_height_var.get(), self.tr("label_layer_height_short")
                ),
                filament_diameter_mm=required_positive_float(
                    self.filament_diameter_var.get(), self.tr("label_filament_diameter_short")
                ),
                print_speed_mmpm=required_positive_float(
                    self.print_speed_var.get(), self.tr("label_print_speed_short")
                ),
                first_layer_speed_mmpm=required_positive_float(
                    self.first_layer_speed_var.get(), self.tr("label_first_layer_speed_short")
                ),
                travel_speed_mmpm=required_positive_float(
                    self.travel_speed_var.get(), self.tr("label_travel_speed_short")
                ),
                z_speed_mmpm=required_positive_float(self.z_speed_var.get(), self.tr("label_z_speed_short")),
                z_hop_mm=required_non_negative_float(self.z_hop_var.get(), self.tr("label_z_hop_short")),
                extrusion_multiplier=required_positive_float(
                    self.extrusion_multiplier_var.get(), self.tr("label_extrusion_multiplier_short")
                ),
                origin_x_mm=required_non_negative_float(self.origin_x_var.get(), self.tr("label_origin_x_short")),
                origin_y_mm=required_non_negative_float(self.origin_y_var.get(), self.tr("label_origin_y_short")),
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
                self.preview_label.configure(text=f"{self.tr('preview_saved_to')}\n{heightmap_path}")
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
                messagebox_module.showerror(self.tr("error_generation_failed"), str(exc))
                return

            self.update_preview(summary.heightmap_path)
            self.append_status(self.tr("status_heightmap_preview", path=summary.heightmap_path))
            self.append_status(
                self.tr(
                    "status_print_size",
                    width=summary.heightmap.width_mm,
                    depth=summary.heightmap.depth_mm,
                    height=summary.heightmap.total_height_mm,
                )
            )
            if summary.gcode_path is not None and summary.gcode_stats is not None:
                self.append_status(
                    self.tr("status_gcode", path=summary.gcode_path)
                )
                self.append_status(
                    self.tr(
                        "status_layers",
                        layers=summary.gcode_stats.layer_count,
                        segments=summary.gcode_stats.print_segments,
                        filament=summary.gcode_stats.filament_mm / 1000,
                    )
                )
            if summary.obj_path is not None:
                self.append_status(self.tr("status_obj", path=summary.obj_path))
            if summary.stl_path is not None:
                self.append_status(self.tr("status_stl", path=summary.stl_path))
            if summary.mesh_vertices is not None and summary.mesh_faces is not None:
                self.append_status(
                    self.tr(
                        "status_mesh",
                        vertices=summary.mesh_vertices,
                        triangles=summary.mesh_faces,
                    )
                )

            message_lines = [self.tr("msg_heightmap_saved", path=summary.heightmap_path)]
            if summary.gcode_path is not None:
                message_lines.append(self.tr("msg_gcode_saved", path=summary.gcode_path))
            if summary.obj_path is not None:
                message_lines.append(self.tr("msg_obj_saved", path=summary.obj_path))
            if summary.stl_path is not None:
                message_lines.append(self.tr("msg_stl_saved", path=summary.stl_path))
            messagebox_module.showinfo(self.tr("info_generation_completed"), "\n".join(message_lines))

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
