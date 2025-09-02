# backend/api/weather.py
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from backend.api.deps import get_redis
from backend.schemas.location import Location
from backend.services.nearest_station import haversine
from backend.services.crawler_telegram import crawl_telegram
import json, httpx, datetime, urllib

weather_router = APIRouter(tags=["Weather"])

# ===== 接收 GPS 座標 =====
@weather_router.post("/gps_location")
async def receive_location(location: Location, redis: Redis = Depends(get_redis)):
    gps = {"lon": location.lon, "lat": location.lat}
    await redis.set("gps", json.dumps(gps), ex=3600)

    # ===== 最近測站 API =====
    url_station = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-88D62B68-5C16-456B-8D80-E11CAD258497"
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            res_station = await client.get(url_station)
            data_station = res_station.json()
        stations = data_station['records']['Station']

        def get_wgs84_coords(st):
            for coord in st['GeoInfo']['Coordinates']:
                if coord['CoordinateName'] == 'WGS84':
                    return float(coord['StationLongitude']), float(coord['StationLatitude'])
            return None, None

        nearest = min(stations, key=lambda st: haversine(location.lon, location.lat, *get_wgs84_coords(st)))
        county = nearest["GeoInfo"]["CountyName"]

        # 存 county 到 Redis（給 earthquake 用）
        await redis.set("country", json.dumps({"CountyName": county}), ex=3600)

        # ===== 日出日落 API =====
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        url_suntime = (
            "https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001"
            f"?Authorization=CWA-88D62B68-5C16-456B-8D80-E11CAD258497"
            f"&format=JSON&CountyName={urllib.parse.quote(county)}&Date={today}"
        )

        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            res_suntime = await client.get(url_suntime)
            data_suntime = res_suntime.json()

        locations = data_suntime.get("records", {}).get("locations", {}).get("location", [])
        suntime_data = {}
        if locations:
            time_info = locations[0].get("time", [])
            if time_info:
                suntime_data = {
                    "Date": time_info[0].get("Date"),
                    "SunRiseTime": time_info[0].get("SunRiseTime"),
                    "SunSetTime": time_info[0].get("SunSetTime"),
                }

        # ===== 最終整合回傳 =====
        return {
            "status": "Location Received",
            "lat": location.lat,
            "lon": location.lon,
            "station": {
                "stationId": nearest["StationId"],
                "stationName": nearest["StationName"],
                "CountyName": county,
                "weather": nearest["WeatherElement"]
            },
            "suntime": suntime_data
        }

    except Exception as e:
        return {"Error": f"Unable to connect to CWB API: {str(e)}"}


# ===== 抓取 Telegram 地震訊息 =====
@weather_router.api_route("/earthquake", methods=["GET", "POST"])
async def get_telegram_messages(redis: Redis = Depends(get_redis)):
    result = await crawl_telegram(redis)
    return result

