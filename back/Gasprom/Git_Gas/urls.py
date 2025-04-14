from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    ProjectViewSet,
    EventViewSet,
    EventRegisterAPIView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/event/register/', EventRegisterAPIView.as_view(), name='event-register'),
]
