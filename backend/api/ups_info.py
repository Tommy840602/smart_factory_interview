from backend.schemas.ups import UPSStatus
from fastapi import APIRouter
from backend.services.ups_state import parse_upsc_output,get_light_color

ups_router = APIRouter(tags=["UPS"])

@ups_router.get("/ups")
async def get_ups_status():
    ups_data = parse_upsc_output()
    battery_charge = int(ups_data.get("battery.charge", "0"))
    battery_runtime = int(ups_data.get("battery.runtime", "0"))
    ups_status = ups_data.get("ups.status", "UNKNOWN")
    ups_load = int(ups_data.get("ups.load", "0"))
    input_voltage = int(ups_data.get("input.voltage", "0"))
    output_voltage = int(ups_data.get("output.voltage", "0"))

    light = get_light_color(ups_status, battery_charge)

    return UPSStatus(
        battery_charge=battery_charge,
        battery_runtime=battery_runtime,
        ups_status=ups_status,
        ups_load=ups_load,
        input_voltage=input_voltage,
        output_voltage=output_voltage,
        light=light
    )