from django.urls import path

from .views import NearbyFacilitiesView


app_name = "hospitals"

urlpatterns = [
    path("nearby/", NearbyFacilitiesView.as_view(), name="nearby"),
]
