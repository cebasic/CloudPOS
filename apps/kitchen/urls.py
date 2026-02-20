from django.urls import path
from . import views

app_name = "kitchen"

urlpatterns = [
    path("", views.kitchen_display, name="display"),
    path("debug/", views.kitchen_debug, name="debug"),
]
