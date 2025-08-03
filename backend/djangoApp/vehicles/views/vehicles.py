from rest_framework import generics, permissions
from vehicles.models import Vehicle, VehicleModel
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


class VehicleModelListAPIView(generics.ListAPIView):
    """
    GET  /api/vehicle-models/
      → 제조사·모델명·이미지 목록 조회
    """
    
    @swagger_auto_schema(
        operation_description="제조사와 모델명, 이미지 목록을 조회합니다.",
        responses={
            200: VehicleModelSerializer(many=True),
            401: "인증되지 않은 사용자"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    queryset = VehicleModel.objects.all().order_by("brand", "model_name")
    serializer_class = VehicleModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class VehicleListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/vehicles/   → 내 차량 목록 조회
    POST /api/vehicles/   → 차량 생성
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="사용자의 차량 목록을 조회합니다.",
        responses={
            200: VehicleSerializer(many=True),
            401: "인증되지 않은 사용자"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="새로운 차량을 등록합니다.",
        request_body=VehicleCreateSerializer,
        responses={
            201: VehicleSerializer,
            400: "잘못된 요청 데이터",
            401: "인증되지 않은 사용자"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VehicleCreateSerializer
        return VehicleSerializer

    def perform_create(self, serializer):
        serializer.save()


class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/vehicles/{pk}/   → 단일 차량 조회
    PUT    /api/vehicles/{pk}/   → 전체 수정 (model, license_plate)
    PATCH  /api/vehicles/{pk}/   → 부분 수정
    DELETE /api/vehicles/{pk}/   → 차량 삭제
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="특정 차량의 상세 정보를 조회합니다.",
        responses={
            200: VehicleSerializer,
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자"
        }
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
            401: "인증되지 않은 사용자"
        }
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
            401: "인증되지 않은 사용자"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="차량을 삭제합니다.",
        responses={
            204: "삭제 성공",
            404: "차량을 찾을 수 없음",
            401: "인증되지 않은 사용자"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return VehicleCreateSerializer
        return VehicleSerializer


@swagger_auto_schema(
    method='get',
    operation_description="특정 번호판이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            'license',
            openapi.IN_QUERY,
            description="확인할 번호판",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="번호판 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'exists': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        ),
        400: "license 파라미터가 없음",
        401: "인증되지 않은 사용자"
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_license(request):
    """
    GET /api/vehicles/check-license/?license=12가3456
    → { "exists": true } or { "exists": false }
    """
    license_plate = request.query_params.get("license")
    if not license_plate:
        return Response(
            {"detail": "license 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = Vehicle.objects.filter(license_plate=license_plate).exists()
    return Response({"exists": exists})
