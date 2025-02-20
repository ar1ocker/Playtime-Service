from django.urls import path

from .views import BattleMetricsPlaytimeUpdateApi, PlaytimeGetApi

urlpatterns = [
    path("get-playtime/<str:path>/", PlaytimeGetApi.as_view(), name="playtime-get"),
    path(
        "set-playtime/bm/<str:path>/", BattleMetricsPlaytimeUpdateApi.as_view(), name="battle-metrics-playtime-update"
    ),
]
