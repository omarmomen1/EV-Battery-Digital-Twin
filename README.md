# Physics-Informed Digital Twin for EV Battery Modules
**Bridging High-Fidelity CHT Simulation with a Live IoT Battery Management System**

> **Author**: Omar Momen  
> **Discipline**: Mechanical Engineering + Embedded Software Systems  
> **Tools**: Ansys Fluent 24.1 · PyFluent · CadQuery · Python · MQTT · InfluxDB · Grafana  

A full-stack, software-defined Digital Twin of a high-performance Electric Vehicle Battery Thermal Management System (BTMS). This project integrates parametric 3D CAD generation, automated Computational Fluid Dynamics (CFD), and a real-time IoT Telemetry pipeline with anomaly detection.

---

## 1. The Validated Prototype (Current State)

The foundation of this Digital Twin is built on a fully validated, physics-grounded prototype. 

* **Physical Model**: A 4-cell liquid-cooled cold plate architecture.
* **CFD Validation**: 6 distinct Conjugate Heat Transfer (CHT) design points were solved using the k-ω SST turbulence model in Ansys Fluent. The simulation achieved convergence and verified the pressure drop ($\Delta P$) and peak temperatures across multiple coolant mass flow rates.
* **Telemetry Anchor**: The Python IoT simulator (`telemetry_simulator.py`) is directly anchored to this validated CFD data. Using Newton's Law of Cooling and NumPy interpolation, the simulated sensors react with the exact thermal mass and steady-state boundaries derived from the Ansys solver.
* **BMS Safety Layer**: A dedicated microservice evaluates the first temporal derivative ($dT/dt$) of the MQTT telemetry stream, distinguishing benign thermal plateaus from early-stage thermal runaway precursors (<3 second detection latency).

---

## 2. Next-Generation Architecture (Ongoing Work)

To scale the prototype into a production-grade architecture, I have engineered a next-generation immersion cooling module and closed-loop software pipeline. This architecture is currently in active development.

* **Procedural Honeycomb Geometry**: Utilizing Python's `CadQuery`, the CAD model has been upgraded to a **40-cell (4x10) staggered honeycomb manifold** optimized for direct dielectric fluid immersion.
* **CFD Automation**: A headless PyFluent script was written to completely automate the meshing and solving of the 40-cell manifold. 
* **Closed-Loop BMS Feedback**: The IoT architecture has been upgraded to support closed-loop actuation. The telemetry simulator now intercepts `CRITICAL` anomaly alerts via MQTT callbacks to automatically override vehicle throttle (Limp Mode) and command maximum coolant pump RPM.

---

## 3. Engineering Limitations & Assessment

As an engineer, distinguishing between validated results and simulated assumptions is critical. Understanding where this model breaks down is essential for scaling to production.

### Physics & Thermal Limitations
* **Isothermal Flow in 40-Cell Simulation**: While the automated PyFluent script successfully generates a 3D volume mesh and converges the Navier-Stokes equations for the 40-cell honeycomb, the Ansys Python API currently throws a silent dictionary key error when mapping the volumetric heat source to the parametrically generated cell zones. As a result, the current 40-cell solution is isothermal. Extracting validated thermal gradients requires manually updating the source-term coupling in the Fluent GUI.
* **Uniform Volumetric Heat Generation**: The uniform $150,000 \, W/m^3$ heat generation assumption used in the validated 4-cell model underestimates peak generation at high discharge rates, where internal resistance spikes. Furthermore, it ignores electrochemical non-uniformity—real heat generation is highest at the current collectors. 
* **Constant Fluid Properties**: The dielectric coolant properties are treated as constant. In reality, viscosity changes meaningfully between 25°C and 60°C, which alters both the local heat transfer coefficient and the hydraulic pressure drop.

### Software & Systems Limitations
* **Simulated Closed-Loop Actuation**: The closed-loop BMS feedback currently acts upon its own simulated parameters. While the pub/sub software architecture is sound, calling this a "True Closed-Loop System" requires integration with a physical actuator (Hardware-in-the-Loop) or a coupled 1D-system solver to confirm the physical hydraulic response of the pump.
* **Threshold Calibration**: The $dT/dt$ alert thresholds (0.5°C/s and 1.2°C/s) were calibrated against synthetic fault injections. In a production environment, these thresholds must be derived directly from Accelerating Rate Calorimetry (ARC) test data on the specific 21700 cell chemistry.

---

## 4. Future Work Roadmap

1. **Electrochemical Coupling**: Replace the uniform heat flux boundary condition with a Newman P2D (pseudo-two-dimensional) electrochemical model.
2. **PyFluent API Resolution**: Resolve the dynamic source-term dictionary mapping in the PyFluent 24.1 script to fully automate the 40-cell thermal solve.
3. **Hardware-in-the-Loop (HIL) Calibration**: Measure the true thermal time constant of a physical 21700 cell using a thermocouple array, and use the empirical data to calibrate the simulator's $\alpha$ parameter.
