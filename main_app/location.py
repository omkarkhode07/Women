import requests

city = ""
state = ""
lat = "28.6139"
log = "77.2090"

try:
    res = requests.get("https://ipinfo.io/", timeout=3)
    if res.status_code == 200:
        data = res.json()
        city = data.get("city", "")
        state = data.get("region", "")
        loc_coords = data.get("loc", "").split(",")
        if len(loc_coords) == 2:
            lat = loc_coords[0]
            log = loc_coords[1]
except Exception:
    pass
