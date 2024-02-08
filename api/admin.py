from django.contrib import admin

from api.models import Client, Distribution, Message

admin.site.register(Client)
admin.site.register(Message)


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


admin.site.register(Distribution, DistributionAdmin)
