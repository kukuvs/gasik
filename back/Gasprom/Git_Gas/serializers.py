# Git_Gas/serializers.py

from rest_framework import serializers
from .models import SkillUser, User, Project

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
        """
        Проверяем, что оба пароля совпадают.
        """
        if attrs.get('password1') != attrs.get('password2'):
            raise serializers.ValidationError("Пароли не совпадают.")
        return attrs

    def create(self, validated_data):
        """
        Создаем пользователя, устанавливая хешированный пароль.
        """
        validated_data.pop('password2')  # Удаляем подтверждение пароля
        password = validated_data.pop('password1')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProjectSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Project.
    Поля:
        - title: название проекта (до 30 символов)
        - description: описание (до 1000 символов)
        - date_proj: дата проекта
        - url: ссылка на проект
        - main_user: основной пользователь (ID), можно заменить на вложенный сериализатор, если нужно
    """
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'date_proj', 'url', 'main_user')

class SkillUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillUser
        fields = ['user', 'skill']
        
class AddSkillByTitleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=30)
