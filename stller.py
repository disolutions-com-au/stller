#!/usr/bin/env python3

import sys
import os
import argparse
import pyvista as pv
import numpy as np
import warnings
import vtk

# Filter PyVista warnings if needed
warnings.filterwarnings("ignore", category=pv.core.errors.PyVistaDeprecationWarning)

def display_stl(filepath, show_edges=True, color='lightblue'):
    """
    Read and display an STL file using PyVista
    
    Parameters:
    -----------
    filepath : str
        Path to the STL file
    show_edges : bool, optional
        Whether to display mesh edges, default True
    color : str, optional
        Color to use for the mesh, default 'lightblue'
    """
    # Print information about the file
    print(f"Loading STL file: {filepath}")
    
    # Read the STL file
    try:
        mesh = pv.read(filepath)
    except Exception as e:
        print(f"Error loading STL file: {e}")
        sys.exit(1)
    
    # Print mesh information
    print(f"Mesh loaded successfully:")
    print(f"  - Number of points: {mesh.n_points}")
    print(f"  - Number of faces: {mesh.n_faces}")
    print(f"  - Surface area: {mesh.area:.2f}")
    print(f"  - Volume: {mesh.volume:.2f}")
    
    # Create a plotter
    plotter = pv.Plotter()
    
    # Add the mesh to the plotter with modern styling
    plotter.add_mesh(
        mesh, 
        show_edges=show_edges,
        color=color,
        edge_color='black',
        smooth_shading=True,
        name='mesh'
    )
    
    # Add axis orientation widget
    plotter.add_axes()
    
    # Add bounding box for scale reference
    plotter.add_bounding_box(color='gray', opacity=0.3)
    
    # Create a selection state
    selection_mode = False
    selected_faces = set()
    
    # Create cell picker for selection
    cell_picker = vtk.vtkCellPicker()
    cell_picker.SetTolerance(0.001)
    
    # Update the status message
    def update_status_message():
        if selection_mode:
            mode_txt = "SELECTION MODE: Click faces to select them"
        else:
            mode_txt = "MOVEMENT MODE: Navigate the model"
            
        # Add or update status message
        plotter.add_text(
            mode_txt,
            position='upper_left',
            font_size=12,
            name='mode_status'
        )
        
        # Update selection count if any faces selected
        if selected_faces:
            plotter.add_text(
                f"Selected: {len(selected_faces)} faces",
                position='upper_right',
                font_size=12,
                name='selection_count'
            )
        elif 'selection_count' in plotter.actors:
            # Remove selection count if it exists and no faces selected
            plotter.remove_actor('selection_count')
    
    # Toggle between movement and selection modes
    def toggle_mode():
        nonlocal selection_mode
        selection_mode = not selection_mode
        
        # Toggle cell picking based on mode
        if selection_mode:
            # Disable normal camera interactor
            plotter.enable_cell_picking(through=False, callback=cell_picked, show_message=False)
            print(f"DEBUG: Switched to selection mode. Cell picking enabled.")
        else:
            # Re-enable normal camera interactor
            plotter.disable_picking()
            print(f"DEBUG: Switched to movement mode. Cell picking disabled.")
        
        update_status_message()
        plotter.render()
    
    # Add a button to toggle selection mode
    plotter.add_checkbox_button_widget(
        toggle_mode,
        value=False,
        position=(10, 40),
        size=30,
        border_size=1,
        color_on='green',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the checkbox
    plotter.add_text(
        "Toggle Selection Mode",
        position=(50, 40),
        font_size=12,
        name='toggle_text'
    )
    
    # Add a button to clear selection
    def clear_selection():
        nonlocal selected_faces
        selected_faces = set()
        update_selection_display()
        update_status_message()
        print("Selection cleared")
    
    # Add a clear selection button
    plotter.add_checkbox_button_widget(
        clear_selection,
        value=False,
        position=(10, 70),
        size=30,
        border_size=1,
        color_on='red',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the clear button
    plotter.add_text(
        "Clear Selection",
        position=(50, 70),
        font_size=12,
        name='clear_text'
    )
    
    # Callback for when a cell is picked
    def cell_picked(cell_id):
        print(f"DEBUG: Cell picked callback called with cell_id={cell_id}")
        
        if not selection_mode:
            print(f"DEBUG: Not in selection mode, ignoring pick")
            return
            
        if cell_id < 0:
            print(f"DEBUG: Invalid cell ID {cell_id}, ignoring")
            return
            
        if cell_id in selected_faces:
            # If already selected, deselect it
            selected_faces.remove(cell_id)
            print(f"Face {cell_id} deselected")
        else:
            # Otherwise, add to selection
            selected_faces.add(cell_id)
            print(f"Face {cell_id} selected")
        
        update_selection_display()
        update_status_message()
    
    # Update the display to highlight selected faces
    def update_selection_display():
        # Remove previous selection actor if it exists
        if 'selected_faces' in plotter.actors:
            plotter.remove_actor('selected_faces')
        
        if not selected_faces:
            return
            
        # Create a new selection mesh
        mask = np.zeros(mesh.n_cells, dtype=bool)
        mask[list(selected_faces)] = True
        selection = mesh.extract_cells(mask)
        
        # Add the selection with a distinct appearance
        plotter.add_mesh(
            selection,
            color='red',
            opacity=0.8,
            show_edges=True,
            line_width=2,
            name='selected_faces'
        )
    
    # Alternative direct picking method
    def setup_mouse_callback():
        def on_left_click(position):
            if not selection_mode:
                return
                
            # The position is already a tuple (x, y)
            x, y = position
            print(f"DEBUG: Mouse click at coordinates ({x}, {y})")
            
            # Use the cell picker to find the cell at the click position
            cell_picker.Pick(x, y, 0, plotter.renderer)
            cell_id = cell_picker.GetCellId()
            
            print(f"DEBUG: Picked cell_id={cell_id}")
            
            if cell_id != -1:
                if cell_id in selected_faces:
                    # If already selected, deselect it
                    selected_faces.remove(cell_id)
                    print(f"Face {cell_id} deselected")
                else:
                    # Otherwise, add to selection
                    selected_faces.add(cell_id)
                    print(f"Face {cell_id} selected")
                
                update_selection_display()
                update_status_message()
        
        plotter.track_click_position(callback=on_left_click, side="left", viewport=True)
    
    # Add key bindings for mode switching
    def toggle_mode_key():
        toggle_mode()
        return
    
    plotter.add_key_event('m', toggle_mode_key)
    
    # Add information about controls
    plotter.add_text(
        "Controls:\n"
        "Left-click + drag: Rotate\n"
        "Right-click + drag: Zoom\n"
        "Middle-click + drag: Pan\n"
        "r: Reset camera\n"
        "s: Take screenshot\n"
        "m: Toggle selection mode",
        position='lower_left', 
        font_size=10,
        name='controls'
    )
    
    # Initialize status message
    update_status_message()
    
    # Set up the custom mouse callback for more reliable picking
    setup_mouse_callback()
    
    # Show the mesh
    print("Displaying mesh. Close the window to exit.")
    print("Press 'm' to toggle selection mode")
    plotter.show()
    
    # Return selected faces when the window is closed
    return selected_faces

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Visualize STL files")
    parser.add_argument('filepath', help='Path to the STL file to visualize')
    parser.add_argument('--no-edges', action='store_true', help='Hide mesh edges')
    parser.add_argument('--color', default='lightblue', help='Mesh color (default: lightblue)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.isfile(args.filepath):
        print(f"Error: File {args.filepath} not found")
        sys.exit(1)
    
    # Check if file has .stl extension
    _, ext = os.path.splitext(args.filepath)
    if ext.lower() != '.stl':
        print(f"Warning: File {args.filepath} does not have .stl extension")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Display the STL file - invert no_edges for show_edges
    selected_faces = display_stl(args.filepath, show_edges=not args.no_edges, color=args.color)
    
    if selected_faces:
        print(f"Selected faces: {selected_faces}")

if __name__ == "__main__":
    main() 