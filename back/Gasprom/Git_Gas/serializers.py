from rest_framework import serializers
from .models import SkillUser, User, Project, Event, EventUser, Corporation

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    Требует подтверждения пароля.
    """
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone', 'age', 'password1', 'password2')

    def validate(self, attrs):
        if attrs.get('password1') != attrs.get('password2'):
            raise serializers.ValidationError("Пароли не совпадают.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProjectSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Project.
    Поле main_user устанавливается автоматически, поэтому передавать его не надо.
    """
    main_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'date_proj', 'url', 'main_user')


class SkillUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillUser
        fields = ['user', 'skill']


class AddSkillByTitleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=30)


# Сериализатор для событий
class EventSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Event.
    Поле organizer указывает на компанию (его устанавливает только авторизованный представитель компании).
    """
    organizer = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'organizer')


class EventUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя на мероприятие.
    """
    class Meta:
        model = EventUser
        fields = ('user', 'event')
