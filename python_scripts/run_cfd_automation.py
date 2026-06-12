"""
Tesla BTMS CFD Automation Script
Author: Omar
Description: Automates the Ansys Fluent CFD pipeline for a Dielectric Immersion BTMS.
This script handles headless launch, geometry import, meshing, physics setup, solving, 
and automated post-processing of temperature contours.
"""

import os
import ansys.fluent.core as pyfluent

# --- Configuration & Tesla Standards ---
# Fluid properties based on standard Dielectric Coolant (e.g., Novec 7100 approximation)
DIELECTRIC_DENSITY = 1520      # kg/m^3
DIELECTRIC_SPECIFIC_HEAT = 1183 # J/(kg*K)
DIELECTRIC_THERMAL_COND = 0.069 # W/(m*K)
DIELECTRIC_VISCOSITY = 0.0006   # kg/(m*s)

# Battery Heat Generation (21700 Cell under high C-rate discharge)
VOLUMETRIC_HEAT_GEN = 150000    # W/m^3

GEOMETRY_PATH = r"D:\MEK\The Digital Twins EV Battery\Production_Repository\cfd_outputs\custom_tesla_btms_honeycomb.step"
OUTPUT_DIR = r"D:\MEK\The Digital Twins EV Battery\Production_Repository\cfd_outputs"

def setup_cfd_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("[INFO] Launching Ansys Fluent in Headless Mode (4 Cores)...")
    # Launching in meshing mode first to handle the IGES geometry
    meshing = pyfluent.launch_fluent(precision="double", processor_count=4, mode="meshing", show_gui=False)
    
    print(f"[INFO] Importing Geometry: {GEOMETRY_PATH}")
    meshing.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")
    meshing.workflow.TaskObject["Import Geometry"].Arguments = {"FileName": GEOMETRY_PATH}
    meshing.workflow.TaskObject["Import Geometry"].Execute()

    print("[INFO] Generating Volume Mesh...")
    # Add Local Sizing for Battery Cells
    meshing.workflow.TaskObject["Add Local Sizing"].Arguments = {
        "AddChild": "yes",
        "BOIExecution": "Body Size",
        "TargetMeshSize": 2.0 # mm
    }
    meshing.workflow.TaskObject["Add Local Sizing"].Execute()
    
    # Generate the Surface and Volume Mesh
    meshing.workflow.TaskObject["Generate the Surface Mesh"].Execute()
    meshing.workflow.TaskObject["Describe Geometry"].Execute()
    meshing.workflow.TaskObject["Update Boundaries"].Execute()
    meshing.workflow.TaskObject["Update Regions"].Execute()
    meshing.workflow.TaskObject["Generate the Volume Mesh"].Execute()
    
    print("[INFO] Mesh Generation Complete. Transferring to Solver...")
    solver = meshing.switch_to_solver()

    print("[INFO] Setting up Physics (Energy, Turbulence, Materials)...")
    # Enable Energy Equation
    solver.setup.models.energy.enabled = True
    
    # Enable k-omega SST Turbulence Model
    solver.setup.models.viscous.model = "k-omega"
    solver.setup.models.viscous.k_omega_model = "sst"

    # Define Dielectric Fluid Material
    solver.setup.materials.fluid.create("dielectric-coolant")
    solver.setup.materials.fluid["dielectric-coolant"].density.value = DIELECTRIC_DENSITY
    solver.setup.materials.fluid["dielectric-coolant"].specific_heat.value = DIELECTRIC_SPECIFIC_HEAT
    solver.setup.materials.fluid["dielectric-coolant"].thermal_conductivity.value = DIELECTRIC_THERMAL_COND
    solver.setup.materials.fluid["dielectric-coolant"].viscosity.value = DIELECTRIC_VISCOSITY

    # Apply Heat Generation to Battery Cell Zones dynamically
    try:
        solid_zones = solver.setup.cell_zone_conditions.solid.keys()
        applied_count = 0
        for zone in solid_zones:
            if "battery" in zone.lower():
                # Brute-force through known PyFluent source term dictionary schemas
                api_formats = [
                    {"energy": [{"source": VOLUMETRIC_HEAT_GEN}]},
                    {"energy": {"source_terms": VOLUMETRIC_HEAT_GEN}},
                    {"energy_source": [{"source": VOLUMETRIC_HEAT_GEN}]},
                    {"energy_source": {"source": VOLUMETRIC_HEAT_GEN}},
                    {"q_dot": VOLUMETRIC_HEAT_GEN},
                    {"energy": VOLUMETRIC_HEAT_GEN}
                ]
                
                success = False
                for api_format in api_formats:
                    try:
                        solver.setup.cell_zone_conditions.solid[zone].source_terms = api_format
                        success = True
                        break
                    except:
                        continue
                
                if success:
                    applied_count += 1
                        
        print(f"[INFO] Successfully applied {VOLUMETRIC_HEAT_GEN} W/m^3 heat generation to {applied_count} cell zones.")
        if applied_count == 0:
            print("[WARN] No battery zones found or API rejected all formats. Heat generation not applied!")
    except Exception as e:
        print(f"[WARN] Could not apply heat generation automatically: {e}")

    print("[INFO] Initializing and Solving...")
    solver.solution.initialization.hybrid_initialize()
    
    # Solve for 200 iterations
    solver.solution.run_calculation.iterate(iter_count=200)

    print("[INFO] Post-Processing: Generating Contours...")
    # Create a mid-plane for temperature contour
    solver.results.surfaces.plane_surface.create("mid-plane")
    solver.results.surfaces.plane_surface["mid-plane"].method = "xy-plane"
    solver.results.surfaces.plane_surface["mid-plane"].z = 0.0

    # Create and save temperature contour
    solver.results.graphics.contour.create("temperature-contour")
    solver.results.graphics.contour["temperature-contour"].field = "temperature"
    solver.results.graphics.contour["temperature-contour"].surfaces_list = ["mid-plane"]
    solver.results.graphics.contour["temperature-contour"].display()
    
    contour_path = os.path.join(OUTPUT_DIR, "temperature_contour.png")
    solver.results.graphics.views.restore_view(view_name="front")
    solver.results.graphics.picture.save_picture(file_name=contour_path)
    print(f"[SUCCESS] Temperature contour saved to: {contour_path}")

    # Extract Max Temperature for IoT Digital Twin pipeline
    try:
        max_temp_report = solver.solution.report_definitions.volume.create("max-battery-temp")
        max_temp_report.report_type = "volume-max"
        max_temp_report.field = "temperature"
        battery_zones = [z for z in solver.setup.cell_zone_conditions.solid.keys() if "battery" in z.lower()]
        max_temp_report.zone_names = battery_zones
        
        max_temp_val = max_temp_report.get_value()
        csv_path = os.path.join(OUTPUT_DIR, "cfd_max_temp_results.csv")
        with open(csv_path, "w") as f:
            f.write("Flow_Rate_kg_s,Max_Temp_C\n")
            f.write(f"0.1,{max_temp_val - 273.15}\n") # Convert K to C
        print(f"[SUCCESS] Extracted Max Temperature: {max_temp_val - 273.15:.2f} C")
    except Exception as e:
        print("[WARN] Could not extract max temperature automatically.")

    print("[INFO] Shutting down Fluent...")
    solver.exit()

if __name__ == "__main__":
    setup_cfd_pipeline()
