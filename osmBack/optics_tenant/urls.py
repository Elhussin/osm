from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from optics_tenant.api.urls import urlpatterns 
# from wagtail.api.v2.views import PagesAPIViewSet
# from wagtail.api.v2.router import WagtailAPIRouter

# # ]
# api_router = WagtailAPIRouter('wagtailapi')
# api_router.register_endpoint('pages', PagesAPIViewSet)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path('api/', include(urlpatterns)),   # api urls
    # path('cms/', include('cms.urls')),  # Include CMS URLs

]
