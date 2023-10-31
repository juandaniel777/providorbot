from django.urls import path
from .views import MessageView, PingView,WhatsAppMessageView

urlpatterns = [
    path('ping', PingView.as_view(), name='ping'),
    path('whatsapp/message', MessageView.as_view(), name='whatsapp message'),
    path('whatsapp/test', WhatsAppMessageView.as_view(), name='whatsapp test'),
    # path('get_recommendations/', GetRecommendationsView.as_view(), name='get_recommendations'),
]