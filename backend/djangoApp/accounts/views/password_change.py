from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers.password_change import PasswordChangeSerializer


class PasswordChangeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/auth/password-change/
        { current_password, new_password, new_password2 }
        """
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "비밀번호가 변경되었습니다."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
