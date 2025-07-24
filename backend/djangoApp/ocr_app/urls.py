# ocr_app/urls.py
from django.urls import path

from .views import annot_stream, index

urlpatterns = [
    path("", index, name="index"),
    path("annot_stream/", annot_stream, name="annot_stream"),
]
