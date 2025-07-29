from django.shortcuts import render
from django.http import JsonResponse
from vehicles.models import VehicleModel
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

def vehicle_models_view(request):
    """차량 모델 목록을 보여주는 뷰"""
    vehicle_models = VehicleModel.objects.all()
    return render(request, 'vehicles/vehicle_models.html', {
        'vehicle_models': vehicle_models
    })

@api_view(['GET'])
def vehicle_models_api(request):
    """차량 모델 목록을 JSON으로 반환하는 API"""
    vehicle_models = VehicleModel.objects.all()
    data = []
    
    for model in vehicle_models:
        data.append({
            'id': model.id,
            'brand': model.brand,
            'model_name': model.model_name,
            'size_class': model.size_class,
            'image_url': model.image_url,
            'full_name': str(model)
        })
    
    return Response(data, status=status.HTTP_200_OK)
