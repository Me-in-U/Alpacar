#!/usr/bin/env python
"""
Simple test of admin workflow without Unicode issues
"""

import os
import sys
import django
from django.utils import timezone

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from vehicles.models import Vehicle, VehicleModel
from parking.models import ParkingSpace
from events.views import manual_entrance

def test_simple_admin_entry():
    """Test simple admin entry notification"""
    
    print("=" * 50)
    print("SIMPLE ADMIN ENTRY TEST")
    print("=" * 50)
    
    # Get test user and vehicle
    User = get_user_model()
    
    # Ensure test user has push enabled
    test_user = User.objects.filter(email__contains='jun').first()
    if test_user:
        test_user.push_enabled = True
        test_user.save()
        print(f"Test user: {test_user.email} (push_enabled: {test_user.push_enabled})")
    else:
        print("No test user found")
        return
    
    # Get or create test vehicle
    try:
        vehicle_model = VehicleModel.objects.first()
        if not vehicle_model:
            vehicle_model = VehicleModel.objects.create(
                brand='테스트',
                model_name='테스트카',
                size_class='compact'
            )
        
        test_vehicle, created = Vehicle.objects.get_or_create(
            license_plate='테스트123',
            defaults={
                'user': test_user,
                'model': vehicle_model
            }
        )
        print(f"Test vehicle: {test_vehicle.license_plate} (user: {test_vehicle.user.email})")
        
    except Exception as e:
        print(f"Vehicle setup error: {e}")
        return
    
    # Create admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            email='admin@test.com',
            nickname='Admin',
            password='admin123'
        )
    
    print(f"Admin user: {admin_user.email}")
    
    # Test manual entry
    print("\nTesting manual entry...")
    
    factory = RequestFactory()
    request = factory.post('/api/events/manual-entrance/', {
        'license_plate': test_vehicle.license_plate
    }, content_type='application/json')
    force_authenticate(request, user=admin_user)
    
    try:
        response = manual_entrance(request)
        print(f"Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("SUCCESS: Manual entry completed!")
            print("Check console for notification logs...")
        else:
            print(f"ERROR: {response.data if hasattr(response, 'data') else 'Unknown error'}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Check notifications
    from accounts.models import Notification
    recent_notifications = Notification.objects.filter(
        user=test_user
    ).order_by('-created_at')[:3]
    
    print(f"\nRecent notifications for {test_user.email}:")
    for notif in recent_notifications:
        print(f"  ID: {notif.id} | Type: {notif.notification_type} | Created: {notif.created_at.strftime('%H:%M:%S')}")
        print(f"      Title: {repr(notif.title)}")  # Use repr to avoid encoding issues
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    test_simple_admin_entry()