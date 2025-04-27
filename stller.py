#!/usr/bin/env python3

import sys
import os
import argparse
import pyvista as pv
import numpy as np
import warnings
import vtk
import logging
import colorsys
import random
import time

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Filter PyVista warnings if needed
warnings.filterwarnings("ignore", category=pv.core.errors.PyVistaDeprecationWarning)

def select_faces_by_region_growing(mesh, seed_face_id, angle_tolerance=15.0):
    """
    Select faces from a mesh by region growing from a seed face based on angle tolerance.
    
    Parameters:
    -----------
    mesh : pyvista.PolyData
        The mesh to select faces from
    seed_face_id : int
        The ID of the face to start selection from
    angle_tolerance : float, optional
        The maximum angle (in degrees) between adjacent face normals to be included, default 15.0
    
    Returns:
    --------
    set
        A set of face IDs that are connected to the seed face and within angle tolerance
    """
    logger.info(f"Starting region growing from face {seed_face_id} with angle tolerance {angle_tolerance}°")
    
    # Ensure we have cell normals
    mesh.compute_normals(cell_normals=True, point_normals=True, inplace=True)
    print(f"DEBUG: Mesh has {mesh.n_cells} cells and {mesh.n_points} points")
    
    # Get face normals
    face_normals = mesh.cell_normals
    seed_normal = face_normals[seed_face_id]
    print(f"DEBUG: Seed face normal: {seed_normal}")
    
    # Build cell neighbors connectivity
    print(f"DEBUG: Building cell connectivity...")
    
    # Initialize a dictionary to store connectivity
    cell_neighbors = {}
    
    # For each cell, find the points it contains
    cell_to_points = {}
    # For each point, find the cells it's part of
    point_to_cells = {}
    
    # Build the mappings
    for cell_id in range(mesh.n_cells):
        cell = mesh.get_cell(cell_id)
        point_ids = cell.point_ids
        cell_to_points[cell_id] = point_ids
        
        # Update point to cells mapping
        for pt_id in point_ids:
            if pt_id not in point_to_cells:
                point_to_cells[pt_id] = set()
            point_to_cells[pt_id].add(cell_id)
    
    # Now find neighbors for each cell (cells that share points)
    for cell_id in range(mesh.n_cells):
        if cell_id not in cell_neighbors:
            cell_neighbors[cell_id] = set()
            
        # Get points of this cell
        points = cell_to_points[cell_id]
        
        # Find all cells that share points with this cell
        for pt_id in points:
            for neighbor_id in point_to_cells.get(pt_id, set()):
                if neighbor_id != cell_id:
                    cell_neighbors[cell_id].add(neighbor_id)
    
    # Convert sets to lists for consistent output
    for cell_id in cell_neighbors:
        cell_neighbors[cell_id] = list(cell_neighbors[cell_id])
    
    # Debug: print seed face neighbors
    print(f"DEBUG: Seed face {seed_face_id} has {len(cell_neighbors[seed_face_id])} neighbors: {cell_neighbors[seed_face_id]}")
    
    # Debug: print angles with seed face for all neighbors
    for neighbor_id in cell_neighbors[seed_face_id]:
        neighbor_normal = face_normals[neighbor_id]
        dot_product = np.dot(seed_normal, neighbor_normal)
        # Handle floating point errors in dot product
        dot_product = np.clip(dot_product, -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        print(f"DEBUG: Neighbor {neighbor_id} has normal {neighbor_normal}, angle with seed: {angle:.2f}°")
    
    # Initialize the selected faces with the seed face
    selected_faces = {seed_face_id}
    candidates = set(cell_neighbors[seed_face_id])
    
    # Region growing
    print(f"DEBUG: Starting region growing with {len(candidates)} initial candidates")
    iteration = 0
    
    while candidates:
        iteration += 1
        print(f"DEBUG: Iteration {iteration}, {len(candidates)} candidates")
        new_candidates = set()
        
        for candidate_id in candidates:
            # Skip if already selected
            if candidate_id in selected_faces:
                continue
            
            # Calculate the angle between the candidate normal and seed normal
            candidate_normal = face_normals[candidate_id]
            dot_product = np.dot(seed_normal, candidate_normal)
            # Handle floating point errors in dot product
            dot_product = np.clip(dot_product, -1.0, 1.0)
            angle = np.degrees(np.arccos(dot_product))
            
            print(f"DEBUG: Candidate {candidate_id} has angle {angle:.2f}° with seed")
            
            # If within tolerance, add to selection and consider its neighbors
            if angle <= angle_tolerance:
                selected_faces.add(candidate_id)
                print(f"DEBUG: Added candidate {candidate_id} to selection (angle: {angle:.2f}°)")
                for neighbor_id in cell_neighbors[candidate_id]:
                    if neighbor_id not in selected_faces and neighbor_id not in candidates:
                        new_candidates.add(neighbor_id)
        
        # Update candidates for next iteration
        candidates = new_candidates
        print(f"DEBUG: Found {len(new_candidates)} new candidates for next iteration")
    
    print(f"DEBUG: Region growing completed with {len(selected_faces)} faces selected")
    logger.info(f"Region growing selected {len(selected_faces)} faces")
    return selected_faces

def generate_distinct_colors(n):
    """Generate n visually distinct colors"""
    colors = []
    for i in range(n):
        # Use golden ratio to get evenly distributed hues
        hue = (i * 0.618033988749895) % 1.0
        # Fixed saturation and value for vibrant colors
        saturation = 0.8
        value = 0.9
        # Convert HSV to RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(rgb)
    return colors

def display_stl(filepath, show_edges=True, color='lightblue', window_size=(1920, 1080)):
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
    window_size : tuple or list, optional
        Size of the window as (width, height), default (1024, 768)
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
    
    # Ensure we have normals calculated
    mesh.compute_normals(inplace=True)
    
    # Create a plotter with specified window size
    plotter = pv.Plotter(window_size=window_size)
    
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
    angle_tolerance = 15.0  # Default angle tolerance for region growing
    region_growing_mode = False
    
    # MultiSelect: Track multiple selection groups with different colors
    selection_groups = []  # List of sets, each set is a group of selected faces
    current_group = 0      # Index of the current active group
    
    # Generate some initial distinct colors for groups
    group_colors = generate_distinct_colors(10)
    
    # Create cell picker for selection
    cell_picker = vtk.vtkCellPicker()
    cell_picker.SetTolerance(0.001)
    
    # Interactive export function
    def export_interactive(value=None):
        # Ask for file path using a simple text prompt in the UI
        plotter.add_text(
            "Enter export path in terminal...",
            position='lower_right',
            font_size=14,
            color='red',
            name='export_prompt'
        )
        plotter.render()
        
        # Get export path from user in terminal
        export_path = input("Enter path to save STL file: ")
        if not export_path.strip():
            print("Export cancelled - no path provided")
            plotter.remove_actor('export_prompt')
            return
        
        # Ask if user wants to export only selected
        only_selected = input("Export only selected faces? (y/n): ").lower().startswith('y')
        
        # Export the selection
        success = export_selection_groups(
            filepath, 
            export_path, 
            selection_groups, 
            only_selected=only_selected
        )
        
        if success:
            plotter.add_text(
                f"Exported to {export_path}",
                position='upper_right',
                font_size=14,
                color='green',
                name='export_prompt'
            )
        else:
            plotter.add_text(
                "Export failed! See terminal for details.",
                position='upper_right',
                font_size=14,
                color='red',
                name='export_prompt'
            )
        
        # Update display after 2 seconds
        time.sleep(2)
        plotter.remove_actor('export_prompt')
        plotter.render()
    
    # Update the status message
    def update_status_message():
        if selection_mode:
            if region_growing_mode:
                mode_txt = f"REGION SELECTION MODE: Click faces to select regions (angle: {angle_tolerance:.1f}°)"
            else:
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
        
        # Update selection counts for all groups
        total_selected = sum(len(group) for group in selection_groups)
        if total_selected > 0:
            # Create status text for all groups
            group_info = []
            for i, group in enumerate(selection_groups):
                if len(group) > 0:
                    group_info.append(f"Group {i+1}: {len(group)} faces")
            
            # Add highlight for current group
            group_text = " | ".join(group_info)
            current_txt = f"Current: Group {current_group+1} | Total: {total_selected} faces"
            
            plotter.add_text(
                f"{current_txt}\n{group_text}",
                position='upper_right',
                font_size=12,
                name='selection_count'
            )
        elif 'selection_count' in plotter.actors:
            # Remove selection count if it exists and no faces selected
            plotter.remove_actor('selection_count')
    
    # Toggle between movement and selection modes
    def toggle_mode():
        nonlocal selection_mode, region_growing_mode
        selection_mode = not selection_mode
        
        # Toggle cell picking based on mode
        if selection_mode:
            # Disable normal camera interactor
            plotter.enable_cell_picking(through=False, callback=cell_picked, show_message=False)
            print(f"DEBUG: Switched to selection mode. Cell picking enabled.")
        else:
            # Call our force movement function to ensure consistent behavior
            force_movement_mode()
        
        update_status_message()
        plotter.render()
    
    # Toggle region growing mode
    def toggle_region_growing():
        nonlocal region_growing_mode
        region_growing_mode = not region_growing_mode
        print(f"DEBUG: Region growing mode {'enabled' if region_growing_mode else 'disabled'}")
        update_status_message()
        plotter.render()
    
    # Create a new selection group
    def create_new_group():
        nonlocal current_group, selection_groups
        
        # If the current group is empty, don't create a new one
        if len(selection_groups) == 0 or len(selection_groups[current_group]) > 0:
            # Add a new empty group
            selection_groups.append(set())
            current_group = len(selection_groups) - 1
            
            # Generate more colors if needed
            if current_group >= len(group_colors):
                group_colors.extend(generate_distinct_colors(5))
                
            print(f"DEBUG: Created new selection group {current_group+1}")
            update_status_message()
            update_selection_display()
            plotter.render()
    
    # Switch to a different selection group
    def next_group():
        nonlocal current_group
        if len(selection_groups) > 0:
            current_group = (current_group + 1) % len(selection_groups)
            print(f"DEBUG: Switched to selection group {current_group+1}")
            update_status_message()
            plotter.render()
    
    # Additional function to force movement mode
    def force_movement_mode(*args):
        nonlocal selection_mode, region_growing_mode
        # Only take action if we're in selection mode
        selection_mode = False
        region_growing_mode = False
        
        # Force disable picking
        plotter.disable_picking()
        
        # Use multiple approaches to reset the camera interactor style
        print("DEBUG: Attempting to reset interaction style")
        
        # Method 1: Use camera reset methods
        try:
            plotter.reset_camera_clipping_range()
            # Try to directly set the interactor style
            if hasattr(plotter, 'iren') and hasattr(plotter.iren, 'interactor_style'):
                plotter.iren.interactor_style.set_style_to_trackball_camera()
            print("DEBUG: Reset camera properties")
        except Exception as e:
            print(f"DEBUG: Error with method 1: {e}")
        
        # Method 2: Reset key events directly
        try:
            plotter.reset_key_events()
            plotter.add_key_event('m', toggle_mode_key)
            plotter.add_key_event('r', toggle_region_key)
            plotter.add_key_event('g', create_new_group_key)
            plotter.add_key_event('n', next_group_key)
            print("DEBUG: Reset key events")
        except Exception as e:
            print(f"DEBUG: Error with method 2: {e}")
        
        # Method 3: Directly set camera properties
        try:
            # Force the interactor to switch back to camera interaction
            plotter.enable_trackball_style()
            print("DEBUG: Enabled trackball style")
        except Exception as e:
            print(f"DEBUG: Error with method 3: {e}")
        
        # Print overall status
        print(f"DEBUG: Forced switch to movement mode")
        
        # Update UI
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
    
    # Add a button to toggle region growing
    plotter.add_checkbox_button_widget(
        toggle_region_growing,
        value=False,
        position=(10, 100),
        size=30,
        border_size=1,
        color_on='blue',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the region growing checkbox
    plotter.add_text(
        "Toggle Region Growing",
        position=(50, 100),
        font_size=12,
        name='region_text'
    )
    
    # Add a button for new selection group
    plotter.add_checkbox_button_widget(
        create_new_group,
        value=False,
        position=(10, 130),
        size=30,
        border_size=1,
        color_on='orange',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the new group button
    plotter.add_text(
        "Create New Group",
        position=(50, 130),
        font_size=12,
        name='new_group_text'
    )
    
    # Add a button to switch between groups
    plotter.add_checkbox_button_widget(
        next_group,
        value=False,
        position=(10, 160),
        size=30,
        border_size=1,
        color_on='purple',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the next group button
    plotter.add_text(
        "Next Group",
        position=(50, 160),
        font_size=12,
        name='next_group_text'
    )
    
    # Add angle tolerance slider
    def update_angle_tolerance(value):
        nonlocal angle_tolerance
        angle_tolerance = value
        plotter.add_text(
            f"Angle Tolerance: {angle_tolerance:.1f}°",
            position=(50, 190),
            font_size=12,
            name='angle_text'
        )
        print(f"DEBUG: Angle tolerance set to {angle_tolerance:.1f}°")
        update_status_message()
    
    plotter.add_slider_widget(
        update_angle_tolerance,
        [1.0, 90.0],
        value=15.0,
        title="Angle Tolerance",
        pointa=(0.02, 0.25),
        pointb=(0.18, 0.25),
        style='modern'
    )
    
    # Add a button to clear selection
    def clear_selection():
        nonlocal selection_groups, current_group
        
        # Clear only the current group
        if len(selection_groups) > current_group:
            selection_groups[current_group] = set()
            print(f"Cleared selection group {current_group+1}")
        
        update_selection_display()
        update_status_message()
    
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
        "Clear Current Group",
        position=(50, 70),
        font_size=12,
        name='clear_text'
    )
    
    # Add a button for force movement mode
    plotter.add_checkbox_button_widget(
        force_movement_mode,
        value=False,
        position=(350, 40),
        size=30,
        border_size=1,
        color_on='yellow',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the force movement button
    plotter.add_text(
        "Force Movement Mode",
        position=(400, 40),
        font_size=12,
        name='force_move_text'
    )
    
    # Add Export Button
    plotter.add_checkbox_button_widget(
        export_interactive,
        value=False,
        position=(10, 220),
        size=30,
        border_size=1,
        color_on='purple',
        color_off='grey',
        background_color='white'
    )
    
    # Add text next to the export button
    plotter.add_text(
        "Export Selection to STL",
        position=(50, 220),
        font_size=12,
        name='export_text'
    )
    
    # Callback for when a cell is picked
    def cell_picked(cell_id):
        nonlocal selection_mode, region_growing_mode, current_group
        print(f"DEBUG: Cell picked callback called with cell_id={cell_id}")
        
        if not selection_mode:
            print(f"DEBUG: Not in selection mode, ignoring pick")
            return
            
        # Check if we received a mesh/grid object instead of an integer cell ID
        if hasattr(cell_id, 'n_cells'):
            print(f"DEBUG: Received a mesh object instead of cell ID")
            # Extract information from the mesh if possible
            if cell_id.n_cells > 0:
                # We could try to extract the cell ID from the mesh, but for safety
                # we'll just return since we received unexpected data format
                print(f"DEBUG: Unable to determine specific cell ID from mesh")
                return
            else:
                print(f"DEBUG: Invalid pick or empty selection, ignoring")
                return
        
        # Check for invalid cell ID (negative)
        if isinstance(cell_id, int) and cell_id < 0:
            print(f"DEBUG: Invalid cell ID {cell_id}, ignoring")
            return
        
        # Make sure we have at least one selection group
        if len(selection_groups) == 0:
            selection_groups.append(set())
            current_group = 0
            print(f"DEBUG: Created initial selection group since none existed")
        
        if region_growing_mode:
            # Use region growing to select connected faces
            print(f"DEBUG: Starting region growing from cell {cell_id}")
            new_selection = select_faces_by_region_growing(mesh, cell_id, angle_tolerance)
            
            # Update the current selection group
            for face_id in new_selection:
                selection_groups[current_group].add(face_id)
            
            print(f"Region growing selected {len(new_selection)} faces based on face {cell_id}")
        else:
            # Single face selection mode
            # Check if the face is in any group
            in_current_group = cell_id in selection_groups[current_group]
            
            if in_current_group:
                # If already in current group, deselect it
                selection_groups[current_group].remove(cell_id)
                print(f"Face {cell_id} removed from group {current_group+1}")
            else:
                # Otherwise, add to current group
                selection_groups[current_group].add(cell_id)
                print(f"Face {cell_id} added to group {current_group+1}")
        
        update_selection_display()
        update_status_message()
    
    # Update the display to highlight selected faces
    def update_selection_display():
        # Remove all previous selection actors
        for i in range(len(selection_groups)):
            actor_name = f'selected_faces_{i}'
            if actor_name in plotter.actors:
                plotter.remove_actor(actor_name)
        
        # Create new actors for each selection group
        for i, group in enumerate(selection_groups):
            if len(group) == 0:
                continue
                
            # Create a mask for this group
            mask = np.zeros(mesh.n_cells, dtype=bool)
            mask[list(group)] = True
            selection = mesh.extract_cells(mask)
            
            # Get the color for this group
            color = group_colors[i % len(group_colors)]
            
            # Add a distinct actor for this group
            plotter.add_mesh(
                selection,
                color=color,
                opacity=0.8,
                show_edges=True,
                line_width=2,
                name=f'selected_faces_{i}'
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
                # Call the same cell_picked function we use for the built-in picker
                cell_picked(cell_id)
        
        plotter.track_click_position(callback=on_left_click, side="left", viewport=True)
    
    # Add key bindings for mode switching
    def toggle_mode_key():
        toggle_mode()
        return
    
    def toggle_region_key():
        toggle_region_growing()
        return
    
    def create_new_group_key():
        create_new_group()
        return
    
    def next_group_key():
        next_group()
        return
        
    plotter.add_key_event('m', toggle_mode_key)
    plotter.add_key_event('r', toggle_region_key)
    plotter.add_key_event('g', create_new_group_key)
    plotter.add_key_event('n', next_group_key)
    
    # Add information about controls
    plotter.add_text(
        "\n"
        "\n"
        "Controls:\n"
        "Left-click + drag: Rotate\n"
        "Right-click + drag: Zoom\n"
        "Middle-click + drag: Pan\n"
        "m: Toggle selection mode\n"
        "r: Toggle region growing\n"
        "g: Create new group\n"
        "n: Next group\n"
        "c: Reset camera",
        position='upper_left', 
        font_size=10,
        name='controls'
    )
    
    # Initialize state and UI
    create_new_group()  # Create the first group
    update_status_message()
    
    # Set up the custom mouse callback for more reliable picking
    setup_mouse_callback()
    
    # Show the mesh
    print("Displaying mesh. Close the window to exit.")
    print("Press 'm' to toggle selection mode")
    print("Press 'r' to toggle region growing mode")
    print("Press 'g' to create a new selection group")
    print("Press 'n' to switch to the next selection group")
    plotter.show()
    
    # Return selected faces when the window is closed
    return selection_groups

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Visualize STL files")
    parser.add_argument('filepath', help='Path to the STL file to visualize')
    parser.add_argument('--no-edges', action='store_true', help='Hide mesh edges')
    parser.add_argument('--color', default='lightblue', help='Mesh color (default: lightblue)')
    parser.add_argument('--export', help='Export the selected groups to a new STL file')
    parser.add_argument('--only-selected', action='store_true', help='Export only the selected groups, not the full mesh')
    parser.add_argument('--window-size', type=int, nargs=2, default=[1920, 1080], 
                        metavar=('WIDTH', 'HEIGHT'),
                        help='Window size in pixels (default: 1920 1080)')
    
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
    selection_groups = display_stl(args.filepath, 
                                  show_edges=not args.no_edges, 
                                  color=args.color,
                                  window_size=args.window_size)
    
    # Report on selection groups
    if selection_groups:
        non_empty_groups = [group for group in selection_groups if len(group) > 0]
        print(f"Total selection groups: {len(non_empty_groups)} non-empty groups")
        
        for i, group in enumerate(selection_groups):
            if len(group) > 0:
                print(f"Group {i+1}: {len(group)} faces")
        
        # If export path is provided, export the selected groups
        if args.export:
            if export_selection_groups(args.filepath, args.export, selection_groups, only_selected=args.only_selected):
                print(f"Successfully exported selection to {args.export}")
            else:
                print(f"Failed to export selection")

def export_selection_groups(input_filepath, output_filepath, selection_groups, only_selected=False):
    """
    Export the selected face groups to a new STL file.
    
    Parameters:
    -----------
    input_filepath : str
        Path to the original STL file
    output_filepath : str
        Path to save the new STL file
    selection_groups : list of sets
        List of sets of face IDs for each selection group
    only_selected : bool, optional
        If True, export only the selected faces, otherwise export the full mesh
        with selected faces grouped together, default False
    
    Returns:
    --------
    bool
        True if export was successful, False otherwise
    """
    try:
        # Read the original mesh
        original_mesh = pv.read(input_filepath)
        print(f"Original mesh loaded: {original_mesh.n_cells} faces, {original_mesh.n_points} points")
        
        # Get non-empty groups
        non_empty_groups = [group for group in selection_groups if len(group) > 0]
        
        if not non_empty_groups:
            print("No faces selected, nothing to export")
            return False
        
        # Count total selected faces
        total_selected = sum(len(group) for group in non_empty_groups)
        print(f"Total selected faces across all groups: {total_selected}")
        
        # Ensure we have a proper file extension
        if not output_filepath.lower().endswith('.stl'):
            output_filepath += '.stl'
        
        if only_selected:
            # Create a set of all selected faces
            all_selected = set()
            for group in non_empty_groups:
                all_selected.update(group)
            
            # Create a list to hold the individual meshes for each group
            group_meshes = []
            for i, group in enumerate(non_empty_groups):
                mask = np.zeros(original_mesh.n_cells, dtype=bool)
                mask[list(group)] = True
                group_mesh = original_mesh.extract_cells(mask)
                group_meshes.append(("Group " + str(i+1), group_mesh))
            
            # Write the selected groups to ASCII STL file with multiple solids
            with open(output_filepath, 'w') as f:
                # Write each group as a separate solid
                for name, mesh in group_meshes:
                    write_ascii_stl_solid(f, mesh, name)
            
            print(f"Exported {len(non_empty_groups)} groups with {total_selected} total faces to {output_filepath}")
        else:
            # Create a set of all selected faces
            all_selected = set()
            for group in non_empty_groups:
                all_selected.update(group)
            
            # Create a mask for non-selected faces (the body)
            body_mask = np.ones(original_mesh.n_cells, dtype=bool)
            body_mask[list(all_selected)] = False
            
            # Extract the body mesh
            body_mesh = None
            if np.any(body_mask):
                body_mesh = original_mesh.extract_cells(body_mask)
            
            # Create meshes for each group
            group_meshes = []
            for i, group in enumerate(non_empty_groups):
                mask = np.zeros(original_mesh.n_cells, dtype=bool)
                mask[list(group)] = True
                group_mesh = original_mesh.extract_cells(mask)
                group_meshes.append(("Group " + str(i+1), group_mesh))
            
            # Write all parts to the ASCII STL file
            with open(output_filepath, 'w') as f:
                # First write the body if it exists
                if body_mesh is not None:
                    write_ascii_stl_solid(f, body_mesh, "Body")
                
                # Then write each group as a separate solid
                for name, mesh in group_meshes:
                    write_ascii_stl_solid(f, mesh, name)
            
            print(f"Exported full mesh to {output_filepath}")
            print(f"- Body: {np.sum(body_mask)} faces")
            for i, group in enumerate(non_empty_groups):
                print(f"- Group {i+1}: {len(group)} faces")
        
        return True
    
    except Exception as e:
        print(f"Error exporting selection: {e}")
        import traceback
        traceback.print_exc()
        return False

def write_ascii_stl_solid(file, mesh, name):
    """
    Write a mesh to an ASCII STL file as a named solid section.
    
    Parameters:
    -----------
    file : file object
        An open file object to write to
    mesh : pyvista.DataSet
        The mesh to write
    name : str
        The name to give to this solid
    """
    # Check if the mesh is PolyData, if not convert it
    if not isinstance(mesh, pv.PolyData):
        print(f"Converting {type(mesh).__name__} to PolyData for solid '{name}'")
        try:
            # For UnstructuredGrid, we need to extract the surface
            mesh = mesh.extract_surface()
        except Exception as e:
            print(f"Error converting mesh for solid '{name}': {e}")
            return
    
    # Ensure mesh has face normals
    mesh.compute_normals(cell_normals=True, inplace=True)
    
    # Write the solid header
    file.write(f"solid {name}\n")
    
    # Iterate through each face (cell) in the mesh
    for i in range(mesh.n_cells):
        # Get the cell
        cell = mesh.get_cell(i)
        
        # Get the points of this cell
        points = [mesh.points[pid] for pid in cell.point_ids]
        
        # Get the face normal
        normal = mesh.cell_normals[i]
        
        # Write the facet
        file.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
        file.write("    outer loop\n")
        
        # Write the vertices
        for point in points:
            file.write(f"      vertex {point[0]:.6e} {point[1]:.6e} {point[2]:.6e}\n")
        
        file.write("    endloop\n")
        file.write("  endfacet\n")
    
    # Write the solid footer
    file.write(f"endsolid {name}\n")

if __name__ == "__main__":
    main() 