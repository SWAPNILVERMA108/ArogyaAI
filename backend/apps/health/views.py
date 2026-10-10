from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .serializers import HealthCategorySerializer, HealthTipQuerySerializer, HealthTipSerializer
from .services import TIPS_DISCLAIMER, TIPS_DISCLAIMER_HI, HealthContentService


class HealthCategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Health"], request=None, responses={200: HealthCategorySerializer(many=True)})
    def get(self, request):
        data = HealthCategorySerializer(HealthContentService.categories(), many=True).data
        return success_response(data, "Health categories retrieved successfully.")


class HealthTipListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Health"],
        parameters=[HealthTipQuerySerializer],
        responses={200: HealthTipSerializer(many=True)},
    )
    def get(self, request):
        query = HealthTipQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        tips = HealthContentService.tips(query.validated_data.get("category"))
        return success_response(
            {
                "tips": HealthTipSerializer(tips, many=True).data,
                "disclaimer": TIPS_DISCLAIMER,
                "disclaimer_hi": TIPS_DISCLAIMER_HI,
            },
            "Health tips retrieved successfully.",
        )
