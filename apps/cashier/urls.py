from django.urls import path
from . import views

app_name = "cashier"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("abrir/", views.session_open, name="session_open"),
    path("corte/", views.cash_cut, name="cash_cut"),
    path("corte/<int:pk>/", views.cut_detail, name="cut_detail"),
    path("historial/", views.history, name="history"),
    path("gasto/", views.expense_create, name="expense_create"),
]
