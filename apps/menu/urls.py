from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("items/create/", views.item_create, name="item_create"),
    path("items/<int:pk>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path("items/<int:pk>/toggle/", views.item_toggle_available, name="item_toggle"),
    path("86/", views.quick_86, name="quick_86"),
]
