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
    # 관리자 사이트
    path("admin/", admin.site.urls),
    # favicon 처리
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("icons/favicon.ico"), permanent=True
        ),
    ),
    # 스트리밍 앱 URL (Pi 업로드, 대시보드)
    path("", include("streamapp.urls")),
    # 계정 관리 앱 URL (회원가입, 로그인, 푸시 설정 등)
    path("", include("accounts.urls")),
    # 차량 관리 앱 URL
    path("vehicles/", include("vehicles.urls")),
    # allauth 콜백
    # path("accounts/", include("allauth.urls")),
    # dj‑rest‑auth
    # path("dj-rest-auth/", include("dj_rest_auth.urls")),
    # path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    # path("dj-rest-auth/social/", include("dj_rest_auth.social_urls")),
]
# DEBUG=True 환경에서 STATICFILES_DIRS 를 /static/ URL로 서빙
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )
