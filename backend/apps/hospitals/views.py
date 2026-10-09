from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.exceptions.api import ServiceUnavailable
from common.utils.responses import success_response

from .serializers import NearbyFacilitiesQuerySerializer, NearbyFacilitiesResponseSerializer
from .services import HospitalFinderService


class NearbyFacilitiesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "maps"

    @extend_schema(
        tags=["Hospitals"],
        parameters=[NearbyFacilitiesQuerySerializer],
        responses={200: NearbyFacilitiesResponseSerializer},
    )
    def get(self, request):
        serializer = NearbyFacilitiesQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data
        latitude, longitude = query.get("latitude"), query.get("longitude")
        if latitude is None:
            coordinates = HospitalFinderService.geocode(
                city=query.get("city", ""),
                pincode=query.get("pincode", ""),
            )
            if coordinates is None:
                return success_response(
                    {
                        "facilities": [],
                        "attribution": "© OpenStreetMap contributors",
                        "attribution_url": "https://www.openstreetmap.org/copyright",
                    },
                    "No matching location was found.",
                )
            latitude = coordinates["latitude"]
            longitude = coordinates["longitude"]

        facilities = HospitalFinderService.search(
            latitude=latitude,
            longitude=longitude,
            radius=query["radius"],
            category=query.get("category"),
        )
        data = {
            "facilities": facilities,
            "attribution": "© OpenStreetMap contributors",
            "attribution_url": "https://www.openstreetmap.org/copyright",
        }
        return success_response(data, "Nearby facilities retrieved successfully.")
