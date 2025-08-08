# parking/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from events.models import VehicleEvent

from .models import ParkingAssignment, ParkingAssignmentHistory, ParkingSpace
from .serializers import (
    ParkingAssignmentSerializer,
    ParkingHistorySerializer,
    ParkingScoreHistorySerializer,
    ParkingSpaceSerializer,
)


class ParkingHistoryListView(generics.ListAPIView):
    """
    사용자의 주차 이력 조회 API
    GET /api/parking/history/
    """

    serializer_class = ParkingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """현재 로그인한 사용자의 주차 이력만 반환"""
        try:
            return (
                ParkingAssignment.objects.filter(user=self.request.user)
                .select_related("space", "vehicle")
                .order_by("-start_time")
            )
        except Exception as e:
            # 에러 로깅
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error fetching parking history for user {self.request.user.id}: {str(e)}"
            )
            return ParkingAssignment.objects.none()


class ParkingScoreHistoryView(generics.ListAPIView):
    """
    사용자의 주차 점수 히스토리 조회 API
    GET /api/parking/score-history/
    """

    serializer_class = ParkingScoreHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """현재 로그인한 사용자의 점수 히스토리만 반환"""
        return ParkingAssignmentHistory.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )[
            :10
        ]  # 최근 10개만


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parking_chart_data(request):
    """
    차트용 데이터 반환 API
    GET /api/parking/chart-data/
    """
    try:
        # 최근 9개의 주차 기록 가져오기
        assignments = ParkingAssignment.objects.filter(user=request.user).order_by(
            "-start_time"
        )[:9]

        # 차트 데이터 형식으로 변환
        labels = []
        scores = []
        full_date_times = []

        for assignment in reversed(assignments):  # 오래된 것부터 표시
            labels.append(assignment.start_time.strftime("%m-%d"))

            # ParkingAssignmentHistory에서 실제 점수 가져오기
            try:
                history = ParkingAssignmentHistory.objects.filter(
                    assignment=assignment
                ).first()
                if history:
                    score = history.score
                else:
                    # 임시로 랜덤값 사용
                    import random

                    score = random.randint(60, 95)
            except:
                # 에러 발생시 기본값
                score = 75

            scores.append(score)
            full_date_times.append(assignment.start_time.strftime("%Y-%m-%d %H:%M"))

        return Response(
            {"labels": labels, "scores": scores, "fullDateTimes": full_date_times}
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching chart data for user {request.user.id}: {str(e)}")

        # 에러 발생시 빈 데이터 반환
        return Response({"labels": [], "scores": [], "fullDateTimes": []})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_parking_assignment(request):
    """
    새로운 주차 배정 생성 API
    POST /api/parking/assign/
    """
    serializer = ParkingAssignmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_parking(request, assignment_id):
    """
    주차 완료 처리 API
    POST /api/parking/complete/{assignment_id}/
    """
    try:
        assignment = ParkingAssignment.objects.get(
            id=assignment_id, user=request.user, status="ASSIGNED"
        )
        assignment.status = "COMPLETED"
        assignment.end_time = timezone.now()
        assignment.save()

        # 주차 공간 해제
        assignment.space.status = "free"
        assignment.space.save(update_fields=["status"])

        return Response(
            {
                "message": "주차가 완료되었습니다.",
                "assignment": ParkingAssignmentSerializer(assignment).data,
            }
        )
    except ParkingAssignment.DoesNotExist:
        return Response(
            {"error": "주차 배정을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # 필요 시 IsAdminUser로 강화
def set_space_status(request):
    zone = request.data.get("zone")
    slot_number = request.data.get("slot_number")
    new_status = request.data.get("status")  # "free"|"occupied"|"reserved"

    if (
        not zone
        or not slot_number
        or new_status not in dict(ParkingSpace.STATUS_CHOICES)
    ):
        return Response(
            {"error": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ps = ParkingSpace.objects.get(zone=zone, slot_number=slot_number)
    except ParkingSpace.DoesNotExist:
        return Response({"error": "space not found"}, status=status.HTTP_404_NOT_FOUND)

    if ps.status == new_status:
        return Response({"ok": True})  # 변화 없음

    ps.status = new_status
    ps.save(update_fields=["status"])

    # 웹소켓 구독자에게 즉시 반영
    channel_layer = get_channel_layer()
    payload = {
        f"{ps.zone}{ps.slot_number}": {"status": ps.status, "size": ps.size_class}
    }
    async_to_sync(channel_layer.group_send)(
        "parking_space",
        {"type": "parking_space.update", "payload": payload},
    )

    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parking_stats_today(request):
    """
    오늘 이용량 및 요약
    GET /api/parking/stats/today/
    """
    today = timezone.localdate()
    usage_today = VehicleEvent.objects.filter(
        entrance_time__date=today,
    ).count()

    # 참고로 현재 상태 요약도 내려줄 수 있음(선택)
    total_spaces = ParkingSpace.objects.count()
    reserved = ParkingSpace.objects.filter(status="reserved").count()
    occupied = ParkingSpace.objects.filter(status="occupied").count()
    free = ParkingSpace.objects.filter(status="free").count()

    return Response(
        {
            "usage_today": usage_today,
            "total_spaces": total_spaces,
            "occupied": occupied,
            "free": free,
            "reserved": reserved,
            "date": str(today),
        }
    )
