from django.urls import path
from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_editor, name="editor"),
]
