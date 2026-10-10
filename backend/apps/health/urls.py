from django.urls import path

from .views import HealthCategoryListView, HealthTipListView

app_name = "health"

urlpatterns = [
    path("categories/", HealthCategoryListView.as_view(), name="categories"),
    path("tips/", HealthTipListView.as_view(), name="tips"),
]
