"""
URL configuration for djangoApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("icons/favicon.ico"), permanent=True
        ),
    ),
    path("ocr/", include("ocr_app.urls")),
    path("admin/", admin.site.urls),
]
# DEBUG=True 환경에서 STATICFILES_DIRS 를 /static/ URL로 서빙
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )
