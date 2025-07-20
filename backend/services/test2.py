# Re-run after reset: Generate 3 simulated robot_{i}_left_arm.csv files based on right_arm.csv format
import pandas as pd
import numpy as np
import zipfile
import os

rows = 1120000
start_timestamp = 257258.126
time_step = 0.05

def generate_simulated_row(i):
    ts = round(start_timestamp + i * time_step, 3)
    return {
        "Timestamp": ts,
        "Actual Joint Positions": str(list(np.round(np.random.uniform(-1.58, -1.56, 6), 15))),
        "Actual Joint Velocities": str(list(np.round(np.random.uniform(-0.1, 0.1, 6), 8))),
        "Actual Joint Currents": str(list(np.round(np.random.uniform(-0.2, 1.5, 6), 8))),
        "Actual Cartesian Coordinates": str(list(np.round(np.random.uniform(-1.3, 1.3, 6), 15))),
        "Actual Tool Speed": str(list(np.round(np.random.uniform(-0.05, 0.05, 6), 15))),
        "Generalized Forces": str(list(np.round(np.random.uniform(-1.5, 1.5, 6), 15))),
        "Temperature of Each Joint": str(list(np.random.choice([34.375, 36.875, 39.6875, 42.8125, 45.0, 45.3125], 6))),
        "Execution Time": round(np.random.uniform(0.8, 1.2), 6),
        "Safety Status": 1,
        "Tool Acceleration": str(list(np.round(np.random.uniform(-9.5, 0.5, 3), 15))),
        "Norm of Cartesion Linear Momentum": round(np.random.uniform(0.3, 0.7), 9),
        "Robot Current": round(np.random.uniform(0.4, 0.6), 9),
        "Joint Voltages": str(list(np.round(np.random.uniform(47.3, 47.7, 6), 6))),
        "Elbow Position": str(list(np.round(np.random.uniform(-0.08, 0.4, 3), 15))),
        "Elbow Velocity": str(list(np.round(np.random.uniform(0.0, 0.1, 3), 6))),
        "Tool Current": round(np.random.uniform(0.06, 0.12), 8),
        "Tool Temperature": round(np.random.uniform(39.5, 39.8), 4),
        "TCP Force": round(np.random.uniform(0.5, 1.5), 9),
        "Anomaly State": 0
    }

# Generate and save 3 CSV files
file_paths = []
for i in range(1, 4):
    df = pd.DataFrame([generate_simulated_row(j) for j in range(rows)])
    path = f"robot_{i}_right_arm.csv"
    df.to_csv(path, index=False)
    file_paths.append(path)    



# Compress into a zip
zip_path = "robotic_right_arm_dataset.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in file_paths:
        zipf.write(file, os.path.basename(file))