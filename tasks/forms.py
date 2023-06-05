from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User

from .models import *


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.CharField(label='Почта', widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-input'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-input'}),
        }


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class ValidateAnswer(forms.Form):
    answer = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Введите найденный флаг сюда'}))
    task_id = forms.IntegerField(label='', widget=forms.TextInput(attrs={'class': 'hidden'}))


class CreateTeam(forms.ModelForm):
    name = forms.CharField(label='Название команды', widget=forms.TextInput(attrs={'class': 'form-input'}))
    url = forms.URLField(required=False, label='Веб-ресурс команды', widget=forms.TextInput(attrs={'class': 'form-input'}))
    is_open = forms.BooleanField(label='Открыть вступление в команду?', initial=True, required=False)

    class Meta:
        model = Teams
        fields = ('name', 'url', 'is_open')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'url': forms.URLInput(attrs={'class': 'form-input'}),
            'is_open': forms.BooleanField(),
        }


class JoinTeam(forms.Form):
    team_id = forms.CharField()


class CTFRegistration(forms.Form):
    ctf_id = forms.CharField(required=False)
    user_id = forms.CharField(required=False)


class LeaveTeam(forms.Form):
    user_id = forms.CharField()


class ChooseUserFromTeam(forms.Form):
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        profile = Profile.objects.get(user_id=user_id)
        team = Teams.objects.get(pk=profile.team_id)
        cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)
        super(ChooseUserFromTeam, self).__init__(*args, **kwargs)
        if user_id:
            self.fields['user'].queryset = User.objects.filter(id__in=Profile.objects.filter(team_id=team.id).values('user_id')).exclude(id=cpt.id)

    user = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=False), label='Выберите пользователя из списка')