# parking/urls.py

from django.urls import path
from events.views import active_vehicle_events

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
    # 주차 완료 처리
    path(
        "parking/complete/<int:assignment_id>/",
        views.complete_parking,
        name="parking-complete",
    ),
    path("parking/space/set-status/", views.set_space_status, name="set-space-status"),
    path("parking/stats/today/", views.parking_stats_today, name="parking-stats-today"),
    path("vehicle-events/active/", active_vehicle_events),
    # 주차 배정 생성
    path("parking/assign/", views.assign_space),
    # 관리자 주차 완료 처리
    path("parking/admin/complete/", views.admin_complete_parking, name="admin-complete-parking"),
    # 관리자 사용자 점수 업데이트
    path("parking/admin/update-scores/", views.update_all_user_scores, name="admin-update-scores"),
]
