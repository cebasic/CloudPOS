from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("create/", views.order_create, name="create"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/add-item/", views.order_add_item, name="add_item"),
    path("<int:pk>/remove-item/<int:item_pk>/", views.order_remove_item, name="remove_item"),
    path("<int:pk>/status/", views.order_update_status, name="update_status"),
    path("<int:pk>/checkout/", views.order_checkout, name="checkout"),
    path("<int:pk>/receipt/", views.order_receipt, name="receipt"),
    path("<int:pk>/item/<int:item_pk>/status/", views.order_item_status, name="item_status"),
]
