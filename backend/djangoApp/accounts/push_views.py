# accounts/push_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Member, PushSubscription


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def push_setting(request):
    user = request.user
    if request.method == "GET":
        return Response({"push_on": user.push_enabled})
    # POST: {"push_on": true/false}
    on = request.data.get("push_on", False)
    user.push_enabled = bool(on)
    user.save()
    return Response({"push_on": user.push_enabled})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    data = request.data
    PushSubscription.objects.update_or_create(
        user=request.user,
        endpoint=data["endpoint"],
        defaults={"p256dh": data["keys"]["p256dh"], "auth": data["keys"]["auth"]},
    )
    return Response(status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unsubscribe_push(request):
    endpoint = request.data.get("endpoint")
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
