from django.core.management.base import BaseCommand
from vehicles.models import VehicleModel
import os

class Command(BaseCommand):
    help = 'Insert vehicle model data into database'

    def handle(self, *args, **options):
        # 차량 모델 데이터
        vehicle_data = [
            {
                'brand': 'KIA',
                'model_name': 'Carnival',
                'size_class': 'suv',
                'image_url': '/static/vehicle_images/carnival.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'EV6',
                'size_class': 'suv',
                'image_url': '/static/vehicle_images/ev6.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'K5',
                'size_class': 'midsize',
                'image_url': '/static/vehicle_images/k5.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'Morning',
                'size_class': 'compact',
                'image_url': '/static/vehicle_images/morning.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'Sorento',
                'size_class': 'suv',
                'image_url': '/static/vehicle_images/sorento.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'Sportage',
                'size_class': 'suv',
                'image_url': '/static/vehicle_images/sportage.avif'
            }
        ]

        # 데이터 삽입
        for data in vehicle_data:
            vehicle_model, created = VehicleModel.objects.get_or_create(
                brand=data['brand'],
                model_name=data['model_name'],
                defaults={
                    'size_class': data['size_class'],
                    'image_url': data['image_url']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {data["brand"]} {data["model_name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{data["brand"]} {data["model_name"]} already exists')
                )

        self.stdout.write(
            self.style.SUCCESS('Vehicle model data insertion completed!')
        ) 