import json
from rest_framework import generics, permissions
from vehicles.models import Vehicle, VehicleLicensePlateModelMapping, VehicleModel
from vehicles.serializers.vehicles import (
    VehicleCreateSerializer,
    VehicleModelSerializer,
    VehicleSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny


class VehicleModelListAPIView(generics.ListAPIView):
    """
    GET  /api/vehicle-models/
      → 제조사·모델명·이미지 목록 조회
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = VehicleModel.objects.all().order_by("brand", "model_name")
    serializer_class = VehicleModelSerializer

    @swagger_auto_schema(
        operation_description="제조사와 모델명, 이미지 목록을 조회합니다.",
        responses={200: VehicleModelSerializer(many=True), 401: "인증되지 않은 사용자"},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VehicleListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/vehicles/   → 내 차량 목록 조회
    POST /api/vehicles/   → 차량 생성
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VehicleCreateSerializer
        return VehicleSerializer

    @swagger_auto_schema(
        operation_description="사용자의 차량 목록을 조회합니다.",
        responses={200: VehicleSerializer(many=True), 401: "인증되지 않은 사용자"},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="새로운 차량을 등록합니다.",
        request_body=VehicleCreateSerializer,
        responses={
            201: VehicleSerializer,
            400: "잘못된 요청 데이터 또는 중복된 번호판",
            401: "인증되지 않은 사용자",
        },
    )
    def post(self, request, *args, **kwargs):
        lp = request.data.get("license_plate")
        if not lp:
            return Response({"detail": "license_plate는 필수입니다."}, status=400)
        if Vehicle.objects.filter(license_plate=lp).exists():
            return Response({"detail": "이미 등록된 차량 번호입니다."}, status=400)
        try:
            mapping = VehicleLicensePlateModelMapping.objects.get(license_plate=lp)
        except VehicleLicensePlateModelMapping.DoesNotExist:
            return Response({"detail": "차량 모델 매핑 정보가 없습니다."}, status=400)
        model = VehicleModel.objects.get(pk=mapping.model_id)
        vehicle = Vehicle.objects.create(
            license_plate=lp, user=request.user, model=model
        )
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data, status=201)


class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/vehicles/{pk}/   → 단일 차량 조회
    PUT    /api/vehicles/{pk}/   → 전체 수정 (model, license_plate)
    PATCH  /api/vehicles/{pk}/   → 부분 수정
    DELETE /api/vehicles/{pk}/   → 차량 삭제
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Vehicle.objects.none()
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return VehicleCreateSerializer
        return VehicleSerializer

    @swagger_auto_schema(
        operation_description="특정 차량의 상세 정보를 조회합니다.",
        responses={
            200: VehicleSerializer,
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="차량 정보를 전체 수정합니다.",
        request_body=VehicleCreateSerializer,
        responses={
            200: VehicleSerializer,
            400: "잘못된 요청 데이터",
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="차량 정보를 부분 수정합니다.",
        request_body=VehicleCreateSerializer,
        responses={
            200: VehicleSerializer,
            400: "잘못된 요청 데이터",
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="차량을 삭제합니다.",
        responses={
            204: "삭제 성공",
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@swagger_auto_schema(
    method="get",
    operation_description="특정 번호판이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            "license",
            openapi.IN_QUERY,
            description="확인할 번호판",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={
        200: openapi.Response(
            description="번호판 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"exists": openapi.Schema(type=openapi.TYPE_BOOLEAN)},
            ),
        ),
        400: "license 파라미터가 없음",
        401: "인증되지 않은 사용자",
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def check_license(request):
    """
    GET /api/vehicles/check-license/?license=12가3456
    -> { "exists": true } or { "exists": false }
    """
    # 파라미터 키 혼동 방지: license 또는 license_plate 모두 허용
    lp = request.query_params.get("license") or request.query_params.get(
        "license_plate"
    )
    if not lp:
        return Response(
            {"detail": "license 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = Vehicle.objects.filter(license_plate=lp).exists()
    return Response({"exists": exists})


@swagger_auto_schema(
    method="get",
    operation_description="현재 사용자가 차량을 등록했는지 확인합니다.",
    responses={
        200: openapi.Response(
            description="차량 등록 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"has_vehicle": openapi.Schema(type=openapi.TYPE_BOOLEAN)},
            ),
        ),
        401: "인증되지 않은 사용자",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_vehicle_registration(request):
    """
    GET /api/user/vehicle/check/
    → { "has_vehicle": true } or { "has_vehicle": false }
    """
    has_vehicle = Vehicle.objects.filter(user=request.user).exists()
    return Response({"has_vehicle": has_vehicle})


@swagger_auto_schema(
    method="get",
    operation_description="차량번호-모델 매핑 정보를 조회합니다.",
    manual_parameters=[
        openapi.Parameter(
            "license_plate",
            openapi.IN_QUERY,
            description="번호판",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={
        200: openapi.Response(
            description="매핑 정보",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"model_id": openapi.Schema(type=openapi.TYPE_INTEGER)},
            ),
        ),
        400: "license_plate 파라미터 필요",
        404: "매핑 정보 없음",
        401: "인증되지 않은 사용자",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_mapping_model(request):
    lp = request.query_params.get("license_plate")
    if not lp:
        return Response(
            {"detail": "license_plate 파라미터 필요"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        mapping = VehicleLicensePlateModelMapping.objects.get(license_plate=lp)
        return Response({"model_id": mapping.model_id})
    except VehicleLicensePlateModelMapping.DoesNotExist:
        return Response({"detail": "매핑 정보 없음"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_simple_vehicle(request):
    """
    POST /api/vehicles/  { "license_plate": "…" }
    → mapping에서 model_id를 조회해 Vehicle 생성
    """
    lp = request.data.get("license_plate")
    if not lp:
        return Response(
            {"detail": "license_plate는 필수입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if Vehicle.objects.filter(license_plate=lp).exists():
        return Response(
            {"detail": "이미 등록된 차량 번호입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        mapping = VehicleLicensePlateModelMapping.objects.get(license_plate=lp)
    except VehicleLicensePlateModelMapping.DoesNotExist:
        return Response(
            {"detail": "차량 모델 매핑 정보가 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model = VehicleModel.objects.get(pk=mapping.model_id)
    vehicle = Vehicle.objects.create(license_plate=lp, user=request.user, model=model)
    serializer = VehicleSerializer(vehicle)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from pywebpush import webpush, WebPushException
from vehicles.models import Vehicle
from accounts.models import PushSubscription


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_push_to_plate(request):
    plate = request.data.get("license_plate")
    if not plate:
        return Response({"error": "license_plate 필수"}, status=400)

    try:
        vehicle = Vehicle.objects.select_related("user").get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response({"error": "차량을 찾을 수 없음"}, status=404)

    user = vehicle.user
    subs = PushSubscription.objects.filter(user=user)
    if not subs:
        return Response({"error": "푸시 구독 없음"}, status=404)

    payload = {"title": "관리자 알림", "body": f"{plate} 차량 관련 안내입니다."}
    for s in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": s.endpoint,
                    "keys": {"p256dh": s.p256dh, "auth": s.auth},
                },
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS,
            )
        except WebPushException as e:
            print(f"[PUSH ERROR] {e}")

    return Response({"success": True})
