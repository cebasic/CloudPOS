import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.orders.models import Order, OrderItem


class KitchenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "kitchen"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        orders = await self.get_active_orders()
        await self.send(text_data=json.dumps({"type": "initial", "orders": orders}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        if action == "update_item_status":
            waiter_id, table_number, item_name = await self.update_item_status(
                data["item_id"], data["status"]
            )
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "kitchen.update", "order_id": data.get("order_id")},
            )
            if data["status"] == "ready" and waiter_id:
                await self.channel_layer.group_send(
                    f"waiter_{waiter_id}",
                    {
                        "type": "waiter.notification",
                        "order_id": data.get("order_id"),
                        "table_number": table_number,
                        "message": f"{table_number}: {item_name} está listo",
                    },
                )

    async def kitchen_update(self, event):
        orders = await self.get_active_orders()
        await self.send(text_data=json.dumps({"type": "update", "orders": orders}))

    @database_sync_to_async
    def get_active_orders(self):
        orders = (
            Order.objects.filter(status__in=["pending", "in_progress", "ready"])
            .select_related("table", "waiter")
            .prefetch_related("items__menu_item")
            .order_by("created_at")
        )
        result = []
        for order in orders:
            items = []
            for item in order.items.select_related("menu_item").all():
                if not item.menu_item.requires_kitchen:
                    continue
                items.append({
                    "id": item.pk,
                    "name": item.menu_item.name,
                    "quantity": item.quantity,
                    "notes": item.notes,
                    "status": item.status,
                    "status_display": item.get_status_display(),
                })
            if not items:
                continue
            result.append({
                "id": order.pk,
                "table_number": order.display_label,
                "label": order.display_label,
                "order_type": order.order_type,
                "waiter": order.waiter.get_full_name() or order.waiter.username,
                "status": order.status,
                "status_display": order.get_status_display(),
                "notes": order.notes,
                "created_at": order.created_at.strftime("%H:%M"),
                "created_at_ts": int(order.created_at.timestamp() * 1000),
                "items": items,
            })
        return result
    @database_sync_to_async
    def update_item_status(self, item_id, status):
        try:
            item = OrderItem.objects.select_related("order__table", "order__waiter", "menu_item").get(pk=item_id)
            if status in dict(OrderItem.Status.choices):
                item.status = status
                item.save(update_fields=["status"])
                item.order.sync_status()
                label = item.order.display_label
                return item.order.waiter_id, label, item.menu_item.name
        except OrderItem.DoesNotExist:
            pass
        return None, None, None
