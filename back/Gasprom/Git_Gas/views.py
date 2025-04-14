from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer,
    ProjectSerializer,
    AddSkillByTitleSerializer,
    EventSerializer,
    EventUserSerializer
)
from .models import User, Project, Skill, SkillUser, Event, EventUser

class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet для работы с пользователями.
    Реализует регистрацию (create), получение JWT (token) и добавление навыков.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def token(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"error": "Email и пароль обязательны."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            })
        return Response({"error": "Неверные учетные данные."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_skill_by_id(self, request):
        skill_id = request.data.get("skill_id")
        if not skill_id:
            return Response({'error': 'Не передан идентификатор навыка'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response({'error': 'Навык не найден'}, status=status.HTTP_404_NOT_FOUND)
        if SkillUser.objects.filter(user=request.user, skill=skill).exists():
            return Response({'message': 'Навык уже добавлен'}, status=status.HTTP_200_OK)
        SkillUser.objects.create(user=request.user, skill=skill)
        return Response({'message': 'Навык добавлен пользователю'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_skill_by_title(self, request):
        serializer = AddSkillByTitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data['title'].strip().capitalize()
        skill, _ = Skill.objects.get_or_create(title=title)
        if SkillUser.objects.filter(user=request.user, skill=skill).exists():
            return Response({'message': f'Навык "{title}" уже добавлен'}, status=status.HTTP_200_OK)
        SkillUser.objects.create(user=request.user, skill=skill)
        return Response({'message': f'Навык "{title}" успешно добавлен'}, status=status.HTTP_201_CREATED)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления проектами (CRUD).
    При создании проекта поле main_user автоматически устанавливается равным request.user.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(main_user=self.request.user)


# Новый ViewSet для мероприятий (Event)
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления событиями.
    Создавать событие может только представительный пользователь компании.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, 'corporation'):
            return Response({"error": "Только компания может создавать мероприятия."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user.corporation)



# APIView для регистрации студента на мероприятие (создание связи EventUser)
class EventRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventUserSerializer(data=request.data)
        if serializer.is_valid():
            # Предполагаем, что студент не может зарегистрироваться несколько раз
            if EventUser.objects.filter(user=request.user, event=serializer.validated_data['event']).exists():
                return Response({'message': 'Вы уже зарегистрированы на это мероприятие.'}, status=status.HTTP_200_OK)
            # Устанавливаем пользователя равным request.user
            serializer.save(user=request.user)
            # Можно добавить логику начисления рейтинговых баллов за регистрацию
            return Response({'message': 'Вы успешно зарегистрированы на мероприятие.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
