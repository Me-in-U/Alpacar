from django.db import models
from accounts.models import Member

class VehicleModel(models.Model):
    SIZE_CLASS_CHOICES = [
        ('compact', 'Compact'),
        ('midsize', 'Midsize'),
        ('suv', 'SUV'),
    ]
    
    model_id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    size_class = models.CharField(max_length=10, choices=SIZE_CLASS_CHOICES)
    image_url = models.CharField(max_length=255)

    class Meta:
        db_table = 'VehicleModel'

    def __str__(self):
        return f"{self.brand} {self.model_name}"

class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    license_plate = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(Member, on_delete=models.CASCADE, db_column='user_id')
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, db_column='model_id')

    class Meta:
        db_table = 'Vehicle'

    def __str__(self):
        return self.license_plate

class VehicleEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, db_column='vehicle_id')
    event_type = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    class Meta:
        db_table = 'VehicleEvent'

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.event_type}"
