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

# Define Stunning Dark Mode Aesthetic
bg_color = '#0B0F19'  # Deep space dark blue
grid_color = '#1E293B'
text_color = '#E2E8F0'
cyan_neon = '#00f0ff'
orange_neon = '#ffaa00'
purple_neon = '#b5179e'

plt.rcParams.update({
    'axes.facecolor': bg_color,
    'figure.facecolor': bg_color,
    'text.color': text_color,
    'axes.labelcolor': text_color,
    'xtick.color': text_color,
    'ytick.color': text_color,
    'axes.edgecolor': grid_color,
    'font.family': 'sans-serif',
    'font.weight': 'medium'
})

# Plot 1: Temperature vs Mass Flow
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(al_df['Mass Flow (kg/s)'], al_df['Max Temp (C)'], marker='o', markersize=8, label='Aluminum Cold Plate', color=cyan_neon, linewidth=3, zorder=3)
ax.plot(cu_df['Mass Flow (kg/s)'], cu_df['Max Temp (C)'], marker='s', markersize=8, label='Copper Cold Plate', color=orange_neon, linewidth=3, zorder=3)

# Glow effect
ax.plot(al_df['Mass Flow (kg/s)'], al_df['Max Temp (C)'], color=cyan_neon, linewidth=8, alpha=0.2, zorder=2)
ax.plot(cu_df['Mass Flow (kg/s)'], cu_df['Max Temp (C)'], color=orange_neon, linewidth=8, alpha=0.2, zorder=2)

ax.set_title('Max Cell Temperature vs. Coolant Mass Flow Rate', fontsize=16, pad=20, fontweight='bold')
ax.set_xlabel('Mass Flow Rate (kg/s)', fontsize=12, labelpad=10)
ax.set_ylabel('Maximum Temperature (°C)', fontsize=12, labelpad=10)
ax.grid(True, linestyle='-', color=grid_color, linewidth=1, zorder=1)

# Style the legend
legend = ax.legend(fontsize=11, facecolor=bg_color, edgecolor=grid_color, framealpha=0.9)
for text in legend.get_texts():
    text.set_color(text_color)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
temp_plot_path = os.path.join(output_dir, "temperature_plot.png")
plt.savefig(temp_plot_path, dpi=300, facecolor=bg_color, edgecolor='none')
print(f"Saved: {temp_plot_path}")
plt.close()

# Plot 2: Pressure Drop vs Mass Flow
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(cu_df['Mass Flow (kg/s)'], cu_df['Pressure Drop (Pa)'], marker='^', markersize=8, color=purple_neon, linewidth=3, zorder=3)

# Glow effect
ax.plot(cu_df['Mass Flow (kg/s)'], cu_df['Pressure Drop (Pa)'], color=purple_neon, linewidth=8, alpha=0.2, zorder=2)

ax.set_title('Manifold Pressure Drop vs. Mass Flow Rate', fontsize=16, pad=20, fontweight='bold')
ax.set_xlabel('Mass Flow Rate (kg/s)', fontsize=12, labelpad=10)
ax.set_ylabel('Pressure Drop (Pa)', fontsize=12, labelpad=10)
ax.grid(True, linestyle='-', color=grid_color, linewidth=1, zorder=1)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
pressure_plot_path = os.path.join(output_dir, "pressure_drop_plot.png")
plt.savefig(pressure_plot_path, dpi=300, facecolor=bg_color, edgecolor='none')
print(f"Saved: {pressure_plot_path}")
plt.close()

print("All stunning plots generated successfully.")
