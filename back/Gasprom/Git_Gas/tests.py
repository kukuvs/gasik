from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Skill


class UserSkillTestCase(TestCase):
    """Тесты API: регистрация, логин, добавление навыков"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('api_register')
        self.token_url = reverse('obtain_jwt_token')
        self.add_skill_by_id_url = reverse('add-skill')
        self.add_skill_by_title_url = reverse('add-skill-by-title')

        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "TestPass123"
        }

        self.skill = Skill.objects.create(title="Python")

    def authenticate(self):
        """Регистрирует и логинит пользователя, возвращает токен"""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.token_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }, format='json')
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def test_register_user(self):
        """Тест регистрации пользователя"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_add_skill_to_user_by_id(self):
        """Добавление навыка по ID"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_id_url, {"skill_id": self.skill.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_skill_to_user_by_title(self):
        """Добавление навыка по названию"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_title_url, {"title": "Python"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
