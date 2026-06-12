# Tesla-Architecture EV Battery Digital Twin

A full-stack, software-defined Digital Twin of a high-performance Electric Vehicle Battery Thermal Management System (BTMS). This project integrates procedural 3D CAD generation, automated Computational Fluid Dynamics (CFD), and a real-time IoT Telemetry pipeline with anomaly detection.

## Project Architecture

1. **Procedural Geometry**: A Python `CadQuery` script generates a pristine, Tesla-style 4x10 staggered honeycomb array of 21700 cells enclosed in a custom cross-flow manifold. 
2. **CFD Automation**: A headless PyFluent script automates the meshing, applies dielectric fluid properties and 18650/21700 volumetric heat generation, and extracts the steady-state thermal gradient data.
3. **IoT Pipeline**: A Python simulator broadcasts synthetic real-time telemetry (anchored to the CFD thermal data) over an MQTT broker. A bridge script ingests this into an InfluxDB time-series database.
4. **Live Anomaly Detection**: A continuous background script monitors the `dT/dt` rates to detect thermal runaway precursors before catastrophic failure.

---

## Engineering Limitations & Assessment

As a simulation-driven model, this Digital Twin relies on several critical boundary conditions and simplifications. Understanding where these assumptions break down is essential for scaling this architecture to production.

### Physics & Thermal Limitations
- **Uniform Volumetric Heat Generation**: The uniform $150,000 \, W/m^3$ heat generation assumption is conservative at low SOC, but underestimates peak generation at high discharge rates, where internal resistance spikes as the cell approaches cutoff voltage. Furthermore, it ignores electrochemical non-uniformity—real heat generation is highest at the current collectors and drops axially. The model currently treats the cell as a uniform heater rather than a dynamic electrochemical battery. This means the CFD steady-state temperatures are likely optimistic by 3–6°C under real fast-charge conditions.
- **Constant Fluid Properties**: The dielectric coolant properties (viscosity and specific heat) are currently treated as constant. In reality, these properties change meaningfully between 25°C and 60°C, which significantly alters both the local heat transfer coefficient and the pressure drop across the staggered honeycomb array.
- **Steady-State CFD vs. Transient Reality**: The steady-state CFD captures the thermal limit, but misses transient thermal events (e.g., a 10-second full-throttle burst from cold). The Digital Twin's Newton's Law of Cooling simulator partially compensates for this, but the thermal time constant ($\alpha$) was tuned heuristically rather than derived from a physically measured time constant.

### Software & Systems Limitations
- **Open-Loop Telemetry**: The current IoT architecture is open-loop. While the Python Anomaly Detector successfully flags thermal runaway precursors, the BMS output does not modify the simulator's next time step. A true digital twin must close the loop: utilizing the anomaly detection result to throttle the simulated vehicle load or ramp up the coolant pump RPM.
- **Threshold Calibration**: The $dT/dt$ alert thresholds (0.5°C/s and 1.2°C/s) were calibrated against synthetic fault injections. In a production environment, these thresholds must be derived directly from Accelerating Rate Calorimetry (ARC) test data on the specific 21700 cell chemistry.
- **Module vs. Pack Scaling**: This model is scoped to a single 40-cell module. Scaling to a full 4,000+ cell pack introduces massive thermal gradients between modules, coolant temperature rise along the main manifold, and pack-level current balancing effects that invalidate single-module boundary conditions.

---

## Future Work & Next Iterations

To bridge the gap between this prototype and a production-grade BMS simulator, the following iterations are proposed:
1. **Electrochemical Coupling**: Replace the uniform heat flux boundary condition with a Newman P2D (pseudo-two-dimensional) electrochemical model to provide spatially and temporally resolved heat generation mapping.
2. **Hardware-in-the-Loop (HIL) Calibration**: Measure the true thermal time constant of a physical 21700 cell using a thermocouple array, and use the empirical data to calibrate the simulator's $\alpha$ parameter.
3. **Closed-Loop Control Logic**: Implement a feedback mechanism where the BMS output dynamically alters the coolant flow rate setpoint, feeding back into a multidimensional CFD interpolation table.
4. **1D-3D Co-Simulation**: Extend the architecture to a full pack by modeling the global manifold temperature rise as a 1D thermal-fluid network, using the 3D CFD module data as local node inputs.
