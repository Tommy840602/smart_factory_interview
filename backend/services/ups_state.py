import subprocess
import os
from backend.core.config import settings

def parse_upsc_output() -> dict:
    # 使用环境变量或配置中的路径，如果都没有则使用默认路径
    upsc_path = os.getenv('UPSC_PATH','/opt/homebrew/bin/upsc')
    try:
        result = subprocess.run([upsc_path, "dummy@127.0.0.1"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data
    except FileNotFoundError:
        # 如果找不到 upsc 命令，返回模拟数据
        return {
            "battery.charge": "100",
            "ups.status": "OL",
            "ups.load": "0",
            "battery.runtime": "3600"
        }

def get_light_color(status: str, battery_charge: int) -> str:
    if battery_charge <= 20:
        return "red"
    if "LB" in status or "OVER" in status or "FSD" in status:
        return "red"
    elif "OB" in status or "DISCHRG" in status:
        return "yellow"
    elif "OL" in status or "CHRG" in status:
        return "green"
    else:
        return "green"