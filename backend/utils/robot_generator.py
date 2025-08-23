# generator.py
import numpy as np
from datetime import datetime

# generator.py
import numpy as np
from datetime import datetime

def generate_record(ts: datetime) -> dict:
    # 所有數值維持為數字/陣列，不轉成字串，方便後端解析
    def rands(n, lo, hi, fmt=None):
        vals = np.random.uniform(lo, hi, n)
        if fmt:
            return [float(format(x, fmt)) for x in vals]
        return vals.tolist()

    def rand_list6():       return rands(6, -5, 5, ".8f")
    def rand_joint_angles():return rands(6, -5, 5, ".15f")
    def rand_temp6():       return rands(6, 30, 80, ".4f")
    def rand_coords3():     return rands(3, -1, 1, ".15f")
    def rand_voltage6():    return rands(6, 24, 48, ".4f")
    def rand_force6():      return rands(6, -10, 10, ".4f")

    return {
        "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),     # Asia/Taipei 由呼叫端決定
        "Actual Joint Positions": rand_joint_angles(),
        "Actual Joint Velocities": rand_list6(),
        "Actual Joint Currents":   rand_list6(),
        "Actual Cartesian Coordinates": rand_list6(),
        "Actual Tool Speed":       rand_list6(),
        "Generalized Forces":      rand_force6(),
        "Temperature of Each Joint": rand_temp6(),
        "Execution Time": float(format(np.random.uniform(0.01, 1.5), ".6f")),
        "Safety Status": int(np.random.choice([0, 1, 2])),
        "Tool Acceleration": rand_coords3(),
        "Norm of Cartesian Linear Momentum": float(format(np.random.uniform(0, 5), ".8f")),
        "Robot Current": float(format(np.random.uniform(0, 15), ".8f")),
        "Joint Voltages": rand_voltage6(),
        "Elbow Position": rand_coords3(),
        "Elbow Velocity": rand_coords3(),
        "Tool Current": float(format(np.random.uniform(0, 5), ".8f")),
        "Tool Temperature": float(format(np.random.uniform(30, 90), ".4f")),
        "TCP Force": float(format(np.random.uniform(0, 15), ".8f")),
        "Anomaly State": int(np.random.choice([0, 1])),
    }


def generate_nicla_record(ts: datetime) -> dict:
    # 你的 Nicla 規格（單筆，即時）
    def r(lo, hi, fmt=".5f"): return float(format(np.random.uniform(lo, hi), fmt))
    def rc(choices): return float(format(np.random.choice(choices), ".5f"))

    return {
        "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "AccX":  r(-9.74, -9.68),
        "AccY":  r(-0.06, 0.06),
        "AccZ":  r(0.84, 0.92),
        "GyroX": rc([0.0, 0.0625, -0.0625, 0.125, -0.125, 0.1875, -0.1875]),
        "GyroY": rc([0.0, 0.0625, -0.0625]),
        "GyroZ": rc([0.0, 0.0625, -0.0625, 0.125, -0.125]),
        "MagX":  float(format(np.random.uniform(32.96, 33.44), ".2f")),
        "MagY":  float(format(np.random.uniform(-30.84, -30.48), ".2f")),
        "MagZ":  float(format(np.random.uniform(6.23, 7.08), ".5f")),
    }
