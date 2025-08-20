#!/usr/bin/env python

import os

import django

# Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django.setup()

from vehicles.models import Vehicle, VehicleLicensePlateModelMapping

print("=== Vehicle License Plate Model Mapping 검사 ===")
print(f"Total mappings: {VehicleLicensePlateModelMapping.objects.count()}")

if VehicleLicensePlateModelMapping.objects.count() > 0:
    print("\nFirst 10 entries:")
    for i, mapping in enumerate(VehicleLicensePlateModelMapping.objects.all()[:10], 1):
        print(f"{i}. {mapping.license_plate} -> model_id: {mapping.model_id}")

    # 테스트용 라이센스 플레이트 찾기
    test_plates = ["466우5726", "770오4703", "411수5748", "820마2378"]
    print("\n=== 테스트 라이센스 플레이트 검사 ===")
    for plate in test_plates:
        exists = VehicleLicensePlateModelMapping.objects.filter(
            license_plate=plate
        ).exists()
        vehicle_exists = Vehicle.objects.filter(license_plate=plate).exists()
        print(f"{plate}: mapping_exists={exists}, vehicle_exists={vehicle_exists}")
else:
    print("No license plate mappings found in database!")

print("\n=== Vehicle 테이블 검사 ===")
print(f"Total vehicles: {Vehicle.objects.count()}")
if Vehicle.objects.count() > 0:
    print("\nFirst 5 vehicles:")
    for i, vehicle in enumerate(Vehicle.objects.all()[:5], 1):
        print(
            f"{i}. {vehicle.license_plate} -> user: {vehicle.user}, model: {vehicle.model}"
        )
