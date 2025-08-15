# jetson/broadcast.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

JETSON_CONTROL_GROUP = "jetson-control"


def get_user_skill_level(score: int) -> str:
    """
    사용자 점수를 기반으로 실력 레벨을 반환합니다.
    
    Args:
        score: 사용자 점수 (0-100)
        
    Returns:
        str: 실력 레벨 (beginner, intermediate, advanced)
    """
    if score < 40:
        return "beginner"
    elif score < 80:
        return "intermediate"
    else:
        return "advanced"


def send_request_assignment(license_plate: str, size_class: str, user_skill_level: str = None) -> None:
    async_to_sync(get_channel_layer().group_send)(
        JETSON_CONTROL_GROUP,
        {
            "type": "jetson_control",
            "payload": {
                "message_type": "request_assignment",
                "license_plate": license_plate,
                "size_class": size_class,  # compact|midsize|suv
                "user_skill_level": user_skill_level,  # beginner|intermediate|advanced
            },
        },
    )
