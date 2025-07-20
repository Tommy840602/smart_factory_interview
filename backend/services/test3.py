# Re-run after reset: Generate nicla_{i}.csv files
import pandas as pd
import numpy as np
import zipfile
import os

rows=900000*2
# 模擬 nicla sensor data 生成函數
def generate_nicla_data(rows):
    return pd.DataFrame({
        "AccX": np.round(np.random.uniform(-9.74, -9.68, rows), 5),
        "AccY": np.round(np.random.uniform(-0.06, 0.06, rows), 5),
        "AccZ": np.round(np.random.uniform(0.84, 0.92, rows), 5),
        "GyroX": np.round(np.random.choice([0.0, 0.0625, -0.0625, 0.125, -0.125, 0.1875, -0.1875], size=rows), 5),
        "GyroY": np.round(np.random.choice([0.0, 0.0625, -0.0625], size=rows), 5),
        "GyroZ": np.round(np.random.choice([0.0, 0.0625, -0.0625, 0.125, -0.125], size=rows), 5),
        "MagX": np.round(np.random.uniform(32.96, 33.44, rows), 2),
        "MagY": np.round(np.random.uniform(-30.84, -30.48, rows), 2),
        "MagZ": np.round(np.random.uniform(6.23, 7.08, rows), 5)
    })

# 產出 3 組 nicla_{i}.csv
file_paths = []
for i in range(1, 4):
    df = generate_nicla_data(rows)
    path = f"nicla_{i}.csv"
    df.to_csv(path, index=False)
    file_paths.append(path)

# Compress into a zip
zip_path = "robotic_nicla_dataset.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in file_paths:
        zipf.write(file, os.path.basename(file))