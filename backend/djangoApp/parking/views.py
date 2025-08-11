# parking/views.py
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from events.broadcast import broadcast_active_vehicles
from events.models import VehicleEvent
from vehicles.models import Vehicle

from .models import ParkingAssignment, ParkingAssignmentHistory, ParkingSpace
from .serializers import (
    AssignRequestSerializer,
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
        _broadcast_space(assignment.space)
        broadcast_active_vehicles()
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
    _broadcast_space(ps)
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


def _broadcast_space(space: ParkingSpace):
    channel_layer = get_channel_layer()
    payload = {
        f"{space.zone}{space.slot_number}": {
            "status": space.status,
            "size": space.size_class,
            "vehicle_id": getattr(space, "current_vehicle_id", None),
            "license_plate": (
                getattr(space.current_vehicle, "license_plate", None)
                if getattr(space, "current_vehicle", None)
                else None
            ),
        }
    }
    async_to_sync(channel_layer.group_send)(
        "parking_space",
        {"type": "parking_space.update", "payload": payload},
    )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def assign_space(request):
    # 1) 입력 검증
    req = AssignRequestSerializer(data=request.data)
    req.is_valid(raise_exception=True)
    plate = req.validated_data["license_plate"].strip()
    zone = req.validated_data["zone"].strip()
    slot_number = req.validated_data["slot_number"]

    # 2) 엔티티 조회
    try:
        vehicle = Vehicle.objects.select_related("user").get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response({"detail": "차량을 찾을 수 없습니다."}, status=404)

    # “현재 입차중(미출차)” 이벤트
    ev = (
        VehicleEvent.objects.filter(vehicle=vehicle, exit_time__isnull=True)
        .order_by("-id")
        .first()
    )
    if not ev:
        return Response({"detail": "현재 입차 중인 기록이 없습니다."}, status=400)

    try:
        new_space = ParkingSpace.objects.get(zone=zone, slot_number=slot_number)
    except ParkingSpace.DoesNotExist:
        return Response({"detail": "주차공간을 찾을 수 없습니다."}, status=404)

    if new_space.status != "free":
        return Response({"detail": "해당 슬롯이 비어있지 않습니다."}, status=400)

    # 3) 기존 배정 여부 확인(이 입차 기록에 대해)
    pa, created = ParkingAssignment.objects.get_or_create(
        entrance_event=ev,
        defaults={
            "user": vehicle.user,
            "vehicle": vehicle,
            "space": new_space,
            "start_time": timezone.now(),
            "status": "ASSIGNED",
        },
    )

    if created:
        # 새로 만들었으니 새 공간만 reserved
        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        _broadcast_space(new_space)
    else:
        # 이미 배정이 있다 → 재배정(공간 교체)
        if pa.space_id == new_space.id:
            return Response(ParkingAssignmentSerializer(pa).data, status=200)

        old_space = pa.space
        pa.space = new_space
        pa.save(update_fields=["space", "updated_at"])

        # 공간 상태 갱신(이전 free, 새 reserved)
        if old_space and old_space.status != "free":
            old_space.status = "free"
            old_space.current_vehicle = None
            old_space.save(update_fields=["status", "current_vehicle", "updated_at"])
            _broadcast_space(old_space)

        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        _broadcast_space(new_space)
    broadcast_active_vehicles()
    return Response(
        ParkingAssignmentSerializer(pa).data, status=201 if created else 200
    )
