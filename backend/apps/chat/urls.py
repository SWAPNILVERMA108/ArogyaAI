from django.urls import path

from .views import (
    ChatMessageView,
    ConversationCollectionView,
    ConversationDetailView,
    ConversationMessagesView,
)


app_name = "chat"

urlpatterns = [
    path("message/", ChatMessageView.as_view(), name="message"),
    path("conversations/", ConversationCollectionView.as_view(), name="conversations"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<int:pk>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]
