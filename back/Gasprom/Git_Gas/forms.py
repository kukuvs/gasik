from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User

class UserCreationForm(forms.ModelForm):
    """Форма для создания нового пользователя с паролем"""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone', 'age', 'corporation')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Форма для изменения пользователя в админке"""
    password = ReadOnlyPasswordHashField(label="Пароль",
        help_text="Пароль не отображается, но вы можете изменить его через форму изменения пароля.")

    class Meta:
        model = User
        fields = ('email', 'password', 'name', 'phone', 'age', 'corporation', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        return self.initial["password"]
