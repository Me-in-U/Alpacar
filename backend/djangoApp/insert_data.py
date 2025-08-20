#!/usr/bin/env python

import os

import django

# Django 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django.setup()

from vehicles.models import VehicleModel


def insert_vehicle_data():
    # 차량 모델 데이터
    vehicle_data = [
        {
            "brand": "KIA",
            "model_name": "Carnival",
            "size_class": "suv",
            "image_url": "/static/vehicle_images/carnival.avif",
        },
        {
            "brand": "KIA",
            "model_name": "EV6",
            "size_class": "suv",
            "image_url": "/static/vehicle_images/ev6.avif",
        },
        {
            "brand": "KIA",
            "model_name": "K5",
            "size_class": "midsize",
            "image_url": "/static/vehicle_images/k5.avif",
        },
        {
            "brand": "KIA",
            "model_name": "Morning",
            "size_class": "compact",
            "image_url": "/static/vehicle_images/morning.avif",
        },
        {
            "brand": "KIA",
            "model_name": "Sorento",
            "size_class": "suv",
            "image_url": "/static/vehicle_images/sorento.avif",
        },
        {
            "brand": "KIA",
            "model_name": "Sportage",
            "size_class": "suv",
            "image_url": "/static/vehicle_images/sportage.avif",
        },
    ]

    # 데이터 삽입
    for data in vehicle_data:
        _, created = VehicleModel.objects.get_or_create(
            brand=data["brand"],
            model_name=data["model_name"],
            defaults={"size_class": data["size_class"], "image_url": data["image_url"]},
        )

        if created:
            print(f'Successfully created {data["brand"]} {data["model_name"]}')
        else:
            print(f'{data["brand"]} {data["model_name"]} already exists')

    print("Vehicle model data insertion completed!")


if __name__ == "__main__":
    insert_vehicle_data()
