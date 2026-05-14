from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.reservation_list, name="list"),
    path("nueva/", views.reservation_create, name="create"),
    path("<int:pk>/editar/", views.reservation_edit, name="edit"),
    path("<int:pk>/estado/", views.reservation_status, name="status"),
]
