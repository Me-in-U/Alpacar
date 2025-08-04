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
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",  # 원하는 제목 작성
        default_version="v1",  # 애플리케이션의 버전
        description="Alpacar API",  # 설명
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@ios.kr"),
        license=openapi.License(name="BSD License"),
    ),
    permission_classes=(permissions.AllowAny,),
    public=True,
)
# ——— API 전용 URL 패턴 묶음 ——————————————
api_patterns = [
    # REST framework 세션 로그인/로그아웃 (Swagger 세션 로그인 용)
    path("api-auth/", include("rest_framework.urls")),
    # allauth 콜백
    path("accounts/", include("allauth.urls")),
    # 계정 관리
    path("", include("accounts.urls")),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    # 차량 관리
    path("", include("vehicles.urls")),
    # 스트리밍 앱 (Pi 업로드, 대시보드)
    path("", include("streamapp.urls")),
    # Swagger / OpenAPI
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

urlpatterns = [
    # 관리자 사이트를 /api/admin/로 옮기고 싶다면 여기서 조정
    path("api/admin/", admin.site.urls),
    # favicon (static 파일) — 이건 /favicon.ico로 그대로 두셔도 좋습니다
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("icons/favicon.ico"), permanent=True
        ),
    ),
    path("api/", include(api_patterns)),
]
# DEBUG=True 환경에서 STATICFILES_DIRS 를 /static/ URL로 서빙
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )
