import os
import urllib.error
import urllib.request

import environ

environ.Env.read_env(".env")
ua = os.environ.get("MAPS_USER_AGENT", "").strip() or "(empty)"
print("MAPS_USER_AGENT:", ua)


def call(name, url, data=None):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            print(name, "OK", response.status)
    except urllib.error.HTTPError as error:
        print(name, "FAIL HTTP", error.code, error.reason)
    except Exception as error:
        print(name, "FAIL", type(error).__name__, error)


call("nominatim", "https://nominatim.openstreetmap.org/search?format=json&limit=1&postalcode=110001&country=India")
call("overpass", "https://overpass-api.de/api/interpreter", b"data=[out:json];node(1);out;")