from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('django-admin/', admin.site.urls),  # لوحة تحكم Django الافتراضية
    path('admin/', include('wagtail.admin.urls')),  # لوحة تحكم Wagtail
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
