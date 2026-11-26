from django.contrib import admin

from .models import AdministrativeAction, AuditQuery, LoginAttempt


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'role', 'result', 'identifier_fingerprint')
    list_filter = ('role', 'result', 'occurred_at')
    search_fields = ('identifier_fingerprint',)
    date_hierarchy = 'occurred_at'
    readonly_fields = ('user', 'identifier_fingerprint', 'role', 'result', 'occurred_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditQuery)
class AuditQueryAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'actor', 'ip_address', 'role_filter', 'result_filter')
    list_filter = ('role_filter', 'result_filter', 'occurred_at')
    date_hierarchy = 'occurred_at'
    list_select_related = ('actor',)
    readonly_fields = (
        'actor',
        'ip_address',
        'identifier_fingerprint',
        'role_filter',
        'result_filter',
        'occurred_from',
        'occurred_until',
        'occurred_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdministrativeAction)
class AdministrativeActionAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'actor', 'target', 'action', 'ip_address')
    list_filter = ('action', 'occurred_at')
    search_fields = ('actor__email', 'target__email')
    date_hierarchy = 'occurred_at'
    list_select_related = ('actor', 'target')
    readonly_fields = ('actor', 'target', 'action', 'ip_address', 'occurred_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
