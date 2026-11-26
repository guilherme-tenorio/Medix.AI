from django.contrib import admin

from .models import (
    ChatAttachment,
    ChatMessage,
    ChatSession,
    ClinicalOutcome,
    ClinicalQueueItem,
)


@admin.register(ClinicalQueueItem)
class ClinicalQueueItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'queue_type', 'risk_color', 'status', 'assigned_professional', 'enqueued_at')
    list_filter = ('queue_type', 'risk_color', 'status')
    readonly_fields = (
        'id',
        'triage_session',
        'queue_type',
        'risk_color',
        'priority_rank',
        'status',
        'assigned_professional',
        'enqueued_at',
        'accepted_at',
        'finished_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'professional', 'is_closed', 'created_at', 'closed_at')
    list_filter = ('is_closed',)
    readonly_fields = ('id', 'queue_item', 'triage_session', 'professional', 'is_closed', 'closed_at', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'is_from_audio_transcription', 'created_at', 'read_at')
    readonly_fields = ('id', 'session', 'sender', 'content', 'is_from_audio_transcription', 'delivered_at', 'read_at', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'original_name', 'content_type', 'size_bytes', 'uploaded_at')
    readonly_fields = ('id', 'message', 'file', 'original_name', 'content_type', 'size_bytes', 'uploaded_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClinicalOutcome)
class ClinicalOutcomeAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_session', 'outcome_type', 'reclassified_to_red', 'recorded_by', 'created_at')
    readonly_fields = ('id', 'chat_session', 'outcome_type', 'summary_and_conduct', 'warning_signs', 'reclassified_to_red', 'recorded_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
