from django.urls import path

from .views import (
    AcceptQueueItemView,
    ChatAiAssistView,
    ChatMessagesPollView,
    ChatRoomView,
    CloseChatSessionView,
    MedicalQueueDashboardView,
)

app_name = 'care'

urlpatterns = [
    path('medico/fila/', MedicalQueueDashboardView.as_view(), name='queue_dashboard'),
    path('medico/fila/<uuid:queue_item_id>/aceitar/', AcceptQueueItemView.as_view(), name='accept_queue_item'),
    path('chat/<uuid:session_id>/', ChatRoomView.as_view(), name='chat_room'),
    path('chat/<uuid:session_id>/mensagens/', ChatMessagesPollView.as_view(), name='chat_messages_poll'),
    path('chat/<uuid:session_id>/ia/', ChatAiAssistView.as_view(), name='chat_ai_assist'),
    path('chat/<uuid:session_id>/encerrar/', CloseChatSessionView.as_view(), name='close_chat'),
]
