# Stller - STL File Viewer

A simple Python tool for visualizing STL files using PyVista with face selection capabilities.

## Features

- Open and visualize STL files in 3D
- Display mesh information (number of points, faces, surface area, and volume)
- Interactive 3D viewer with rotation, zoom, and panning
- Face selection mode with UI controls
- Command-line interface with customization options
- Handles deprecation warnings for latest PyVista compatibility

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with the path to an STL file:

```bash
python stller.py path/to/your/file.stl
```

### Command Line Options

```
python stller.py [-h] [--no-edges] [--color COLOR] filepath
```

- `filepath`: Path to the STL file to visualize
- `--no-edges`: Hide mesh edges
- `--color COLOR`: Specify mesh color (default: lightblue)
- `-h, --help`: Show help message

### Examples

Display with default settings:
```bash
python stller.py model.stl
```

Display without edges:
```bash
python stller.py --no-edges model.stl
```

Change mesh color:
```bash
python stller.py --color red model.stl
```

### Face Selection

The app provides two modes:
- **Movement Mode**: Navigate the 3D view (default)
- **Selection Mode**: Click faces to select/deselect them

You can toggle between modes using:
- The selection mode checkbox in the UI
- Pressing the 'm' key

Selected faces will be highlighted in red. You can:
- Click selected faces again to deselect them
- Use the clear selection button to remove all selections
- View the count of selected faces in the upper right corner

### Controls

- **Left-click + drag**: Rotate the model
- **Right-click + drag**: Zoom in/out
- **Middle-click + drag**: Pan the camera
- **r key**: Reset camera view
- **s key**: Take screenshot
- **m key**: Toggle selection mode

## Requirements

- Python 3.7+
- PyVista 0.43.0+
- NumPy 1.20.0+
- VTK 9.2.0+

## License

MIT License 