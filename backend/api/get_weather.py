from backend.services.ups_state import parse_upsc_output,get_light_color
from backend.schemas.location import Location
from fastapi import APIRouter,Depends
from redis.asyncio import Redis
from backend.api.deps import get_redis
import json,httpx,redis,datetime,urllib
from backend.services.nearest_station import haversine

weather_router = APIRouter(tags=["Weather"])


@weather_router.post("/gps_location")
async def receive_location(location: Location,redis: Redis = Depends(get_redis)):
    await redis.set("gps", json.dumps({"lon": location.lon,"lat": location.lat}), ex=60)
    return {"status": "Location Received","lon": location.lon,"lat": location.lat}


@weather_router.post("/weather")
async def get_nearest_station(location: Location,redis: Redis = Depends(get_redis)):
    gps_value = await redis.get("gps")
    gps_data = json.loads(gps_value)
    lat,lon = gps_data["lat"],gps_data["lon"]
    url = r"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-88D62B68-5C16-456B-8D80-E11CAD258497"
    try:
        async with httpx.AsyncClient(timeout=10.0,verify=False) as client:
            res = await client.get(url)
            data = res.json()

        stations = data['records']['Station']

        def get_wgs84_coords(st):
            for coord in st['GeoInfo']['Coordinates']:
                if coord['CoordinateName'] == 'WGS84':
                    return float(coord['StationLongitude']), float(coord['StationLatitude'])
            return None, None

        nearest = min(stations,key=lambda st: haversine(lon, lat,*get_wgs84_coords(st)))
        nearest_lon, nearest_lat = get_wgs84_coords(nearest)
        distance = haversine(lon, lat, nearest_lon, nearest_lat)
        await redis.set("country", json.dumps({"CountyName":nearest["GeoInfo"]["CountyName"]}),ex=60)
      
        return {
            "stationId": nearest["StationId"],"stationName": nearest["StationName"],"CountyName":nearest["GeoInfo"]["CountyName"],
            "lat": nearest_lat,"lon": nearest_lon,
            "distance_km": round(distance,2),"weather": nearest["WeatherElement"]
            }

    except Exception as e:
        return {"Error": f"Unable to connect to CWB API: {str(e)}"}

@weather_router.post("/suntime")
async def get_suntime(redis: Redis = Depends(get_redis)):
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    coutryname_value = await redis.get("country")
    
    if coutryname_value is None:
        return {"Error": "No location data available. Please set location first using /weather endpoint."}
        
    try:
        coutryname_data = json.loads(coutryname_value)
        coutryname = coutryname_data["CountyName"]
    except (json.JSONDecodeError, KeyError) as e:
        return {"Error": f"Invalid location data format: {str(e)}"}
        
    url = r"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization=CWA-88D62B68-5C16-456B-8D80-E11CAD258497&format=JSON&CountyName={0}&Date={1}".format(urllib.parse.quote(coutryname), now)
    
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            res = await client.get(url)
            data = res.json()
            
        locations = data.get("records", {}).get("locations", {}).get("location", [])
        if not locations:
            return {"Error": "No suntime data found"}

        location = locations[0]
        time_info = location.get("time", [])
        if not time_info:
            return {"Error": "No time data in location"}

        time_data = time_info[0]

        return {
            "CountyName": location.get("CountyName"),
            "Date": time_data.get("Date"),
            "SunRiseTime": time_data.get("SunRiseTime"),
            "SunSetTime": time_data.get("SunSetTime"),
        }

    except Exception as e:
        return {"Error": f"Unable to connect to CWB API: {str(e)}"}
