# Git_Gas/views.py

from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .serializers import AddSkillByTitleSerializer, UserRegistrationSerializer, ProjectSerializer, SkillUserSerializer
from .models import Project, Skill, SkillUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import json

class UserRegistrationAPIView(generics.CreateAPIView):
    """
    API для регистрации пользователя.
    При успешном создании возвращает данные нового пользователя.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_jwt_token(request):
    """
    API для получения JWT токенов.
    Ожидает JSON с email и password.
    """
    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return Response({"error": "Email и пароль обязательны."}, status=status.HTTP_400_BAD_REQUEST)
    except json.JSONDecodeError:
        return Response({"error": "Некорректный JSON"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, email=email, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })
    return Response({"error": "Неверные учетные данные."}, status=status.HTTP_401_UNAUTHORIZED)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления проектами.
    Позволяет создавать, читать, обновлять и удалять проекты.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

class AddSkillToUser(APIView):
    """
    Добавление скилла пользователю
    """
    def post(self, request):
        serializer = SkillUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Навык добавлен пользователю'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AddSkillByTitleView(APIView):
    """
    Добавление пользователю навыка по названию (через JWT)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddSkillByTitleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        title = serializer.validated_data['title'].strip().capitalize()
        user = request.user

        skill, _ = Skill.objects.get_or_create(title=title)

        if SkillUser.objects.filter(user=user, skill=skill).exists():
            return Response({'message': f'Навык "{title}" уже добавлен'}, status=status.HTTP_200_OK)
        
        SkillUser.objects.create(user=user, skill=skill)
        return Response({'message': f'Навык "{title}" успешно добавлен'}, status=status.HTTP_201_CREATED)