# events\views.py

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from events.broadcast import broadcast_active_vehicles
from parking.models import ParkingAssignment, ParkingSpace
from vehicles.models import Vehicle
from accounts.notification_helpers import send_vehicle_entry_notification, send_parking_complete_notification, send_vehicle_exit_notification
from accounts.utils import create_notification

from .models import VehicleEvent
from .serializers import VehicleEventSerializer


class VehicleEventPagination(PageNumberPagination):
    page_size = 10  # 한 페이지당 10개


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_vehicle_events(request):
    qs = VehicleEvent.objects.select_related("vehicle").order_by("-id")  # 번호판 용
    paginator = VehicleEventPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = VehicleEventSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_entrance(request):
    plate = (request.data.get("license_plate") or "").strip()
    if not plate:
        return Response(
            {"detail": "license_plate가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        vehicle = Vehicle.objects.get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response(
            {"detail": "해당 차량을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    last_event = VehicleEvent.objects.filter(vehicle=vehicle).order_by("-id").first()

    # 최근 이벤트가 없거나 출차였다면 새 입차 생성
    if last_event is None or last_event.status == "Exit":
        ev = VehicleEvent.objects.create(
            vehicle=vehicle,
            entrance_time=timezone.now(),
            parking_time=None,
            exit_time=None,
            status="Entrance",
        )
        
        # 푸시 알림 전송 - 입차 알림 (DB 조회로 user_id 확인)
        try:
            # vehicle 테이블에서 user_id 조회
            vehicle_with_user = Vehicle.objects.select_related('user').get(
                license_plate=vehicle.license_plate
            )
            target_user = vehicle_with_user.user
            
            print(f"[DB QUERY] vehicle 테이블 조회: license_plate={vehicle.license_plate} -> user_id={target_user.id}")
            
            entry_data = {
                'plate_number': vehicle.license_plate,
                'parking_lot': 'SSAFY 주차장',
                'entry_time': timezone.now().isoformat(),
                'admin_action': True,
                'action_url': '/parking-recommend',  # 알림 터치 시 이동할 페이지
                'action_type': 'navigate'
            }
            send_vehicle_entry_notification(target_user, entry_data)
            print(f"[ADMIN] 입차 알림 전송됨: {vehicle.license_plate} -> {target_user.email} (user_id: {target_user.id})")
        except Vehicle.DoesNotExist:
            print(f"[ADMIN ERROR] vehicle 테이블에서 차량 정보를 찾을 수 없음: {vehicle.license_plate}")
        except Exception as e:
            print(f"[ADMIN ERROR] 입차 알림 전송 실패: {str(e)}")
        
        # 입차 목록 갱신 트리거
        broadcast_active_vehicles()
        ser = VehicleEventSerializer(ev)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # 이미 Entrance/Parking 등 진행 중이면 그 이벤트 그대로 반환
    ser = VehicleEventSerializer(last_event)
    broadcast_active_vehicles()
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id):
    now = timezone.now()
    # 1) “입차는 되었으나(parking_time is null) 아직 주차되지 않은” 이벤트 조회
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id,
            entrance_time__isnull=False,
            parking_time__isnull=True,
        )
        .order_by("-id")
        .first()
    )

    if ev is None:
        return Response(
            {"detail": "해당 차량의 입차 기록이 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2) 주차시간·상태 업데이트
    ev.parking_time = now
    ev.status = "Parking"
    ev.save()
    broadcast_active_vehicles()
    
    #  이 입차 이벤트에 대한 배정이 있으면 슬롯도 occupied 처리
    space_label = None
    vehicle = ev.vehicle
    
    try:
        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        space = pa.space
        if space:
            space.status = "occupied"
            space.save(update_fields=["status", "updated_at"])
            space_label = f'{space.zone}{space.slot_number}'

            # 슬롯 상태 브로드캐스트(색/상태 반영)
            from parking.views import _broadcast_space
            _broadcast_space(space)
            
            # parking_assignment 테이블의 status를 COMPLETED로 업데이트 (아직 안 함 - 출차할 때 함)
            # 주차 완료 시에는 아직 ASSIGNED 상태 유지
            
            # 푸시 알림 전송 - 주차 완료 알림 (Celery 큐잉)
            try:
                # 간단한 점수 계산
                import random
                score = random.randint(70, 95)
                
                parking_data = {
                    'plate_number': vehicle.license_plate,
                    'parking_space': space_label or '배정된 구역',
                    'parking_time': now.isoformat(),
                    'score': score,
                    'admin_action': True
                }
                result = send_parking_complete_notification(vehicle.user, parking_data)
                print(f"[ADMIN] 주차 완료 알림 큐잉: {vehicle.license_plate} -> {space_label} ({score}점, task: {result.get('task_id', 'sync')})")
            except Exception as e:
                print(f"[ADMIN ERROR] 주차 완료 알림 큐잉 실패: {str(e)}")
                
    except ParkingAssignment.DoesNotExist:
        # 배정이 없는 경우에도 기본 주차 완료 알림 전송
        try:
            parking_data = {
                'plate_number': vehicle.license_plate,
                'parking_space': '배정된 구역',
                'parking_time': now.isoformat(),
                'score': None,
                'admin_action': True
            }
            result = send_parking_complete_notification(vehicle.user, parking_data)
            print(f"[ADMIN] 주차 완료 알림 전송 (배정 없음): {vehicle.license_plate} (알림 ID: {result.id if hasattr(result, 'id') else 'N/A'})")
        except Exception as e:
            print(f"[ADMIN ERROR] 주차 완료 알림 전송 실패 (배정 없음): {str(e)}")

    # 입차 차량 패널 실시간 갱신 트리거
    broadcast_active_vehicles()
    return Response(VehicleEventSerializer(ev).data, status=200)


from rest_framework import status


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id):
    now = timezone.now()
    # ① “주차는 되었으나(exit_time이 null) 아직 출차되지 않은” 이벤트 조회
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id, parking_time__isnull=False, exit_time__isnull=True
        )
        .order_by("-id")
        .first()
    )

    if ev is None:
        return Response(
            {"detail": "출차할 주차 기록이 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ② exit_time·status 업데이트
    ev.exit_time = now
    ev.status = "Exit"
    ev.save()
    broadcast_active_vehicles()
    
    vehicle = ev.vehicle
    space_label = None
    parking_duration = None
    
    #  배정이 있으면 완료 처리 + 슬롯 해제
    try:
        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        pa.status = "COMPLETED"
        pa.end_time = now
        pa.save(update_fields=["status", "end_time", "updated_at"])

        space = pa.space
        if space:
            space_label = f'{space.zone}{space.slot_number}'
            space.status = "free"
            space.current_vehicle = None
            space.save(update_fields=["status", "current_vehicle", "updated_at"])
            from parking.views import _broadcast_space
            _broadcast_space(space)
            
        # 주차 시간 계산
        if ev.parking_time and ev.exit_time:
            duration = ev.exit_time - ev.parking_time
            total_minutes = int(duration.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            if hours > 0:
                parking_duration = f"{hours}시간 {minutes}분"
            else:
                parking_duration = f"{minutes}분"
        
        # 푸시 알림 전송 - 출차 완료 알림 (Celery 큐잉)
        try:
            exit_data = {
                'plate_number': vehicle.license_plate,
                'parking_space': space_label or '주차 구역',
                'exit_time': now.isoformat(),
                'parking_duration': parking_duration,
                'admin_action': True
            }
            result = send_vehicle_exit_notification(vehicle.user, exit_data)
            print(f"[ADMIN] 출차 알림 전송: {vehicle.license_plate} -> {space_label} ({parking_duration}, 알림 ID: {result.id if hasattr(result, 'id') else 'N/A'})")
        except Exception as e:
            print(f"[ADMIN ERROR] 출차 알림 전송 실패: {str(e)}")
            
    except ParkingAssignment.DoesNotExist:
        # 배정이 없는 경우에도 기본 출차 알림 전송
        try:
            exit_data = {
                'plate_number': vehicle.license_plate,
                'parking_space': '주차 구역',
                'exit_time': now.isoformat(),
                'parking_duration': None,
                'admin_action': True
            }
            result = send_vehicle_exit_notification(vehicle.user, exit_data)
            print(f"[ADMIN] 출차 알림 전송 (배정 없음): {vehicle.license_plate} (알림 ID: {result.id if hasattr(result, 'id') else 'N/A'})")
        except Exception as e:
            print(f"[ADMIN ERROR] 출차 알림 전송 실패 (배정 없음): {str(e)}")

    return Response(VehicleEventSerializer(ev).data, status=200)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def active_vehicle_events(request):
    qs = (
        VehicleEvent.objects.select_related("vehicle", "vehicle__model")
        .filter(exit_time__isnull=True)
        .order_by("-id")
    )

    data = []
    for ev in qs:
        # FK: ParkingAssignment.entrance_event = ev
        assignment = getattr(ev, "assignment", None)  # OneToOne 역참조
        assigned = None
        if assignment and assignment.space:
            assigned = {
                "zone": assignment.space.zone,
                "slot_number": assignment.space.slot_number,
                "label": f"{assignment.space.zone}{assignment.space.slot_number}",
            }

        data.append(
            {
                "id": ev.id,
                "vehicle_id": ev.vehicle_id,
                "license_plate": ev.vehicle.license_plate,
                "entrance_time": ev.entrance_time,
                "status": ev.status,
                "assigned_space": assigned,  # ← 추가!
            }
        )
    return Response({"results": data})
