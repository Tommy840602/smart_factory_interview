# Re-run after reset: generate ZIP with formatted dataset
import pandas as pd
import numpy as np
import zipfile
import os

rows_per_file = 1130000*2

def generate_robotic_arm_data(rows):
    def rand_list(n): return "[" + ", ".join(f"{x:.8f}" for x in np.random.uniform(-5, 5, n)) + "]"
    def rand_joint_angles(): return "[" + ", ".join(f"{x:.15f}" for x in np.random.uniform(-5, 5, 6)) + "]"
    def rand_temp(): return "[" + ", ".join(f"{np.random.uniform(30, 80):.4f}" for _ in range(6)) + "]"
    def rand_coords(): return "[" + ", ".join(f"{np.random.uniform(-1, 1):.15f}" for _ in range(3)) + "]"
    def rand_voltage(): return "[" + ", ".join(f"{np.random.uniform(24, 48):.4f}" for _ in range(6)) + "]"
    def rand_force(): return "[" + ", ".join(f"{np.random.uniform(-10, 10):.4f}" for _ in range(6)) + "]"

    data = {
        "Timestamp": np.round(257250.0 + np.arange(rows) * 0.05, 2),
        "Actual Joint Positions": [rand_joint_angles() for _ in range(rows)],
        "Actual Joint Velocities": [rand_list(6) for _ in range(rows)],
        "Actual Joint Currents": [rand_list(6) for _ in range(rows)],
        "Actual Cartesian Coordinates": [rand_list(6) for _ in range(rows)],
        "Actual Tool Speed": [rand_list(6) for _ in range(rows)],
        "Generalized Forces": [rand_force() for _ in range(rows)],
        "Temperature of Each Joint": [rand_temp() for _ in range(rows)],
        "Execution Time": np.round(np.random.uniform(0.01, 1.5, rows), 6),
        "Safety Status": np.random.choice([0, 1, 2], rows),
        "Tool Acceleration": [rand_coords() for _ in range(rows)],
        "Norm of Cartesion Linear Momentum": np.round(np.random.uniform(0, 5, rows), 8),
        "Robot Current": np.round(np.random.uniform(0, 15, rows), 8),
        "Joint Voltages": [rand_voltage() for _ in range(rows)],
        "Elbow Position": [rand_coords() for _ in range(rows)],
        "Elbow Velocity": [rand_coords() for _ in range(rows)],
        "Tool Current": np.round(np.random.uniform(0, 5, rows), 8),
        "Tool Temperature": np.round(np.random.uniform(30, 90, rows), 4),
        "TCP Force": np.round(np.random.uniform(0, 15, rows), 8),
        "Anomaly State": np.random.choice([0, 1], rows)
    }
    return pd.DataFrame(data)

# Save to CSV and zip
file_paths = []
for i in range(1, 4):
    df = generate_robotic_arm_data(rows_per_file)
    path = f"robot_{i}_left_arm.csv"
    df.to_csv(path, index=False)
    file_paths.append(path)

# Compress into a zip
zip_path = "robotic_left_arm_dataset.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in file_paths:
        zipf.write(file, os.path.basename(file))


