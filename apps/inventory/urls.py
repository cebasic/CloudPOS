from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.stock_list, name="list"),
    path("nuevo/", views.stock_create, name="create"),
    path("compras/", views.buy_list, name="buy_list"),
    path("compras/csv/", views.buy_list_csv, name="buy_list_csv"),
    path("recetas/", views.recipe_index, name="recipe_index"),
    path("recetas/<int:menu_item_id>/", views.recipe_edit, name="recipe_edit"),
    path("conteo/", views.stock_count, name="count"),
    path("conteo/<int:pk>/", views.stock_count_detail, name="count_detail"),
    path("merma/", views.waste_report_view, name="waste_report"),
    path("<int:pk>/", views.stock_detail, name="detail"),
    path("<int:pk>/editar/", views.stock_edit, name="edit"),
    path("<int:pk>/compra/", views.stock_purchase, name="purchase"),
    path("<int:pk>/ajuste/", views.stock_adjust, name="adjust"),
    path("<int:pk>/merma/", views.stock_waste, name="waste"),
]
