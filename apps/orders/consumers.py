import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WaiterConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return
        self.user_id = user.id
        self.group_name = f"waiter_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        # Cajeros/admin/manager también escuchan solicitudes de cuenta (estación de caja)
        self.is_cashier_station = getattr(user, "role", None) in ("admin", "manager", "cashier")
        if self.is_cashier_station:
            await self.channel_layer.group_add("cashier_station", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if getattr(self, "is_cashier_station", False):
            await self.channel_layer.group_discard("cashier_station", self.channel_name)

    async def waiter_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "order_id": event["order_id"],
            "table_number": event["table_number"],
            "message": event["message"],
        }))

    async def bill_request(self, event):
        await self.send(text_data=json.dumps({
            "type": "bill_request",
            "order_id": event["order_id"],
            "table_number": event["table_number"],
            "message": event["message"],
        }))
