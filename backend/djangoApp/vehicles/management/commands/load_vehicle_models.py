from django.core.management.base import BaseCommand
from vehicles.models import VehicleModel
import os

class Command(BaseCommand):
    help = 'Load vehicle models with images from static/vehicle_images'

    def handle(self, *args, **options):
        # 차량 모델 데이터
        vehicle_models = [
            {
                'brand': 'KIA',
                'model_name': 'Carnival',
                'size_class': 'suv',
                'image_url': '/static/vehicle_images/carnival.avif'
            },
            {
                'brand': 'KIA',
                'model_name': 'EV6',
                'size_class': 'midsize',
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

        for model_data in vehicle_models:
            vehicle_model, created = VehicleModel.objects.get_or_create(
                brand=model_data['brand'],
                model_name=model_data['model_name'],
                defaults={
                    'size_class': model_data['size_class'],
                    'image_url': model_data['image_url']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created vehicle model: {vehicle_model}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Vehicle model already exists: {vehicle_model}')
                ) 