# jetson/broadcast.py
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# 장고 -> 젯슨 제어 그룹
JETSON_CONTROL_GROUP = "jetson-control"


def send_request_assignment(license_plate: str, size_class: str):
    """
    젯슨으로 배정 요청 브로드캐스트 (장고 -> 젯슨)
    """
    payload = {
        "message_type": "request_assignment",
        "license_plate": license_plate,
        "size_class": size_class,  # compact|midsize|suv
    }
    async_to_sync(get_channel_layer().group_send)(
        JETSON_CONTROL_GROUP,
        {"type": "jetson_control", "payload": payload},
    )
