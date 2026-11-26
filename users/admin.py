from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from .models import User


@admin.register(User)
class MedixUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Dados MEDIX.AI', {'fields': ('cpf', 'role', 'failed_login_attempts', 'locked_until', 'must_change_password')}),
    )
    list_display = ('username', 'email', 'cpf', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'cpf')
    readonly_fields = UserAdmin.readonly_fields + ('failed_login_attempts', 'locked_until')

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: User | None = None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: User | None = None,
    ) -> bool:
        return False

    def has_view_permission(
        self,
        request: HttpRequest,
        obj: User | None = None,
    ) -> bool:
        return super().has_view_permission(request, obj)
