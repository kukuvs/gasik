from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Skill, Project, SkillUser, Corporation

class UserRegistrationTestCase(TestCase):
    """Тесты API для регистрации пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "age": 30,
            "password1": "TestPass123",
            "password2": "TestPass123"
        }
        self.user_invalid_data = {
            "email": "invalid@example.com",
            "name": "Invalid User",
            "phone": "1111111111",
            "age": 25,
            "password1": "TestPass123",
            "password2": "WrongPass"
        }

    def test_register_user(self):
        """Успешная регистрация нового пользователя"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_register_user_invalid(self):
        """Регистрация с не совпадающими паролями"""
        response = self.client.post(self.register_url, self.user_invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Пароли не совпадают", str(response.data))

    def test_register_user_duplicate(self):
        """Дублирование регистрации одного и того же email"""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Регистрация с отсутствием обязательных полей"""
        incomplete_data = {
            "email": "new@example.com",
            "password1": "NewPass123",
            "password2": "NewPass123"
        }
        response = self.client.post(self.register_url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email_format(self):
        """Регистрация с некорректным форматом email"""
        invalid_email_data = self.user_data.copy()
        invalid_email_data["email"] = "invalid-email-format"
        response = self.client.post(self.register_url, invalid_email_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", str(response.data).lower())

    def test_register_short_password(self):
        """Регистрация с слишком коротким паролем"""
        short_pass_data = self.user_data.copy()
        short_pass_data["password1"] = "123"
        short_pass_data["password2"] = "123"
        response = self.client.post(self.register_url, short_pass_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", str(response.data).lower())

class UserAuthenticationTestCase(TestCase):
    """Тесты API для получения токена"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
        self.token_url = reverse('user-token')
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "age": 30,
            "password1": "TestPass123",
            "password2": "TestPass123"
        }

    def test_obtain_token_valid(self):
        """Успешное получение JWT токена"""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.token_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password1"]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_obtain_token_invalid(self):
        """Попытка получения токена с неправильными данными"""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.token_url, {
            "email": self.user_data["email"],
            "password": "WrongPassword"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Неверные учетные данные", str(response.data))

    def test_obtain_token_missing_fields(self):
        """Получение токена без обязательных полей"""
        self.client.post(self.register_url, self.user_data, format='json')
        response1 = self.client.post(self.token_url, {"email": self.user_data["email"]}, format='json')
        response2 = self.client.post(self.token_url, {"password": self.user_data["password1"]}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_nonexistent_user(self):
        """Попытка получить токен для несуществующего пользователя"""
        response = self.client.post(self.token_url, {
            "email": "nonexistent@example.com",
            "password": "SomePass123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_empty_payload(self):
        """Попытка получить токен с пустым телом запроса"""
        response = self.client.post(self.token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserSkillManagementTestCase(TestCase):
    """Тесты API для управления навыками пользователя"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
        self.token_url = reverse('user-token')
        self.add_skill_by_id_url = reverse('user-add-skill-by-id')
        self.add_skill_by_title_url = reverse('user-add-skill-by-title')
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "age": 30,
            "password1": "TestPass123",
            "password2": "TestPass123"
        }
        self.skill = Skill.objects.create(title="Python")

    def authenticate(self):
        """Регистрирует и аутентифицирует пользователя, устанавливая заголовок авторизации."""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.token_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password1"]
        }, format='json')
        self.assertIn("access", response.data, f"Ошибка аутентификации. Ответ: {response.data}")
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def test_add_skill_to_user_by_id(self):
        """Добавление навыка по ID"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_id_url, {"skill_id": self.skill.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SkillUser.objects.filter(user__email=self.user_data["email"], skill=self.skill).exists())

    def test_add_skill_to_user_by_id_no_param(self):
        """Попытка добавления навыка по ID без параметра"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_id_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Не передан", str(response.data))

    def test_add_skill_to_user_by_id_duplicate(self):
        """Дублирование добавления навыка по ID"""
        self.authenticate()
        response1 = self.client.post(self.add_skill_by_id_url, {"skill_id": self.skill.id}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        response2 = self.client.post(self.add_skill_by_id_url, {"skill_id": self.skill.id}, format='json')
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_add_skill_to_user_by_id_invalid_id(self):
        """Добавление навыка по несуществующему ID"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_id_url, {"skill_id": 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("не найден", str(response.data).lower())

    def test_add_skill_to_user_by_title(self):
        """Добавление навыка по названию"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_title_url, {"title": "Python"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SkillUser.objects.filter(user__email=self.user_data["email"], skill__title="Python").exists())

    def test_add_skill_to_user_by_title_no_param(self):
        """Добавление навыка по названию без параметра"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_title_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_skill_to_user_by_title_duplicate(self):
        """Дублирование добавления навыка по названию"""
        self.authenticate()
        response1 = self.client.post(self.add_skill_by_title_url, {"title": "Python"}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        response2 = self.client.post(self.add_skill_by_title_url, {"title": "Python"}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn("уже добавлен", str(response2.data))

    def test_add_skill_to_user_by_title_invalid_title(self):
        """Добавление навыка по несуществующему названию в бд"""
        self.authenticate()
        response = self.client.post(self.add_skill_by_title_url, {"title": "NonexistentSkill"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("навык успешно добавлен", str(response.data).lower())

class ProjectManagementTestCase(TestCase):
    """Тесты API для управления проектами"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
        self.token_url = reverse('user-token')
        self.projects_url = reverse('project-list')
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "age": 30,
            "password1": "TestPass123",
            "password2": "TestPass123"
        }
        self.dummy_user = User.objects.create(
            email="dummy@example.com",
            name="Dummy User",
            phone="0000000000",
            age=25
        )
        self.dummy_user.set_password("dummyPass123")
        self.dummy_user.save()

    def authenticate(self):
        """Регистрирует и аутентифицирует пользователя, устанавливая заголовок авторизации."""
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.token_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password1"]
        }, format='json')
        self.assertIn("access", response.data, f"Ошибка аутентификации. Ответ: {response.data}")
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def test_project_crud_operations(self):
        """Проверка полного цикла работы с проектом: создание, получение, обновление, удаление"""
        self.authenticate()
        project_data = {
            "title": "New Test Project",
            "description": "Описание нового проекта",
            "date_proj": "2023-11-01",
            "url": "http://newexample.com"
        }
        # Создание проекта
        response_create = self.client.post(self.projects_url, project_data, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        project_id = response_create.data.get('id')
        detail_url = reverse('project-detail', kwargs={'pk': project_id})

        # Получение деталей проекта
        response_retrieve = self.client.get(detail_url, format='json')
        self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)
        self.assertEqual(response_retrieve.data.get('title'), project_data['title'])

        # Обновление проекта
        update_data = {"description": "Обновленное описание"}
        response_update = self.client.patch(detail_url, update_data, format='json')
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)
        self.assertEqual(response_update.data.get('description'), update_data['description'])

        # Удаление проекта
        response_delete = self.client.delete(detail_url, format='json')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_project_create_missing_fields(self):
        """Создание проекта с отсутствием обязательных полей"""
        self.authenticate()
        incomplete_data = {
            "title": "Incomplete Project"
            # отсутствуют description, date_proj, url
        }
        response = self.client.post(self.projects_url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_create_invalid_date(self):
        """Создание проекта с некорректным форматом даты"""
        self.authenticate()
        invalid_date_data = {
            "title": "Project with invalid date",
            "description": "Desc",
            "date_proj": "invalid-date",
            "url": "http://example.com"
        }
        response = self.client.post(self.projects_url, invalid_date_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", str(response.data).lower())

    def test_project_list_view(self):
        """Проверка GET запроса на список проектов"""
        # Создаём дополнительные проекты для dummy-пользователя
        Project.objects.create(
            title="Project 1", description="Desc 1", date_proj="2023-10-02",
            url="http://p1.com", main_user=self.dummy_user
        )
        Project.objects.create(
            title="Project 2", description="Desc 2", date_proj="2023-10-03",
            url="http://p2.com", main_user=self.dummy_user
        )
        self.authenticate()
        response = self.client.get(self.projects_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_project_update_unauthorized(self):
        """Попытка обновления проекта без авторизации"""
        project = Project.objects.create(
            title="Project Unauthorized", description="Desc", date_proj="2023-10-05",
            url="http://unauth.com", main_user=self.dummy_user
        )
        detail_url = reverse('project-detail', kwargs={'pk': project.id})
        update_data = {"description": "Изменено"}
        response = self.client.patch(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_project_delete_unauthorized(self):
        """Попытка удаления проекта без авторизации"""
        project = Project.objects.create(
            title="Project Unauthorized", description="Desc", date_proj="2023-10-05",
            url="http://unauth.com", main_user=self.dummy_user
        )
        detail_url = reverse('project-detail', kwargs={'pk': project.id})
        response = self.client.delete(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_project_detail_not_found(self):
        """Запрос деталей несуществующего проекта"""
        self.authenticate()
        detail_url = reverse('project-detail', kwargs={'pk': 9999})
        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_update_invalid_field(self):
        """Попытка обновления проекта с некорректным полем"""
        self.authenticate()
        project = Project.objects.create(
            title="Project Update Invalid", description="Desc", date_proj="2023-10-06",
            url="http://valid.com", main_user=self.dummy_user
        )
        detail_url = reverse('project-detail', kwargs={'pk': project.id})
        update_data = {"nonexistent_field": "value"}
        response = self.client.patch(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class EventManagementTestCase(TestCase):
    """Тесты API для управления мероприятиями"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
        self.token_url = reverse('user-token')
        self.events_url = reverse('event-list')
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "age": 30,
            "password1": "TestPass123",
            "password2": "TestPass123"
        }
        self.company_user_data = {
            "email": "company@example.com",
            "name": "Company User",
            "phone": "9999999999",
            "age": 40,
            "password1": "CompanyPass123",
            "password2": "CompanyPass123"
        }
        self.company = Corporation.objects.create(
            name="Газпром",
            description="Крупная энергетическая компания",
            email="corp@gazprom.ru",
            password="CorpPass123"
        )

    def authenticate(self, data=None):
        """Регистрирует и аутентифицирует пользователя, устанавливая заголовок авторизации."""
        user_payload = data if data else self.user_data
        self.client.post(self.register_url, user_payload, format='json')
        response = self.client.post(self.token_url, {
            "email": user_payload["email"],
            "password": user_payload["password1"]
        }, format='json')
        self.assertIn("access", response.data, f"Ошибка аутентификации. Ответ: {response.data}")
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return token

    def test_event_list_view_unauthorized(self):
        """Попытка получения списка мероприятий без авторизации"""
        response = self.client.get(self.events_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_event_create_unauthorized(self):
        """Попытка создать мероприятие без авторизации"""
        event_data = {
            "title": "Hackathon",
            "description": "Описание мероприятия",
            "start": "2023-12-01",
            "end": "2023-12-02"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_event_create_not_company(self):
        """Обычный пользователь (не компания) не может создать мероприятие"""
        self.authenticate()
        event_data = {
            "title": "Hackathon",
            "description": "Описание мероприятия",
            "start": "2023-12-01",
            "end": "2023-12-02"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_event_create_missing_fields(self):
        """Создание мероприятия с отсутствием обязательных полей"""
        self.authenticate(data=self.company_user_data)
        incomplete_event = {
            "title": "Incomplete Event"
            # отсутствуют description, start, end
        }
        response = self.client.post(self.events_url, incomplete_event, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_create_with_extra_fields(self):
        """Создание мероприятия с лишними полями"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "Extra Fields Event",
            "description": "Описание с лишними полями",
            "start": "2023-12-10",
            "end": "2023-12-11",
            "unexpected_field": "unexpected_value",
            "another_one": 12345
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_create_with_invalid_dates(self):
        """Создание мероприятия с некорректными датами (start позже end)"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "Invalid Dates Event",
            "description": "Описание с некорректными датами",
            "start": "2023-12-15",
            "end": "2023-12-10"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_create_with_invalid_date_format(self):
        """Создание мероприятия с неправильным форматом даты"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "Bad Date Format Event",
            "description": "Описание с неправильным форматом даты",
            "start": "15-12-2023",
            "end": "16-12-2023"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_create_with_empty_strings(self):
        """Создание мероприятия с пустыми строками в обязательных полях"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "",
            "description": "",
            "start": "",
            "end": ""
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_create_with_sql_injection_attempt(self):
        """Попытка SQL-инъекции в полях создания мероприятия"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "Hackathon'); DROP TABLE events;--",
            "description": "Описание с SQL инъекцией",
            "start": "2023-12-01",
            "end": "2023-12-02"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        # Ожидаем, что сервер не упадет и вернет ошибку валидации или успешный ответ без вреда
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_event_create_with_xss_attempt(self):
        """Попытка XSS-атаки в полях создания мероприятия"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": "<script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>",
            "start": "2023-12-01",
            "end": "2023-12-02"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        # Проверяем, что сервер не падает и корректно обрабатывает ввод
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_event_create_with_very_long_strings(self):
        """Создание мероприятия с очень длинными строками в полях"""
        self.authenticate(data=self.company_user_data)
        long_string = "a" * 10000
        event_data = {
            "title": long_string,
            "description": long_string,
            "start": "2023-12-01",
            "end": "2023-12-02"
        }
        response = self.client.post(self.events_url, event_data, format='json')
        # Ожидаем либо успешное создание, либо ошибку из-за длины
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_event_create_with_null_fields(self):
        """Создание мероприятия с null в обязательных полях"""
        self.authenticate(data=self.company_user_data)
        event_data = {
            "title": None,
            "description": None,
            "start": None,
            "end": None
        }
        response = self.client.post(self.events_url, event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
