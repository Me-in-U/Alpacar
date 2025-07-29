from django.contrib import admin

from events.models import VehicleEvent
from .models import VehicleModel, Vehicle


# Register your models here.
@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ("brand", "model_name", "size_class", "image_url")
    list_filter = ("brand", "size_class")
    search_fields = ("brand", "model_name")
    ordering = ("brand", "model_name")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("license_plate", "user", "model")
    list_filter = ("model__brand", "model__size_class")
    search_fields = ("license_plate", "user__nickname")


@admin.register(VehicleEvent)
class VehicleEventAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "event_type", "timestamp")
    list_filter = ("event_type", "timestamp")
    search_fields = ("vehicle__license_plate",)
