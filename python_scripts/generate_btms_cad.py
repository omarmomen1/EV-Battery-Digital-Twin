"""
Tesla Custom BTMS CAD Generator
Author: Omar
Description: Mathematically generates a parametric 3D CAD model of a 
Dielectric Immersion Battery Pack. Upgraded to use a Staggered Honeycomb 
Array of 21700 cells for advanced fluid dynamics and higher C-rate capability.
"""

import cadquery as cq
import os
import math

OUTPUT_DIR = r"D:\MEK\The Digital Twins EV Battery\Production_Repository\cfd_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
EXPORT_PATH = os.path.join(OUTPUT_DIR, "custom_tesla_btms_honeycomb.step") 

def generate_cad():
    print("[INFO] Initializing Parametric CAD Engine...")
    
    # --- Tesla 21700 Cell Parameters ---
    cell_radius = 10.5  # 21mm diameter
    cell_height = 70.0  # 70mm height
    pitch = 25.0        # 25mm distance between cell centers for fluid channels
    rows = 4
    cols_per_row = 10
    
    # Honeycomb math
    y_step = pitch * math.sqrt(3) / 2  # Height of an equilateral triangle
    
    # --- Fluid Domain (Internal Volume) Parameters ---
    # Calculate bounding box for the staggered array
    domain_length = (cols_per_row - 1) * pitch + (pitch / 2) + (2 * cell_radius) + 20
    domain_width = (rows - 1) * y_step + (2 * cell_radius) + 20
    domain_height = cell_height + 10 # 5mm clearance top and bottom
    
    print(f"[INFO] Generating Fluid Domain ({domain_length:.1f}x{domain_width:.1f}x{domain_height:.1f} mm)...")
    fluid_domain = cq.Workplane("XY").box(domain_length, domain_width, domain_height)
    
    print(f"[INFO] Generating {rows * cols_per_row}x 21700 Battery Cells (Staggered Honeycomb)...")
    
    # Build the staggered array points
    pts = []
    # Center the entire array mathematically
    start_x = -((cols_per_row - 1) * pitch + (pitch / 2)) / 2
    start_y = -((rows - 1) * y_step) / 2
    
    for r in range(rows):
        for c in range(cols_per_row):
            x = start_x + (c * pitch)
            # Offset every odd row by half a pitch
            if r % 2 != 0:
                x += pitch / 2
            y = start_y + (r * y_step)
            pts.append((x, y))
            
    # Generate cells at the calculated points
    cells = (
        cq.Workplane("XY")
        .pushPoints(pts)
        .circle(cell_radius)
        .extrude(cell_height)
    )
    
    # Center the cells vertically in the domain
    cells = cells.translate((0, 0, -cell_height/2))
    
    # Subtract cells from the fluid domain
    print("[INFO] Performing Boolean Subtraction (Fluid - Cells)...")
    fluid_domain = fluid_domain.cut(cells)
    
    # --- Inlet and Outlet Manifolds ---
    print("[INFO] Adding Inlet and Outlet Pipes...")
    pipe_radius = 8.0
    pipe_length = 20.0
    
    # Inlet on one side
    inlet = (
        cq.Workplane("YZ")
        .workplane(offset=-domain_length/2 - pipe_length)
        .circle(pipe_radius)
        .extrude(pipe_length)
    )
    
    # Outlet on the opposite side, offset to create cross-flow through the honeycomb
    outlet = (
        cq.Workplane("YZ")
        .workplane(offset=domain_length/2)
        .center(domain_width/4, 0)
        .circle(pipe_radius)
        .extrude(pipe_length)
    )
    
    fluid_domain = fluid_domain.union(inlet).union(outlet)
    
    # --- Assembly ---
    print("[INFO] Assembling Components...")
    assy = cq.Assembly()
    assy.add(fluid_domain, name="Dielectric_Fluid", color=cq.Color("blue"))
    assy.add(cells, name="Battery_Cells_21700", color=cq.Color("gray"))
    
    print(f"[INFO] Exporting Assembly to {EXPORT_PATH}...")
    assy.save(EXPORT_PATH)
    print("[SUCCESS] CAD Generation Complete!")

if __name__ == "__main__":
    generate_cad()
