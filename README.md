# Negative To Relief

Negative To Relief is a Python application for preparing relief models for 3D printing.

It takes an image, converts it into a height map, and can export the result in several formats:

- PNG heightmap preview.
- G-code for FDM printers.
- OBJ mesh.
- STL mesh.

The application is useful when a negative image, grayscale picture, or regular image needs to be converted into a printable relief.

## What the Application Does

The input can be:

- A negative image.
- A regular black-and-white image.
- A grayscale image where brightness controls height.

Processing steps:

1. Convert the image to grayscale.
2. Invert it when needed.
3. Smooth and normalize tones.
4. Build a heightmap.
5. Generate G-code, OBJ, STL, and a preview PNG.

## Output

Depending on the selected mode and parameters, the application can create:

- `<image>_heightmap.png` - heightmap preview.
- `<image>.gcode` - printer file.
- `<image>.obj` - mesh model.
- `<image>.stl` - mesh model for slicers and 3D editors.

## Requirements

- Python 3.13 or newer.
- `numpy`.
- `Pillow`.
- Working `tkinter` for the GUI.

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Recommended Launch

If a virtual environment is configured, run the app from it:

```bash
source .venv/bin/activate
python main.py
```

Or start with a selected image:

```bash
source .venv/bin/activate
python main.py image.jpg
```

## Modes

The application has two modes:

- GUI.
- CLI.

## GUI

The GUI is the easiest option for everyday use.

```bash
python3 main.py
```

Or:

```bash
python3 main.py negative.jpg --gui
```

In the interface, you can:

- Select the input image.
- Select the output folder.
- Enable or disable G-code, OBJ, and STL export.
- Configure relief size.
- Configure relief height and base thickness.
- Configure smoothing, gamma, and inversion.
- Set print parameters.

## CLI

The CLI is useful for repeatable runs, automation, and exact parameters.

```bash
python3 main.py negative.jpg
```

By default, the following files are saved next to the source image:

- `negative_heightmap.png`
- `negative.gcode`

## CLI Examples

Generate preview and G-code:

```bash
python3 main.py negative.jpg
```

Generate G-code, OBJ, and STL:

```bash
python3 main.py negative.jpg \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl \
  --gcode-out output/relief.gcode
```

Generate only mesh files without G-code:

```bash
python3 main.py negative.jpg \
  --no-gcode \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl
```

Example with processing and print parameters:

```bash
python3 main.py negative.jpg \
  --width-mm 140 \
  --relief-height-mm 2.8 \
  --base-thickness-mm 1.0 \
  --layer-height-mm 0.2 \
  --line-width-mm 0.4 \
  --autocontrast \
  --gamma 0.9 \
  --blur-radius 0.8 \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl \
  --gcode-out output/relief.gcode
```

## Important Parameters

### Geometry

- +--width-mm` - physical model width.
- +--depth-mm` - physical model depth. If omitted, it is calculated from image proportions.
- +--relief-height-mm` - maximum relief height above the base.
- +--base-thickness-mm` - solid base thickness.

### Quality and Detail

- +--resolution-x` and +--resolution-y` - heightmap grid resolution.
- +--blur-radius` - smoothing for noisy images.
- +--gamma` - contrast adjustment by height.
- +--autocontrast` - automatic tonal range stretching.

### Inversion

By default, the application assumes that the input is a negative and inverts it.

If the source is already a regular heightmap or positive image, use:

```bash
--no-invert
```

### Export

- +--no-gcode` - do not create G-code.
- +--obj-out` - OBJ output path.
- +--stl-out` - STL output path.
- +--heightmap-out` - preview PNG output path.
- +--gcode-out` - G-code output path.

### Print Parameters

- +--line-width-mm` - extrusion line width.
- +--layer-height-mm` - layer height.
- +--filament-diameter-mm` - filament diameter.
- +--print-speed` - print speed.
- +--first-layer-speed` - first layer speed.
- +--travel-speed` - travel speed.
- +--z-speed` - Z-axis speed.
- +--z-hop-mm` - Z-hop height.
- +--origin-x-mm`, +--origin-y-mm` - start position on the print bed.
- +--nozzle-temperature`, +--bed-temperature`, +--fan-speed` - basic print settings.

## Recommended Workflow

1. Use an image with good contrast.
2. Start the GUI or CLI.
3. Generate a heightmap preview first.
4. Check that light and dark areas create the intended relief.
5. Adjust gamma, blur, autocontrast, and relief height if needed.
6. Generate G-code or STL.
7. Before printing, inspect the result in a slicer or G-code viewer.

## Before Printing

- Generated G-code is generic and does not include a printer-specific start profile.
- Temperatures, speeds, and start coordinates should be checked for your machine.
- Always inspect layer preview in a slicer before a real print.
