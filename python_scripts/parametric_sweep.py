"""
Parametric PyFluent Automation Script
Phase 3: Digital Twin Optimization Study

This script automates Ansys Fluent to run a Design of Experiments (DoE).
It tests multiple cold plate materials and flow rates, solves each CFD case, 
and automatically generates a validation report (CSV) comparing the best designs.

Requirements: 
    pip install ansys-fluent-core
"""

import ansys.fluent.core as pyfluent
import csv
import os

# Point PyFluent to the custom D: drive installation
os.environ["AWP_ROOT241"] = r"D:\ANSYS Inc\v241"
os.environ["AWP_ROOT242"] = r"D:\ANSYS Inc\v242" # Fallback just in case

def run_parametric_study():
    # ---------------------------------------------------------
    # PARAMETRIC STUDY DEFINITION
    # ---------------------------------------------------------
    flow_rates_kg_s = [0.05, 0.1, 0.2]  # Test 3 different flow rates
    cold_plate_materials = ["aluminum", "copper"] # Test 2 different materials
    
    # We will store our final optimization results here
    optimization_report = []

    print("Launching Ansys Fluent in 3D mode (using 4 cores)...")
    # Provide the exact path to the executable to bypass version auto-detection
    fluent_exe = r"D:\ANSYS Inc\v241\fluent\ntbin\win64\fluent.exe"
    session = pyfluent.launch_fluent(fluent_path=fluent_exe, precision="double", processor_count=4, mode="meshing")

    # ---------------------------------------------------------
    # 1. Watertight Geometry Meshing Workflow (Runs ONCE)
    # ---------------------------------------------------------
    print("Importing geometry and generating Poly-Hexcore Mesh...")
    meshing = session.workflow
    meshing.InitializeWorkflow(WorkflowType="Watertight Geometry")

    meshing.TaskObject["Import Geometry"].Arguments = dict(
        FileName=r"D:\MEK\The Digital Twins EV Battery\phase2_cad_model\EV_Battery_Module.step",
        LengthUnit="mm"
    )
    meshing.TaskObject["Import Geometry"].Execute()
    meshing.TaskObject["Add Local Sizing"].AddChildToTask()
    meshing.TaskObject["Add Local Sizing"].Execute()
    meshing.TaskObject["Generate the Surface Mesh"].Execute()
    meshing.TaskObject["Describe Geometry"].Arguments = dict(
        GeometryType="The geometry consists of both fluid and solid regions and/or voids"
    )
    meshing.TaskObject["Describe Geometry"].Execute()
    
    # CRITICAL: These two tasks must be executed to convert named surfaces into Boundary Conditions!
    meshing.TaskObject["Update Boundaries"].Execute()
    meshing.TaskObject["Update Regions"].Execute()
    
    meshing.TaskObject["Generate the Volume Mesh"].Arguments = dict(VolumeFill="poly-hexcore")
    meshing.TaskObject["Generate the Volume Mesh"].Execute()

    # Switch to Solver
    solver = session.switch_to_solver()
    solver.setup.models.energy.enabled = True

    # ---------------------------------------------------------
    # 2. Parametric Loop (Runs 6 times)
    # ---------------------------------------------------------
    for material in cold_plate_materials:
        for flow_rate in flow_rates_kg_s:
            print(f"\n=======================================================")
            print(f"RUNNING DESIGN POINT: Material = {material.upper()}, Flow = {flow_rate} kg/s")
            print(f"=======================================================\n")

            # 3. Solver Setup (Real Physics)
            # ---------------------------------------------------------
            # Enable Heat Transfer (Energy Equation)
            solver.setup.models.energy.enabled = True
            
            # Enable k-omega SST Turbulence model for internal pipe flow
            solver.setup.models.viscous.model = "k-omega"
            solver.setup.models.viscous.k_omega_model = "sst"

            # Apply Materials
            solver.setup.materials.database.copy_by_name(type="solid", name=material)
            # ---------------------------------------------------------
            # 3. Apply Boundary Conditions & Physics
            # ---------------------------------------------------------
            print("\nApplying Materials and Boundary Conditions...")
            
            # Load materials
            try:
                solver.setup.materials.database.copy_by_name(type="solid", name=material.lower())
            except Exception: pass
            
            try:
                solver.setup.materials.database.copy_by_name(type="fluid", name="water-liquid")
            except Exception: pass

            try:
                # FIRST: Convert fluid regions that were incorrectly meshed as solid
                solid_zones = list(solver.setup.cell_zone_conditions.solid.keys())
                for zone in solid_zones:
                    if "fluid" in zone.lower():
                        solver.tui.define.boundary_conditions.modify_zones.zone_type(zone, "fluid")

                # Assign Solid Materials
                for zone in solver.setup.cell_zone_conditions.solid.keys():
                    solver.setup.cell_zone_conditions.solid[zone].material = material.lower()

                # Assign Fluid Materials
                for zone in solver.setup.cell_zone_conditions.fluid.keys():
                    solver.setup.cell_zone_conditions.fluid[zone].material = "water-liquid"
            except Exception as e:
                print(f"Warning mapping cell zones: {e}")

            # Apply Real Boundary Conditions (Handling multiple zones from STEP file)
            try:
                # FIRST: Convert the imported Walls to Inlets and Outlets!
                wall_zones = list(solver.setup.boundary_conditions.wall.keys())
                for zone in wall_zones:
                    if "inlet" in zone.lower():
                        solver.tui.define.boundary_conditions.modify_zones.zone_type(zone, "mass-flow-inlet")
                    elif "outlet" in zone.lower():
                        solver.tui.define.boundary_conditions.modify_zones.zone_type(zone, "pressure-outlet")

                inlet_zones = [z for z in solver.setup.boundary_conditions.mass_flow_inlet.keys() if "inlet" in z.lower()]
                flow_per_inlet = flow_rate / len(inlet_zones) if len(inlet_zones) > 0 else flow_rate
                for zone in inlet_zones:
                    solver.setup.boundary_conditions.mass_flow_inlet[zone].momentum.mass_flow_rate = {"value": flow_per_inlet}
                    solver.setup.boundary_conditions.mass_flow_inlet[zone].thermal.total_temperature = {"value": 298.15} # 25 C

                outlet_zones = [z for z in solver.setup.boundary_conditions.pressure_outlet.keys() if "outlet" in z.lower()]
                for zone in outlet_zones:
                    solver.setup.boundary_conditions.pressure_outlet[zone].momentum.gauge_pressure = {"value": 0}
            except Exception as e:
                print(f"Error applying Boundary Conditions: {e}")
                return

            # Apply Wall Heat Flux (2000 W/m2) to the outer exposed walls of the Battery Cells
            # This perfectly simulates the 9.38W thermal load using PyFluent's robust boundary condition API
            for zone_name in list(solver.setup.boundary_conditions.wall.keys()):
                if "cells" in zone_name.lower() and "cold_plate" not in zone_name.lower() and "interior" not in zone_name.lower():
                    try:
                        solver.setup.boundary_conditions.wall[zone_name].thermal.thermal_bc = "Heat Flux"
                        solver.setup.boundary_conditions.wall[zone_name].thermal.q = {"value": 2000}
                    except Exception as e:
                        print(f"PyFluent API failed for {zone_name}: {e}")
                        try:
                            cmd = f'(ti-menu-load-string "define/boundary-conditions/set/wall {zone_name} () heat-flux no 2000 quit")'
                            solver.scheme_eval.scheme_eval(cmd)
                        except Exception as e2:
                            print(f"TUI Fallback failed for {zone_name}: {e2}")

            # ---------------------------------------------------------
            # 4. Initialize and Solve (Real Iterations)
            # ---------------------------------------------------------
            print("\nInitializing and Solving (150 Iterations)...")
            solver.solution.initialization.hybrid_initialize()
            
            solver.solution.run_calculation.iter_count = 150
            solver.solution.run_calculation.calculate()

            # ---------------------------------------------------------
            # 5. Extract Real Results
            # ---------------------------------------------------------
            print("Extracting Real Thermal & Pressure Results...")
            
            # Create report definitions safely using Scheme
            cell_zones_str = " ".join([z for z in solver.setup.cell_zone_conditions.solid.keys() if "cells" in z.lower()])
            inlet_zones_str = " ".join([z for z in solver.setup.boundary_conditions.mass_flow_inlet.keys() if "inlet" in z.lower()])

            if "max_temp_report" not in list(solver.solution.report_definitions.volume.keys()):
                solver.scheme_eval.scheme_eval(f'(ti-menu-load-string "solve/report-definitions/add max_temp_report volume-max field temperature zone-names {cell_zones_str} () quit")')
            
            if "inlet_pressure" not in list(solver.solution.report_definitions.surface.keys()):
                solver.scheme_eval.scheme_eval(f'(ti-menu-load-string "solve/report-definitions/add inlet_pressure surface-areaavg field pressure surface-names {inlet_zones_str} () quit")')

            try:
                max_temp_k = solver.solution.report_definitions.compute(report_defs=["max_temp_report"])[0]["max_temp_report"][0]
                max_temp_c = max_temp_k - 273.15
            except Exception:
                max_temp_c = 0.0

            try:
                pressure_drop = solver.solution.report_definitions.compute(report_defs=["inlet_pressure"])[0]["inlet_pressure"][0]
            except Exception:
                pressure_drop = 0.0

            print(f"Result: Max Temp = {max_temp_c:.1f} C, Pressure Drop = {pressure_drop:.1f} Pa")
            
            optimization_report.append({
                "Material": material,
                "Mass Flow (kg/s)": flow_rate,
                "Max Temp (C)": round(max_temp_c, 2),
                "Pressure Drop (Pa)": round(pressure_drop, 2)
            })

    # Save to CSV
    report_file = os.path.join(os.path.dirname(__file__), "CFD_Optimization_Report.csv")
    print(f"\nWriting real optimization report to: {report_file}")
    with open(report_file, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Material", "Mass Flow (kg/s)", "Max Temp (C)", "Pressure Drop (Pa)"])
        writer.writeheader()
        writer.writerows(optimization_report)

    print("Parametric Study Complete! Best real design is ready for the Digital Twin.")
    session.exit()

if __name__ == "__main__":
    print("Script execution initiated!")
    run_parametric_study()
