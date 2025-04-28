# Stller - STL File Viewer/Editor
STLLER is a Python-based STL file viewer with advanced face selection capabilities to split STL files. It was developed to assist OpenFOAM users with the pre-processing of STL files before meshing. The tool allows users to:

1. View 3D STL models with detailed information (points, faces, area, volume)
2. Select faces using two modes:\
   -Direct selection of individual faces\
   -Region growing selection (picks connected faces with similar normals)\
3. Organize selections into multiple color-coded groups
4. Export selections to the same or new STL files to split the STL

The tool uses PyVista for 3D visualization and VTK for the underlying mesh operations. It provides both a graphical interface with interactive controls and a command-line interface with various options.

To use STLLER, you need Python 3.7+ with PyVista, NumPy, and VTK installed. The repository includes a sample STL file (mixingpipe.stl) you can use for testing.

Run it with: python stller.py mixingpipe.stl

The interactive controls include:
    - Mouse navigation (rotate, zoom, pan)
    - Keyboard shortcuts (m: toggle selection, r: region growing, g: new group)

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
python stller.py [-h] [--no-edges] [--color COLOR] [--export EXPORT] [--only-selected] [--window-size WIDTH HEIGHT] filepath
```

- `filepath`: Path to the STL file to visualize
- `--no-edges`: Hide mesh edges
- `--color COLOR`: Specify mesh color (default: lightblue)
- `--export EXPORT`: Export the selected groups to a new STL file when you close the visualisation window
- `--only-selected`: Export only the selected groups, not the full mesh
- `--window-size WIDTH HEIGHT`: Window size in pixels (default: 1920 1080)
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

Export selected faces:
```bash
python stller.py model.stl --export output.stl --only-selected
```

### Face Selection Modes

The app provides multiple selection modes:

- **Movement Mode**: Navigate the 3D view (default)
- **Selection Mode**: Click faces to select/deselect them
- **Region Growing Mode**: Click a face to select all connected faces with similar normals

You can toggle between modes using:
- The selection mode checkbox in the UI
- Pressing the 'm' key (toggle selection mode)
- Pressing the 'r' key (toggle region growing)

### Selection Groups

You can create multiple selection groups, each with a different color:
- Create a new group with the 'g' key or the "Create New Group" button
- Switch between groups with the 'n' key or the "Next Group" button
- Clear the current group with the "Clear Current Group" button

### Export Functionality

You can export your selections to a new STL file:
- Use the "Export Selection to STL" button during the session
- Use the `--export` command line option when starting

When exporting, you can choose to:
- Export only the selected faces (separate solids for each group)
- Export the full model with selected faces grouped as separate solids

### Controls

- **Left-click + drag**: Rotate the model
- **Right-click + drag**: Zoom in/out
- **Middle-click + drag**: Pan the camera
- **c key**: Reset camera view
- **m key**: Toggle selection mode
- **r key**: Toggle region growing mode
- **g key**: Create new selection group
- **n key**: Switch to next selection group

## Requirements

- Python 3.7+
- PyVista 0.43.0+
- NumPy 1.20.0+
- VTK 9.2.0+

## License

GNU General Public License v3.0
