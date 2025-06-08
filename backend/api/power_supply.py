import httpx
from backend.schemas.power import PowerStatus
from fastapi import APIRouter,HTTPException

power_router = APIRouter(tags=["Power"])

#taipower power supply open data api
@power_router.get("/power_supply", response_model=PowerStatus)
async def get_power_status():
    url = r"https://service.taipower.com.tw/data/opendata/apply/file/d006020/001.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            data = res.json()
        curr_load = float(data["records"][0]["curr_load"])
        sply_capacity = float(data["records"][3]["real_hr_maxi_sply_capacity"])
        reserve_w = sply_capacity - curr_load
        reserve_percent = (reserve_w / curr_load) * 100

        #determine indicator and rules with color change behined 
        if reserve_w < 50:
            indicator = "black"
        elif reserve_w < 90:
            indicator = "red"
        elif reserve_percent < 6:
            indicator = "orange"
        elif reserve_percent < 10:
            indicator = "yellow"
        else:
            indicator = "green"
        return PowerStatus(reserve_percent=round(reserve_percent,2),reserve_w=round(reserve_w,1),indicator=indicator)

    except httpx.ConnectTimeout:
        raise HTTPException(status_code=504, detail="Connect Timeout")

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP Error:{str(e)}")