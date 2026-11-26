from django.contrib import admin

from .models import NotificationOutbox


@admin.register(NotificationOutbox)
class NotificationOutboxAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'channel', 'recipient', 'status', 'event_key')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('event_key', 'recipient__email')
    readonly_fields = (
        'id',
        'event_key',
        'recipient',
        'channel',
        'subject',
        'body',
        'status',
        'created_at',
        'sent_at',
    )
    list_select_related = ('recipient',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
