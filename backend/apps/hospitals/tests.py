import json
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .services import HospitalFinderService


User = get_user_model()


class HospitalFinderAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="maps-patient@example.com", name="Map Patient", password="StrongPass123!"
        )
        self.client.force_authenticate(self.patient)
        cache.clear()

    @patch("apps.hospitals.services.urlopen")
    def test_coordinate_search_returns_live_facilities_with_osm_attribution(self, urlopen):
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "tags": {
                        "name": "Community Hospital",
                        "amenity": "hospital",
                        "addr:street": "Main Road",
                        "phone": "+91 12345 67890",
                    },
                },
                {
                    "type": "way",
                    "id": 2,
                    "center": {"lat": 12.9816, "lon": 77.5946},
                    "tags": {"name": "Care Pharmacy", "amenity": "pharmacy"},
                },
            ]
        }
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()

        response = self.client.get(
            reverse("hospitals:nearby"),
            {"latitude": "12.9716", "longitude": "77.5946", "radius": 5000},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["facilities"]
        self.assertEqual([item["name"] for item in results], ["Community Hospital", "Care Pharmacy"])
        self.assertEqual(results[0]["facility_type"], "Hospital")
        self.assertEqual(results[0]["address"], "Main Road")
        self.assertEqual(results[1]["facility_type"], "Pharmacy")
        self.assertEqual(results[1]["distance_km"], 1.11)
        self.assertIn("OpenStreetMap", response.data["data"]["attribution"])
        self.assertEqual(
            response.data["data"]["attribution_url"],
            "https://www.openstreetmap.org/copyright",
        )
        query = parse_qs(urlopen.call_args.args[0].data.decode())["data"][0]
        self.assertIn("around:5000,12.971600,77.594600", query)

    @patch("apps.hospitals.services.urlopen")
    def test_city_pincode_search_geocodes_then_searches_overpass(self, urlopen):
        nominatim = MagicMock()
        nominatim.__enter__.return_value.read.return_value = b'[{"lat":"19.0760","lon":"72.8777"}]'
        overpass = MagicMock()
        overpass.__enter__.return_value.read.return_value = b'{"elements":[]}'
        urlopen.side_effect = [nominatim, overpass]

        with patch.dict("os.environ", {"MAPS_USER_AGENT": "ArogyaAI-tests/1.0"}):
            response = self.client.get(
                reverse("hospitals:nearby"), {"city": "Mumbai", "pincode": "400001"}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["facilities"], [])
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("ArogyaAI-tests/1.0", urlopen.call_args_list[0].args[0].get_header("User-agent"))

    def test_invalid_or_incomplete_search_parameters_are_rejected(self):
        cases = (
            {"latitude": "12.9"},
            {"longitude": "77.5"},
            {"latitude": "91", "longitude": "77.5"},
            {"latitude": "12.9", "longitude": "77.5", "city": "Mumbai"},
            {"city": "Mumbai", "category": "unknown"},
            {"city": "Mumbai", "radius": 50000},
        )
        for params in cases:
            with self.subTest(params=params):
                response = self.client.get(reverse("hospitals:nearby"), params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_coordinate_search_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            reverse("hospitals:nearby"), {"latitude": 12.9, "longitude": 77.5}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_category_filters_and_osm_element_normalization(self):
        result = HospitalFinderService._normalize_element(
            {
                "type": "way",
                "id": 7,
                "center": {"lat": 13.0, "lon": 77.5},
                "tags": {
                    "amenity": "clinic",
                    "healthcare": "clinic",
                    "addr:street": "Main Road",
                    "addr:city": "Bengaluru",
                    "addr:suburb": "Main Road",
                    "contact:phone": "123",
                },
            },
            13.0,
            77.5,
        )
        self.assertEqual(result["facility_type_key"], "clinic")
        self.assertEqual(result["address"], "Main Road, Bengaluru")
        self.assertEqual(result["phone"], "123")
        self.assertEqual(result["distance_km"], 0.0)

    def test_city_search_requires_an_identifying_user_agent(self):
        with patch.dict("os.environ", {"MAPS_USER_AGENT": ""}):
            response = self.client.get(reverse("hospitals:nearby"), {"city": "Pune"})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("apps.hospitals.services.urlopen")
    def test_repeated_coordinate_search_uses_cached_map_results(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"elements":[]}'
        params = {"latitude": 18.52, "longitude": 73.85}

        first = self.client.get(reverse("hospitals:nearby"), params)
        second = self.client.get(reverse("hospitals:nearby"), params)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(urlopen.call_count, 1)
