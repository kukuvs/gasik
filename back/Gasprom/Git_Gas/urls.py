# Git_Gas/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddSkillByTitleView, UserRegistrationAPIView, obtain_jwt_token, ProjectViewSet,AddSkillToUser

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('api/register/', UserRegistrationAPIView.as_view(), name='api_register'),
    path('api/token/', obtain_jwt_token, name='obtain_jwt_token'),
    path('api/', include(router.urls)),
    path('api/add-skill/', AddSkillToUser.as_view(), name='add-skill'),
    path('api/user/add-skill/', AddSkillByTitleView.as_view(), name='add-skill-by-title'),
]
