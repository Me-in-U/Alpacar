# ocr_app/urls.py
from django.urls import path

from .views import index

urlpatterns = [
    path("test/", index, name="index"),
    # path("annot_stream/", annot_stream, name="annot_stream"),
]
