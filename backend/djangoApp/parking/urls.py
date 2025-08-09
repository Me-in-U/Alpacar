# parking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 주차 이력 조회
    path(
        "parking/history/",
        views.ParkingHistoryListView.as_view(),
        name="parking-history",
    ),
    # 주차 점수 히스토리 조회
    path(
        "parking/score-history/",
        views.ParkingScoreHistoryView.as_view(),
        name="parking-score-history",
    ),
    # 차트 데이터 조회
    path("parking/chart-data/", views.parking_chart_data, name="parking-chart-data"),
    # 주차 배정 생성
    path("parking/assign/", views.create_parking_assignment, name="parking-assign"),
    # 주차 완료 처리
    path(
        "parking/complete/<int:assignment_id>/",
        views.complete_parking,
        name="parking-complete",
    ),
    path("parking/space/set-status/", views.set_space_status, name="set-space-status"),
    path("parking/stats/today/", views.parking_stats_today, name="parking-stats-today"),
]
