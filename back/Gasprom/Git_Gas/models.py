# Get_Gas/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import Q, F, CheckConstraint


class UserManager(BaseUserManager):
    """
    Менеджер для кастомной модели пользователя, который обеспечивает создание
    обычного пользователя и суперпользователя.
    """
    def create_user(self, email: str, password: str = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if not password:
            raise ValueError("Пароль обязателен")
        user.set_password(password)  # Устанавливает и хеширует пароль
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields) -> "User":
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя.
    
    Поля:
    - name: имя пользователя (до 100 символов)
    - phone: номер телефона (до 20 символов, проверка на допустимые символы)
    - email: почта, используется как логин (до 250 символов, уникальное)
    - age: возраст (целое число, до 2-х цифр)
    - rating: рейтинг (целое число, до 5 цифр)
    - notifications: получать уведомления
    - date_joined: дата регистрации
    """
    name = models.CharField("Имя", max_length=100)

    corporation = models.ForeignKey(
        'Corporation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Компания"
    )
    
    phone = models.CharField(
        "Телефон", 
        max_length=20, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\-]+',
                message="Телефон должен содержать цифры, символы '+' и '-'"
            )
        ]
    )

    email = models.EmailField("Email", max_length=250, unique=True)
    age = models.PositiveSmallIntegerField(
        "Возраст", 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(99)]
    )
    rating = models.PositiveIntegerField(
        "Рейтинг", 
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(99999)]
    )
    notifications = models.BooleanField("Уведомления", default=True)
    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)

    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Администратор", default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        indexes = [
            models.Index(fields=['email'], name='user_email_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.email} - {self.name}"


class Skill(models.Model):
    """
    Модель навыка пользователя.
    
    Поля:
    - title: название навыка (до 30 символов, уникальное)
    """
    title = models.CharField("Название навыка", max_length=30, unique=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        indexes = [
            models.Index(fields=['title'], name='skill_title_idx'),
        ]

    def __str__(self) -> str:
        return self.title


class SkillUser(models.Model):
    """
    Промежуточная модель для связи пользователей и навыков.
    
    Поля:
    - user: ссылка на модель User
    - skill: ссылка на модель Skill
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, verbose_name="Навык")

    class Meta:
        verbose_name = "Связь Навык/Пользователь"
        verbose_name_plural = "Навыки пользователей"
        unique_together = ('user', 'skill')
        indexes = [
            models.Index(fields=['user', 'skill'], name='user_skill_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.skill.title}"


class Event(models.Model):
    """
    Модель события.
    
    Поля:
    - title: название события (до 100 символов)
    - description: описание события (до 2000 символов)
    - start: дата начала
    - end: дата окончания
    - organizer: компания, организующая мероприятие (только Corporation)
    - users: участники события (связь через промежуточную модель EventUser)
    """
    title = models.CharField("Название события", max_length=100)
    description = models.TextField("Описание", max_length=2000)
    start = models.DateField("Дата начала")
    end = models.DateField("Дата окончания")
    organizer = models.ForeignKey(
        'Corporation',
        on_delete=models.CASCADE,
        verbose_name="Организатор"
    )
    users = models.ManyToManyField(
        User, 
        through='EventUser', 
        related_name='events', 
        verbose_name="Участники"
    )

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        constraints = [
            CheckConstraint(check=Q(start__lt=F('end')), name='start_before_end')
        ]
        indexes = [
            models.Index(fields=['start', 'end'], name='event_date_idx'),
        ]

    def __str__(self) -> str:
        return self.title


class EventUser(models.Model):
    """
    Промежуточная модель для связи пользователей и событий.
    
    Поля:
    - user: ссылка на модель User (участник события)
    - event: ссылка на модель Event
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Событие")

    class Meta:
        verbose_name = "Связь Событие/Пользователь"
        verbose_name_plural = "Участники событий"
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['user', 'event'], name='user_event_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.event.title}"




class Project(models.Model):
    """
    Модель проекта.
    
    Поля:
    - title: название проекта (до 30 символов)
    - description: описание проекта (до 1000 символов)
    - date_proj: дата проекта
    - url: ссылка на проект (до 255 символов)
    - main_user: основной пользователь (автор проекта)
    - users: участники проекта (связь через промежуточную модель ProjectUser)
    """
    title = models.CharField("Название проекта", max_length=30)
    description = models.TextField("Описание", max_length=1000)
    date_proj = models.DateField("Дата проекта")
    url = models.URLField("Ссылка", max_length=255)
    main_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_projects', 
        verbose_name="Основной пользователь"
    )
    users = models.ManyToManyField(
        User, 
        through='ProjectUser', 
        related_name='projects', 
        verbose_name="Участники проекта"
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        indexes = [
            models.Index(fields=['title'], name='project_title_idx'),
        ]

    def __str__(self) -> str:
        return self.title


class ProjectUser(models.Model):
    """
    Промежуточная модель для связи пользователей и проектов.
    
    Поля:
    - user: ссылка на модель User
    - project: ссылка на модель Project
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Проект")

    class Meta:
        verbose_name = "Связь Проект/Пользователь"
        verbose_name_plural = "Участники проектов"
        unique_together = ('user', 'project')
        indexes = [
            models.Index(fields=['user', 'project'], name='user_project_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.project.title}"


class Corporation(models.Model):
    """
    Модель компании.
    
    Поля:
    - name: название компании (уникальное)
    - description: описание компании
    - email: почта компании (уникальное)
    - password: хешированный пароль
    """
    name = models.CharField("Название компании", max_length=255, unique=True)
    description = models.TextField("Описание")
    email = models.EmailField("Email", unique=True)
    password = models.CharField("Пароль", max_length=128)

    class Meta:
        verbose_name = "Корпорация"
        verbose_name_plural = "Корпорации"
        indexes = [
            models.Index(fields=['name'], name='corp_name_idx'),
        ]

    def __str__(self) -> str:
        return self.name