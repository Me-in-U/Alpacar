# accounts/jwt_views.py
from rest_framework_simplejwt.views import TokenObtainPairView

from .jwt_serializers import EmailTokenObtainPairSerializer


class LoginAPI(TokenObtainPairView):
    """
    POST /api/token/  { "email": "...", "password": "..." }
    returns { refresh, access }
    """

    serializer_class = EmailTokenObtainPairSerializer
