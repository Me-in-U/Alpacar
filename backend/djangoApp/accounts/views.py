# accounts/views.py
import hashlib
import json
import random
import string

from decouple import config
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Member, PushSubscription


def random_string(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def test_methods(request):
    """
    템플릿 방식과 API 방식을 동시에 테스트하는 페이지 렌더
    """
    return render(request, "accounts/test_methods.html")


def push_setting_view(request):
    uid = request.session.get("member_id")
    if not uid:
        return redirect("test_methods")
    user = Member.objects.get(id=uid)
    return render(
        request,
        "accounts/push_setting.html",
        {
            "push_on": user.push_enabled,
            "VAPID_PUBLIC_KEY": config("VAPID_PUBLIC_KEY"),
        },
    )


@csrf_exempt
def update_push_setting(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST만 허용"}, status=405)
    uid = request.session.get("member_id")
    if not uid:
        return JsonResponse({"error": "로그인 필요"}, status=403)
    body = json.loads(request.body)
    on = body.get("push_on", False)
    user = Member.objects.get(id=uid)
    user.push_enabled = bool(on)
    user.save()
    return JsonResponse({"status": "ok", "push_on": user.push_enabled})


@csrf_exempt
def subscribe_push(request):
    """
    클라이언트에서 전달한 구독 정보를 DB에 저장
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST만 허용"}, status=405)
    uid = request.session.get("member_id")
    if not uid:
        return JsonResponse({"error": "로그인 필요"}, status=403)

    data = json.loads(request.body)
    # data 에는 endpoint, keys: p256dh, auth 가 들어있습니다.
    PushSubscription.objects.update_or_create(
        user_id=uid,
        endpoint=data["endpoint"],
        defaults={"p256dh": data["keys"]["p256dh"], "auth": data["keys"]["auth"]},
    )
    return JsonResponse({"status": "subscribed"})


@csrf_exempt
def unsubscribe_push(request):
    """
    클라이언트에서 전달한 endpoint 로 DB 구독 레코드를 삭제
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST만 허용"}, status=405)
    uid = request.session.get("member_id")
    if not uid:
        return JsonResponse({"error": "로그인 필요"}, status=403)

    data = json.loads(request.body)
    endpoint = data.get("endpoint")
    if endpoint:
        PushSubscription.objects.filter(user_id=uid, endpoint=endpoint).delete()
        return JsonResponse({"status": "unsubscribed"})
    else:
        return JsonResponse({"error": "endpoint 누락"}, status=400)
