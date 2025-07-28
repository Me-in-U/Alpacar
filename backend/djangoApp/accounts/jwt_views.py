# accounts/jwt_views.py
from rest_framework_simplejwt.views import TokenViewBase

from .jwt_serializers import EmailTokenObtainPairSerializer


class EmailTokenObtainPairView(TokenViewBase):
    serializer_class = EmailTokenObtainPairSerializer
