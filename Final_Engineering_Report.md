# Final Engineering Report: Physics-Informed Digital Twin for EV Battery Modules

**Author**: Omar Momen  
**Project Date**: June 2026  
**Objective**: End-to-end development of an EV Battery Thermal Management System (BTMS) Digital Twin, coupling physical Conjugate Heat Transfer (CHT) simulations with an embedded IoT telemetry and Battery Management System (BMS) safety layer.

---

## 1. Executive Summary
This project bridges the gap between mechanical simulation and software-driven systems engineering. A full-stack Digital Twin was developed to monitor and predict thermal runaway precursors in high-performance cylindrical 21700 lithium-ion battery modules. 

Unlike traditional open-loop simulations or pure software telemetry generators, this architecture is **physics-informed**. Validated steady-state thermal gradients and pressure drops from Ansys Fluent CHT simulations act as the absolute boundary conditions for a live Python telemetry simulator. The simulated sensors dynamically obey Newton's Law of Cooling, providing a mathematically robust data stream to an InfluxDB/Grafana pipeline and a closed-loop BMS anomaly detection algorithm.

---

## 2. Phase 1: Procedural CAD Generation
The physical architecture of the battery module was defined programmatically using **CadQuery**, a Python-based parametric CAD kernel.
* **Validated Prototype**: A 4-cell liquid-cooled cold plate array.
* **Next-Generation Architecture**: A 40-cell (4x10) staggered honeycomb manifold optimized for direct dielectric fluid immersion cooling.

By defining geometry as code, the system allows for rapid, automated design iterations without manual GUI interaction.
> **Deliverable**: `python_scripts/generate_btms_cad.py` and resulting `.STEP` files.

---

## 3. Phase 2: Conjugate Heat Transfer (CHT) CFD Simulation
A headless **Ansys PyFluent** automation script was developed to mesh and solve the fluid-solid thermal interactions.
* **Solver**: Ansys Fluent 24.1 (k-ω SST turbulence model).
* **Boundary Conditions**: 150,000 W/m³ volumetric heat generation applied to cell solids, simulating 2C/3C aggressive discharge rates.
* **Optimization Study**: A parametric sweep was conducted across multiple mass flow rates (0.05 kg/s to 0.20 kg/s) for both Aluminum and Copper cold plate configurations.

**Key Findings**:
* Copper cold plates provided an optimal operating point at 0.10 kg/s, yielding a peak cell temperature of 31.67°C with a manageable pressure drop of 126.29 Pa.
* The computational results were automatically parsed into `CFD_Optimization_Report.csv` to act as the ground-truth anchor for the software pipeline.

> **Deliverables**: 
> - `python_scripts/run_cfd_automation.py`
> - `cfd_outputs/temperature_contour.png`
> - `cfd_results/temperature_plot.png` & `cfd_results/pressure_drop_plot.png`

---

## 4. Phase 3: Physics-Informed IoT Telemetry Simulation
To emulate live vehicle telemetry, a Python script (`telemetry_simulator.py`) was developed to broadcast MQTT sensor data at 1 Hz. 
* **Dynamic Loading**: A sinusoidal function mimics driver throttle behavior, proportionally scaling the coolant pump mass flow rate.
* **Physics Interpolation**: The script uses NumPy to interpolate the exact maximum steady-state temperature limit from the CFD CSV report based on the instantaneous flow rate.
* **Thermal Mass (Newton's Law of Cooling)**: A discrete-time mathematical model prevents instant temperature jumps, applying a realistic thermal response coefficient to smoothly approach the CFD-defined boundary limits.
* **Fault Injection**: An artificial +15°C thermal spike is periodically injected to simulate an internal hardware short-circuit (thermal runaway precursor).

> **Deliverable**: `python_scripts/telemetry_simulator.py`

---

## 5. Phase 4: BMS Safety Layer & Data Engineering
A dedicated Battery Management System microservice monitors the MQTT stream. 
* **Calculus-Based Anomaly Detection**: Instead of relying on static absolute temperature thresholds (which cannot distinguish between a stable high-load cruise and an escalating runaway event), the BMS computes the first temporal derivative ($dT/dt$) over a sliding deque window.
* **Closed-Loop Actuation**: Upon detecting a $dT/dt > 1.2$ °C/s, the BMS triggers a `CRITICAL_ANOMALY` alert. The telemetry simulator intercepts this callback, cuts the throttle to 10% (Limp Mode), and commands maximum coolant flow, actively averting catastrophic failure.
* **Time-Series Storage**: An `mqtt_to_influx.py` bridge ingests all payloads into **InfluxDB v2**, visualizing live thermal traces and fault events in **Grafana**.

> **Deliverables**: 
> - `python_scripts/thermal_anomaly_detector.py`
> - `dashboard_config/grafana_dashboard.json`

---

## 6. Engineering Assessment & Future Work
While the open-loop 4-cell physics are fully validated, scaling to the 40-cell honeycomb architecture revealed strict API limitations within PyFluent 24.1 regarding dynamic volumetric source term mapping. 
Future iterations will focus on:
1. Resolving the PyFluent dictionary mapping to achieve a non-isothermal, fully coupled 40-cell mesh.
2. Replacing the uniform volumetric heat generation with a Newman P2D electrochemical coupling.
3. Integrating a physical Hardware-in-the-Loop (HIL) actuator to replace the simulated closed-loop feedback mechanism.

---
**Repository**: [EV-Battery-Digital-Twin](https://github.com/omarmomen1/EV-Battery-Digital-Twin)  
*All scripts, CAD outputs, CFD data, and dashboards are version-controlled and available in the repository.*
