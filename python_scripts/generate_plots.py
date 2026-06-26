import pandas as pd
import matplotlib.pyplot as plt
import os

# Paths
csv_path = "D:/MEK/The Digital Twins EV Battery/phase3_cfd_model/CFD_Optimization_Report.csv"
output_dir = "D:/MEK/The Digital Twins EV Battery/Production_Repository/cfd_results"

# Ensure output dir exists
os.makedirs(output_dir, exist_ok=True)

# Load data
df = pd.read_csv(csv_path)

# Separate by material
al_df = df[df['Material'] == 'aluminum']
cu_df = df[df['Material'] == 'copper']

# Plot 1: Temperature vs Mass Flow
plt.figure(figsize=(8, 6))
plt.plot(al_df['Mass Flow (kg/s)'], al_df['Max Temp (C)'], marker='o', label='Aluminum Cold Plate', color='#3498db', linewidth=2)
plt.plot(cu_df['Mass Flow (kg/s)'], cu_df['Max Temp (C)'], marker='s', label='Copper Cold Plate', color='#e67e22', linewidth=2)
plt.title('Max Cell Temperature vs. Coolant Mass Flow Rate', fontsize=14)
plt.xlabel('Mass Flow Rate (kg/s)', fontsize=12)
plt.ylabel('Max Cell Temperature (°C)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11)
plt.tight_layout()
temp_plot_path = os.path.join(output_dir, "temperature_plot.png")
plt.savefig(temp_plot_path, dpi=300)
print(f"Saved: {temp_plot_path}")
plt.close()

# Plot 2: Pressure Drop vs Mass Flow
plt.figure(figsize=(8, 6))
# Pressure drop is primarily geometric, so it's the same for both materials in this study,
# but we'll plot one to show the hydraulic curve.
plt.plot(cu_df['Mass Flow (kg/s)'], cu_df['Pressure Drop (Pa)'], marker='^', color='#9b59b6', linewidth=2)
plt.title('Manifold Pressure Drop vs. Coolant Mass Flow Rate', fontsize=14)
plt.xlabel('Mass Flow Rate (kg/s)', fontsize=12)
plt.ylabel('Pressure Drop (Pa)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
pressure_plot_path = os.path.join(output_dir, "pressure_drop_plot.png")
plt.savefig(pressure_plot_path, dpi=300)
print(f"Saved: {pressure_plot_path}")
plt.close()

print("All plots generated successfully.")
