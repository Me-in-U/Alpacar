# streamapp\urls.py
from django.urls import path

from . import views

urlpatterns = [
    # Raspberry Pi → POST 이미지/텍스트 업로드
    path("api/frame/", views.upload_frame, name="upload-frame"),
]
