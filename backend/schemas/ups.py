from pydantic import BaseModel

class UPSStatus(BaseModel):
    battery_charge: int
    battery_runtime: int
    ups_status: str
    ups_load: int
    input_voltage: int
    output_voltage: int
    light: str