# jetson/broadcast.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

JETSON_CONTROL_GROUP = "jetson-control"


def send_request_assignment(license_plate: str, size_class: str) -> None:
    async_to_sync(get_channel_layer().group_send)(
        JETSON_CONTROL_GROUP,
        {
            "type": "jetson_control",
            "payload": {
                "message_type": "request_assignment",
                "license_plate": license_plate,
                "size_class": size_class,  # compact|midsize|suv
            },
        },
    )
