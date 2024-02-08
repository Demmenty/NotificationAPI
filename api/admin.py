from django.contrib import admin

from api.models import Client, Distribution, Message


class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "phone_number",
        "operator_code",
        "tag",
        "timezone",
    )
    search_fields = ("operator_code", "tag", "phone_number")


class DistributionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "start_datetime",
        "end_datetime",
        "message_text",
        "client_filter_operator_code",
        "client_filter_tag",
    )
    list_filter = ("client_filter_operator_code", "client_filter_tag")
    search_fields = ("message_text",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "start_datetime",
                    "end_datetime",
                    "message_text",
                    "client_filter_operator_code",
                    "client_filter_tag",
                ),
            },
        ),
        (
            "Статистика",
            {
                "fields": ("total_messages", "sent_messages", "not_sent_messages"),
            },
        ),
    )

    readonly_fields = (
        "total_messages",
        "sent_messages",
        "not_sent_messages",
    )

    def not_sent_messages(self, obj):
        return obj.total_messages - obj.sent_messages


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "created_at",
        "status",
        "distribution",
        "client",
    )
    list_filter = ("status",)
    search_fields = ("distribution__message_text", "client__phone_number")


admin.site.register(Client, ClientAdmin)
admin.site.register(Distribution, DistributionAdmin)
admin.site.register(Message, MessageAdmin)
