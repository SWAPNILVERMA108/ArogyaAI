from django.urls import path

from .admin_views import AdminStatsView, AdminUserDetailView, AdminUserListView

app_name = "admin_api"

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="stats"),
    path("users/", AdminUserListView.as_view(), name="users"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="user-detail"),
]
