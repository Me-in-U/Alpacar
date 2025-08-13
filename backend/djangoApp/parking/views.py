# parking/views.py
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from events.models import VehicleEvent
from vehicles.models import Vehicle
from accounts.utils import create_notification
from .models import ParkingAssignment, ParkingAssignmentHistory, ParkingSpace
from .serializers import (
    AssignRequestSerializer,
    ParkingAssignmentSerializer,
    ParkingHistorySerializer,
    ParkingScoreHistorySerializer,
)

# 실시간 방송은 signals에서 처리. 여기서는 저장/검증/알림만 수행.


class ParkingHistoryListView(generics.ListAPIView):
    serializer_class = ParkingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return (
                ParkingAssignment.objects.filter(user=self.request.user)
                .select_related("space", "vehicle")
                .order_by("-start_time")
            )
        except Exception:
            return ParkingAssignment.objects.none()


class ParkingScoreHistoryView(generics.ListAPIView):
    serializer_class = ParkingScoreHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ParkingAssignmentHistory.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )[:10]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parking_chart_data(request):
    try:
        assignments = ParkingAssignment.objects.filter(user=request.user).order_by(
            "-start_time"
        )[:9]
        labels, scores, full_date_times = [], [], []
        for a in reversed(assignments):
            labels.append(a.start_time.strftime("%m-%d"))
            try:
                hist = ParkingAssignmentHistory.objects.filter(assignment=a).first()
                score = hist.score if hist else 75
            except Exception:
                score = 75
            scores.append(score)
            full_date_times.append(a.start_time.strftime("%Y-%m-%d %H:%M"))
        return Response(
            {"labels": labels, "scores": scores, "fullDateTimes": full_date_times}
        )
    except Exception:
        return Response({"labels": [], "scores": [], "fullDateTimes": []})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_parking_assignment(request):
    ser = ParkingAssignmentSerializer(data=request.data)
    if ser.is_valid():
        ser.save(user=request.user)
        return Response(ser.data, status=201)
    return Response(ser.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_parking(request, assignment_id):
    try:
        assignment = ParkingAssignment.objects.get(
            id=assignment_id, user=request.user, status="ASSIGNED"
        )
        assignment.status = "COMPLETED"
        assignment.end_time = timezone.now()
        assignment.save()
        space = assignment.space
        space.status = "free"
        space.save(update_fields=["status"])
        return Response(
            {
                "message": "주차가 완료되었습니다.",
                "assignment": ParkingAssignmentSerializer(assignment).data,
            }
        )
    except ParkingAssignment.DoesNotExist:
        return Response({"error": "주차 배정을 찾을 수 없습니다."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # 필요시 IsAdminUser
def set_space_status(request):
    zone = request.data.get("zone")
    slot_number = request.data.get("slot_number")
    new_status = request.data.get("status")
    if (
        (not zone)
        or (not slot_number)
        or (new_status not in dict(ParkingSpace.STATUS_CHOICES))
    ):
        return Response({"error": "invalid parameters"}, status=400)
    try:
        ps = ParkingSpace.objects.get(zone=zone, slot_number=slot_number)
    except ParkingSpace.DoesNotExist:
        return Response({"error": "space not found"}, status=404)
    if ps.status == new_status:
        return Response({"ok": True})
    ps.status = new_status
    ps.save(update_fields=["status"])
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parking_stats_today(request):
    today = timezone.localdate()
    usage_today = VehicleEvent.objects.filter(entrance_time__date=today).count()
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


@api_view(["POST"])
@permission_classes([IsAdminUser])
def assign_space(request):
    req = AssignRequestSerializer(data=request.data)
    req.is_valid(raise_exception=True)
    plate = req.validated_data["license_plate"].strip()
    zone = req.validated_data["zone"].strip()
    slot_number = req.validated_data["slot_number"]

    try:
        vehicle = Vehicle.objects.select_related("user").get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response({"detail": "차량을 찾을 수 없습니다."}, status=404)

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
        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        # 푸시 알림 전송
        try:
            print(f"[ADMIN] 주차 배정 알림 전송 시도: {vehicle.license_plate} → {zone}{slot_number}")
            create_notification(
                user=vehicle.user,
                title="🅿️ 주차 구역 배정",
                message=f"{vehicle.license_plate} 차량에 {zone}{slot_number} 구역이 배정되었습니다. 안내에 따라 주차해 주세요.",
                notification_type="parking_assigned",
                data={
                    "plate_number": vehicle.license_plate,
                    "assigned_space": f"{zone}{slot_number}",
                    "assignment_time": timezone.now().isoformat(),
                    "admin_action": True,
                    "action_url": "/parking-recommend",
                    "action_type": "navigate",
                },
            )
            print(f"[ADMIN] 주차 배정 알림 전송 완료: {vehicle.license_plate}")
        except Exception as e:
            print(f"[ADMIN ERROR] 주차 배정 알림 전송 실패: {vehicle.license_plate} - {str(e)}")
    else:
        if pa.space_id == new_space.id:
            return Response(ParkingAssignmentSerializer(pa).data, status=200)
        old_space = pa.space
        pa.space = new_space
        pa.save(update_fields=["space", "updated_at"])
        if old_space and old_space.status != "free":
            old_space.status = "free"
            old_space.current_vehicle = None
            old_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        # 푸시 알림 전송 (재배정)
        try:
            old_space_name = f"{old_space.zone}{old_space.slot_number}" if old_space else "없음"
            print(f"[ADMIN] 주차 재배정 알림 전송 시도: {vehicle.license_plate} {old_space_name} → {zone}{slot_number}")
            create_notification(
                user=vehicle.user,
                title="🔄 주차 구역 재배정",
                message=f"{vehicle.license_plate} 차량의 주차 구역이 {zone}{slot_number}로 변경되었습니다.",
                notification_type="parking_assigned",
                data={
                    "plate_number": vehicle.license_plate,
                    "old_space": (
                        f"{old_space.zone}{old_space.slot_number}"
                        if old_space
                        else None
                    ),
                    "new_space": f"{zone}{slot_number}",
                    "reassignment_time": timezone.now().isoformat(),
                    "admin_action": True,
                    "action_url": "/parking-recommend",
                    "action_type": "navigate",
                },
            )
            print(f"[ADMIN] 주차 재배정 알림 전송 완료: {vehicle.license_plate}")
        except Exception as e:
            print(f"[ADMIN ERROR] 주차 재배정 알림 전송 실패: {vehicle.license_plate} - {str(e)}")

    # 실시간 방송은 signals가 처리
    return Response(
        ParkingAssignmentSerializer(pa).data, status=201 if created else 200
    )
