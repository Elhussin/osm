# No login/admin or tenant data routes on the public schema.
from django.urls import path
from .views import live, ready

urlpatterns = [path("health/live/", live), path("health/ready/", ready)]
