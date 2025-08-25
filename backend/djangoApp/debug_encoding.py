#!/usr/bin/env python

import os

import django

# Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django.setup()

from vehicles.models import VehicleLicensePlateModelMapping

print("=== 라이센스 플레이트 인코딩 디버깅 ===")

# 모든 라이센스 플레이트 출력
for mapping in VehicleLicensePlateModelMapping.objects.all():
    plate = mapping.license_plate
    print(f'License plate: "{plate}"')
    print(f'  - Raw bytes: {plate.encode("utf-8")}')
    print(f"  - Length: {len(plate)}")
    print(f"  - Characters: {list(plate)}")
    print("---")

# 테스트 검색
test_plate = "12가3456"
print(f'\n테스트 플레이트: "{test_plate}"')
print(f'  - Raw bytes: {test_plate.encode("utf-8")}')

# 데이터베이스에서 직접 검색
found = VehicleLicensePlateModelMapping.objects.filter(
    license_plate=test_plate
).exists()
print(f"  - Found in DB: {found}")

# 유사한 패턴 검색
similar = VehicleLicensePlateModelMapping.objects.filter(
    license_plate__contains="가"
).values_list("license_plate", flat=True)
print(f'  - Similar plates with "가": {list(similar)}')
