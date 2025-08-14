from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

PLATE_DISPLAY_GROUP = "plate-display"


def broadcast_plate(assignment_label: str, license_plate: str) -> None:
    """
    슬롯 라벨(예: 'A1')에 대해 번호판을 표시하거나 빈값("")으로 지웁니다.
    """
    if not assignment_label:
        return
    payload = {
        "assignment": assignment_label,
        "license_plate": license_plate or "",
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        PLATE_DISPLAY_GROUP,
        {"type": "broadcast", "payload": payload},
    )
