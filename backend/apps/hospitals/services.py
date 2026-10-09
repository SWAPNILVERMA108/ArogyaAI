import hashlib
import json
import math
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

from common.exceptions.api import ServiceUnavailable


DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DEFAULT_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_RESULTS = 100
GEOCODE_CACHE_SECONDS = 24 * 60 * 60
FACILITY_CACHE_SECONDS = 5 * 60
NOMINATIM_LOCK_KEY = "hospitals:nominatim:request-lock"
NOMINATIM_LAST_REQUEST_KEY = "hospitals:nominatim:last-request"


class HospitalFinderService:
    @classmethod
    def search(cls, *, latitude, longitude, radius, category=None):
        query = cls._build_overpass_query(latitude, longitude, radius)
        endpoint = os.environ.get("OVERPASS_API_URL", DEFAULT_OVERPASS_URL)
        cache_key = "hospitals:overpass:" + hashlib.sha256(
            f"{endpoint}|{query}".encode("utf-8")
        ).hexdigest()
        raw = cache.get(cache_key)
        if raw is None:
            raw = cls._request_json(
                endpoint,
                urlencode({"data": query}).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            cache.set(cache_key, raw, FACILITY_CACHE_SECONDS)
        elements = raw.get("elements")
        if not isinstance(elements, list):
            raise ServiceUnavailable("The map search service returned an invalid response.")

        facilities = []
        seen = set()
        for element in elements:
            if not isinstance(element, dict):
                continue
            facility = cls._normalize_element(element, latitude, longitude)
            if not facility:
                continue
            if category and facility["facility_type_key"] != category:
                continue
            identity = (element.get("type"), element.get("id"))
            if identity in seen:
                continue
            seen.add(identity)
            facility.pop("facility_type_key", None)
            facilities.append(facility)

        facilities.sort(key=lambda item: item["distance_km"] if item["distance_km"] is not None else math.inf)
        return facilities[:MAX_RESULTS]

    @classmethod
    def geocode(cls, *, city="", pincode=""):
        city = " ".join(city.split())
        pincode = " ".join(pincode.split())
        cache_material = f"{city.casefold()}|{pincode.casefold()}".encode("utf-8")
        cache_key = f"hospitals:geocode:{hashlib.sha256(cache_material).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        user_agent = os.environ.get("MAPS_USER_AGENT", "").strip()
        if not user_agent:
            raise ServiceUnavailable(
                "Set MAPS_USER_AGENT before enabling city/postcode searches."
            )
        if not cache.add(NOMINATIM_LOCK_KEY, "1", timeout=REQUEST_TIMEOUT_SECONDS + 5):
            raise ServiceUnavailable("Location lookup is busy. Please retry shortly.")

        try:
            last_request = cache.get(NOMINATIM_LAST_REQUEST_KEY)
            if last_request is not None:
                wait_seconds = 1.0 - (time.monotonic() - last_request)
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
            cache.set(NOMINATIM_LAST_REQUEST_KEY, time.monotonic(), timeout=GEOCODE_CACHE_SECONDS)

            params = {"format": "jsonv2", "limit": 1, "addressdetails": 1}
            if city:
                params["city"] = city
            if pincode:
                params["postalcode"] = pincode
            request_url = f"{os.environ.get('NOMINATIM_API_URL', DEFAULT_NOMINATIM_URL)}?{urlencode(params)}"
            response = cls._request_json(request_url, headers={"User-Agent": user_agent})
        finally:
            cache.delete(NOMINATIM_LOCK_KEY)

        if not isinstance(response, list) or not response:
            return None
        try:
            coordinates = {
                "latitude": float(response[0]["lat"]),
                "longitude": float(response[0]["lon"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ServiceUnavailable("The location lookup returned invalid coordinates.") from exc
        if not (
            math.isfinite(coordinates["latitude"])
            and -90 <= coordinates["latitude"] <= 90
            and math.isfinite(coordinates["longitude"])
            and -180 <= coordinates["longitude"] <= 180
        ):
            raise ServiceUnavailable("The location lookup returned invalid coordinates.")
        cache.set(cache_key, coordinates, GEOCODE_CACHE_SECONDS)
        return coordinates

    @staticmethod
    def _build_overpass_query(latitude, longitude, radius):
        latitude = float(latitude)
        longitude = float(longitude)
        radius = int(radius)
        return (
            "[out:json][timeout:15];("
            f'nwr(around:{radius},{latitude:.6f},{longitude:.6f})["amenity"~'
            '"^(hospital|clinic|doctors|pharmacy|ambulance_station|fire_station)$"];'
            f'nwr(around:{radius},{latitude:.6f},{longitude:.6f})["healthcare"~'
            '"^(hospital|clinic|doctor|pharmacy|centre)$"];'
            f'nwr(around:{radius},{latitude:.6f},{longitude:.6f})["emergency"~'
            '"^(yes|ambulance_station)$"];);out center tags;'
        )

    @classmethod
    def _request_json(cls, url, data=None, headers=None):
        request_headers = {"User-Agent": os.environ.get("MAPS_USER_AGENT", "ArogyaAI/0.1")}
        request_headers.update(headers or {})
        request = Request(url, data=data, headers=request_headers, method="POST" if data else "GET")
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ServiceUnavailable("The map search service is temporarily unavailable.") from exc
        if len(content) > MAX_RESPONSE_BYTES:
            raise ServiceUnavailable("The map search response exceeded the safe size limit.")
        try:
            return json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ServiceUnavailable("The map search service returned invalid data.") from exc

    @classmethod
    def _normalize_element(cls, element, origin_latitude, origin_longitude):
        if not isinstance(element, dict):
            return None
        tags = element.get("tags")
        if not isinstance(tags, dict):
            return None
        facility_type = cls._facility_type(tags)
        if not facility_type:
            return None

        latitude = element.get("lat")
        longitude = element.get("lon")
        if latitude is None or longitude is None:
            center = element.get("center") or {}
            latitude = center.get("lat")
            longitude = center.get("lon")
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return None
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None

        distance = cls._distance_km(float(origin_latitude), float(origin_longitude), latitude, longitude)
        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("mobile")
        return {
            "name": tags.get("name") or tags.get("operator") or "Unnamed facility",
            "address": cls._format_address(tags),
            "phone": phone,
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": round(distance, 2),
            "facility_type": facility_type[1],
            "facility_type_key": facility_type[0],
        }

    @staticmethod
    def _facility_type(tags):
        amenity = str(tags.get("amenity") or "").casefold()
        healthcare = str(tags.get("healthcare") or "").casefold()
        emergency = str(tags.get("emergency") or "").casefold()
        if amenity == "pharmacy" or healthcare == "pharmacy":
            return "pharmacy", "Pharmacy"
        if amenity in {"hospital"} or healthcare == "hospital":
            return "hospital", "Hospital"
        if amenity in {"clinic", "doctors"} or healthcare in {"clinic", "doctor", "centre"}:
            return "clinic", "Clinic"
        if amenity in {"ambulance_station", "fire_station"} or emergency in {"yes", "ambulance_station"}:
            return "emergency", "Emergency Facility"
        return None

    @staticmethod
    def _format_address(tags):
        full_address = tags.get("addr:full")
        if full_address:
            return full_address
        parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:suburb"),
            tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village"),
            tags.get("addr:postcode"),
            tags.get("addr:state"),
        ]
        normalized = (part.strip() for part in parts if isinstance(part, str) and part.strip())
        return ", ".join(dict.fromkeys(normalized))

    @staticmethod
    def _distance_km(lat1, lon1, lat2, lon2):
        earth_radius_km = 6371.0088
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
