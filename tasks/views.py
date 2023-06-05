import datetime

from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordChangeDoneView
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.utils import timezone
from django.db.models import Sum

from tasks.forms import RegisterUserForm, LoginUserForm, ValidateAnswer, CreateTeam, CTFRegistration, LeaveTeam, ChooseUserFromTeam
from tasks.models import Categories, Teams, Profile, Tasks, Attach, Competition, CompeteTasks, Stats, \
    CompeteRegistration
from tasks.utils import DataMixin


# Create your views here.

DEFAULT_TEAM_ID = 1
DEFAULT_CTF_ID = 1


def index(request):
    return render(request, 'tasks/index.html', {'title': 'Главная страница'})


def ctfs(request):
    outdated = Competition.objects.filter(end_date__lte=timezone.now(), is_hidden=False)
    running = Competition.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(), is_hidden=False)
    incoming = Competition.objects.filter(start_date__gte=timezone.now(), is_hidden=False)

    for out in outdated:
        out.reg = len(CompeteRegistration.objects.filter(ctf_id=out.id))
    for run in running:
        run.reg = len(CompeteRegistration.objects.filter(ctf_id=run.id))
    for inc in incoming:
        inc.reg = len(CompeteRegistration.objects.filter(ctf_id=inc.id))

    reg_list = []
    if request.user.is_authenticated:
        user_id = User.objects.get(pk=request.user.id).id
        reg_ctf_list = CompeteRegistration.objects.filter(user_id=user_id)
        for ctf in reg_ctf_list:
            reg_list.append(ctf.ctf_id)

    return render(request, 'tasks/ctfs.html', {'title': 'CTF', 'outdated': outdated, 'running': running,
                                               'incoming': incoming, 'reg_list': reg_list,})


def reg_ctf(request, slug):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})

    form = CTFRegistration()
    ctf = Competition.objects.get(slug=slug)
    user = User.objects.get(pk=request.user.id)
    profile = Profile.objects.get(pk=request.user.id)
    if Competition.objects.filter(end_date__lte=timezone.now(), id=ctf.id).count() > 0:
        return render(request, 'tasks/error.html', {'title': 'Нельзя зарегистрироваться на завершенное CTF!'})

    if ctf.compete_type_id == 1 and profile.team_id == DEFAULT_TEAM_ID:
        print(123)
        err = "Для участия в командном CTF необходимо создать или вступить в команду!"
        return render(request, 'tasks/reg_ctf.html', {'title': 'Регистрация на CTF', 'error': err})
    err = False

    def add_reg(user_id, ctf_id):
        new_stat = CompeteRegistration(user_id=user_id, ctf_id=ctf_id)
        new_stat.save()

    if request.method == 'POST':
        form = CTFRegistration(request.POST)
        if form.is_valid():
            if ctf.compete_type == 1 and profile.team_id == DEFAULT_TEAM_ID:
                err = "Для участия в командном CTF необходимо создать или вступить в команду!"
                return render(request, 'tasks/reg_ctf.html', {'title': 'Регистрация на CTF', 'error': err})

            is_reg = CompeteRegistration.objects.filter(user_id=user.id, ctf_id=ctf.id)
            if not is_reg:
                add_reg(user.id, ctf.id)
                return redirect('ctfs')
            else:
                err = "Вы уже зарегистрированы на это соревнование!"
        else:
            form = CTFRegistration()
    return render(request, 'tasks/reg_ctf.html', {'title': 'Регистрация на CTF', 'ctf_name': ctf.name, 'username': user.username, 'error': err})


class CatList(ListView):
    model = Categories
    template_name = "tasks/categories.html"
    context_object_name = "cats"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Архив заданий"
        return context

    def get_queryset(self):
        not_hidden = Tasks.objects.filter(is_hidden=False).values('cat_id').distinct()
        cats = []
        for cat in not_hidden:
            cats.append(Categories.objects.get(pk=cat['cat_id']))
            cats[-1].cat_logo = cats[-1].cat_logo.split(sep='\\')[-1]
        return cats


class TeamsList(ListView):
    model = Teams
    template_name = "tasks/teams.html"
    context_object_name = "teams"
    extra_context = {}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        def has_team(user_id):
            """Функция, проверяющая, есть ли у пользователя команда"""
            if self.request.user.is_authenticated:
                user = Profile.objects.get(user_id=user_id)
                if user.team_id is None or user.team_id == DEFAULT_TEAM_ID:
                    return False
            return True

        context['has_team'] = has_team(self.request.user)
        context['title'] = "Команды"
        return context

    def get_queryset(self):
        return Teams.objects.filter(is_hidden=False)


def add_team(request):
    def has_team(user_id):
        if request.user.is_authenticated:
            user = Profile.objects.get(user_id=user_id)
            if user.team_id != DEFAULT_TEAM_ID or user.team_id is not None:
                return False
            return True
    user_has_team = has_team(request.user.id)

    if request.method == 'POST' and request.user.is_authenticated and not user_has_team:
            form = CreateTeam(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                url = form.cleaned_data['url']
                cpt_id = request.user.id
                is_open = form.cleaned_data['is_open']
                new_team = Teams(name=name, url=url, cpt_id=cpt_id, is_open=is_open)
                new_team.save()
                user = Profile.objects.get(user_id=request.user.id)
                user.team_id = Teams.objects.get(name=name).id
                user.save()
                return redirect('teams')
    else:
        form = CreateTeam()

    return render(request, 'tasks/add_team.html', {'title': 'Создание команды', 'form': form, 'has_team': user_has_team})


def show_challenges(request, slug):
    cat_id = Categories.objects.get(slug=slug).id
    tasks = get_list_or_404(Tasks, cat_id=cat_id)
    for task in tasks:
        task.attach = Attach.objects.filter(task_id=task.id)
        task.solved_times = Stats.objects.filter(task_id=task.id, is_correct=True).count()
    cat_name = Categories.objects.get(id=cat_id).name

    solved_tasks = []

    if request.user.is_authenticated:
        solved_tasks_list = Stats.objects.filter(is_correct=True, user=request.user)

        for task in solved_tasks_list:
            solved_tasks.append(task.task_id)

    def is_ans_valid(answer, task_id):
        if answer == Tasks.objects.get(pk=task_id).answer:
            return True
        return False

    def add_stats(answer, task_id):
        is_correct = is_ans_valid(answer, task_id)
        compete = Competition.objects.get(id=DEFAULT_CTF_ID)
        team = Profile.objects.get(user_id=request.user.id).team_id
        if team:
            team_res = team
        else:
            team_res = None
        task = Tasks.objects.get(pk=task_id)
        points = Tasks.objects.get(pk=task_id).score
        new_stat = Stats(user=request.user, task=task, compete=compete, team=None, is_correct=is_correct, points=points)
        new_stat.save()

    if request.method == 'POST':
        form = ValidateAnswer(request.POST)
        if form.is_valid():
            if form.cleaned_data['task_id'] not in solved_tasks:
                add_stats(**form.cleaned_data)
                solved_tasks.append(form.cleaned_data['task_id'])
                return redirect('/challenges/' + slug + '/')
    else:
        form = ValidateAnswer()
    return render(request, 'tasks/category.html', {'title': cat_name, 'tasks': tasks, 'form': form, 'solved_tasks': solved_tasks})


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'tasks/register.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Регистрация")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'tasks/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Авторизация")
        return dict(list(context.items()) + list(c_def.items()))

    def get_success_url(self):
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return redirect('home')


def show_ctf(request, slug):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    sl = slug
    ctf_id = get_object_or_404(Competition, slug=sl).id

    if Competition.objects.filter(end_date__lte=timezone.now(), id=ctf_id).count() > 0:
        status = 'outdated'
    elif Competition.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(), id=ctf_id).count():
        status = 'running'
    else:
        status = 'incoming'

    reg_list = []
    user_id = User.objects.get(pk=request.user.id).id
    reg_ctf_list = CompeteRegistration.objects.filter(user_id=user_id)
    for ctf in reg_ctf_list:
        reg_list.append(ctf.ctf_id)

    if ctf_id not in reg_list and status != 'outdated':
        return render(request, 'tasks/error.html', {'title': 'Необходимо зарегистрироваться на CTF!'})

    ctf = get_object_or_404(Competition, id=ctf_id)
    ctf_tasks_list = CompeteTasks.objects.filter(compete_id=ctf_id)
    team = Teams.objects.get(pk=Profile.objects.get(user_id=request.user.id).team_id)
    ctf_tasks = []
    for task in ctf_tasks_list:
        ctf_tasks.append(Tasks.objects.get(pk=task.task_id))
    for task in ctf_tasks:
        task.attach = Attach.objects.filter(task_id=task.id)
    cats = Categories.objects.values('id', 'name').distinct()
    ctf_name = Competition.objects.get(id=ctf_id).name

    solved_tasks = []
    if ctf.compete_type_id == 1:
        solved_tasks_list = Stats.objects.filter(is_correct=True, team_id=team, compete=ctf_id)
    else:
        solved_tasks_list = Stats.objects.filter(is_correct=True, user=request.user, compete=ctf_id)

    for task in solved_tasks_list:
        solved_tasks.append(task.task_id)

    def is_ans_valid(answer, task_id):
        if answer == Tasks.objects.get(pk=task_id).answer:
            return True
        return False

    def add_stats(answer, task_id):
        is_correct = is_ans_valid(answer, task_id)
        compete = Competition.objects.get(slug=sl)
        team = Teams.objects.get(pk=Profile.objects.get(user_id=request.user.id).team_id)
        task = Tasks.objects.get(pk=task_id)
        points = Tasks.objects.get(pk=task_id).score
        new_stat = Stats(user=request.user, task=task, compete=compete, team=team, is_correct=is_correct, points=points)
        new_stat.save()

    if request.method == 'POST' and status == 'running':
        form = ValidateAnswer(request.POST)
        if form.is_valid():
            if ctf.compete_type_id != 1:
                if form.cleaned_data['task_id'] not in solved_tasks:
                    add_stats(**form.cleaned_data)
                    solved_tasks.append(form.cleaned_data['task_id'])
                    return redirect('/ctfs/'+slug+'/')
            else:
                add_stats(**form.cleaned_data)
    else:
        form = ValidateAnswer()

    return render(request, 'tasks/ctf.html', {'title': ctf_name, 'tasks': ctf_tasks, 'cats': cats, 'solved_tasks': solved_tasks, 'form': form, 'status': status})


def show_profile(request, username):
    user = User.objects.get(username=username)
    if request.user.username == username:
        user_profile = True
        title = 'Мой профиль'
    else:
        user_profile = False
        title = 'Профиль ' + username
    #is_admin = user.is_staff

    tasks_solved = Stats.objects.filter(user_id=user.id, is_correct=True).count()
    tasks_solved_archive = Stats.objects.filter(user_id=user.id, compete=DEFAULT_CTF_ID, is_correct=True)
    tasks_points = 0

    for task in tasks_solved_archive:
        tasks_points += task.points
    ctf_list = CompeteRegistration.objects.filter(user_id=user.id)
    ctf_part = len(ctf_list)
    ctf_list_id = [ctf.id for ctf in ctf_list]

    ctf_points = 0
    ctf_task_list = Stats.objects.filter(user_id=user.id, compete__isnull=False, is_correct=True).exclude(compete=DEFAULT_CTF_ID)
    for task in ctf_task_list:
        ctf_points += task.points

    team_id = Profile.objects.get(user_id=user.id).team_id
    if team_id == DEFAULT_TEAM_ID:
        team = None
    else:
        team = Teams.objects.get(id=team_id)

    #top = Stats.objects.values('user_id').filter(is_correct=True).order_by('user_id').annotate(total_points=Sum('points')).order_by('-total_points').filter(user_id=user.id).count()
    total_scoreboard = Stats.objects.values('user_id').filter(is_correct=True).order_by('user_id').annotate(total_points=Sum('points')).order_by('-total_points')
    user_score = Stats.objects.values('user_id').filter(is_correct=True).order_by('user_id').annotate(total_points=Sum('points')).order_by('-total_points').filter(user_id=user.id)
    try:
        top = list(total_scoreboard).index(list(user_score)[0])+1
    except IndexError:
        top = User.objects.count()+1

    mvp = int((1-((top-1) / User.objects.count()))*100)

    return render(request, 'tasks/profile.html', {'title': title, 'self': user_profile, 'tasks_points': tasks_points, 'tasks_solved': tasks_solved, 'ctf_points': ctf_points, 'ctf_part': ctf_part, 'team': team, 'top': top, 'username': user.username, 'mvp': mvp})


class ChangePass(DataMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'tasks/change_pass.html'
    success_url = reverse_lazy('change_pass_done')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Смена пароля")
        return dict(list(context.items()) + list(c_def.items()))


class ChangePassDone(DataMixin, PasswordChangeDoneView):
    template_name = 'tasks/change_pass_done.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Пароль успешно изменен")
        return dict(list(context.items()) + list(c_def.items()))


def show_team(request, team_id):
    if team_id is None:
        reverse_lazy('teams/')
    team = get_object_or_404(Teams, pk=team_id)

    #if team.is_hidden:
    #    raise Http404

    #if team_id == DEFAULT_TEAM_ID:
    #    return render(request, 'tasks/team.html', {'title': 'Команда не найдена', 'is_default': True})

    if team.is_open:
        title = team.name
    else:
        title = team.name + ' (вступление закрыто)'

    if request.user.is_authenticated and Profile.objects.get(user_id=request.user.id).team_id == team_id:
        is_in_team = True
    else:
        is_in_team = False

    def has_team(user_id):
        """Функция, проверяющая, есть ли у пользователя команда"""
        if request.user.is_authenticated:
            user = Profile.objects.get(user_id=user_id)
            if user.team_id is None or user.team_id == DEFAULT_TEAM_ID:
                return False
            return True
        return False

    try:
        cpt = User.objects.get(pk=Teams.objects.get(pk=team_id).cpt_id)
    except:
        cpt = User.objects.get(pk=Teams.objects.get(pk=2).cpt_id)

    if request.user.id == cpt.id:
        is_cpt = True
    else:
        is_cpt = False
    members = User.objects.filter(pk__in=Profile.objects.filter(team_id=team_id).values_list('user_id'))

    return render(request, 'tasks/team.html', {'title': title, 'cpt': cpt, 'is_cpt': is_cpt, 'is_in_team': is_in_team, 'members': members, 'has_team': has_team, 'team_id': team_id})


def join_team(request, team_id):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    action = 'join'
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=team_id)
    error = False

    if request.method == 'POST':
        def has_error():
            err = False
            if profile.team_id != DEFAULT_TEAM_ID:
                err = 'Вы уже состоите в команде! Сперва покиньте текущую команду.'
            if not team.is_open:
                err = 'Вход в команду закрыт. Свяжитесь с капитаном для вступления'
            return err

        error = has_error()
        if error:
            return render(request, 'tasks/change_team.html',
                          {'title': 'Подтвердите действие', 'action': action, 'team': team, 'error': error,
                           'username': request.user.username})
        else:
            profile.team_id = team_id
            profile.save()
            return redirect('team', team_id=team_id)

    return render(request, 'tasks/change_team.html', {'title': 'Подтвердите действие', 'action': action, 'team': team, 'error': error, 'username': request.user.username })


def leave_team(request):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    action = 'leave'
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=profile.team_id)
    if team.id == DEFAULT_TEAM_ID:
        err = 'Вы не можете покинуть команду, так как не состоите в ней!'
        return render(request, 'tasks/change_team.html',
                      {'title': 'Ошибка', 'action': action, 'team': team, 'error': err})
    cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)
    err = False

    if request.method == 'POST':
        form = LeaveTeam(request.POST)

        def has_error():
            err = False
            if team.id == DEFAULT_TEAM_ID:
                err = 'Вы не можете покинуть команду, так как не состоите в ней!'
            if request.user.id == cpt.id:
                err = 'Вы не можете покинуть команду, так как вы капитан! Передайте лидерство или удалите команду'
            return err

        if has_error():
            err = has_error()
            return render(request, 'tasks/change_team.html',
                          {'title': 'Подтвердите действие', 'action': action, 'team': team, 'error': err,
                           'username': request.user.username})
        else:
            profile.team_id = DEFAULT_TEAM_ID
            profile.save()
            return redirect('teams')

    return render(request, 'tasks/change_team.html', {'title': 'Подтвердите действие', 'action': action, 'team': team, 'error': err, 'username': request.user.username })


def kick_team(request):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=profile.team_id)
    cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)
    form = ChooseUserFromTeam(user_id=request.user.id)
    if request.user.id != cpt.id:
        err = 'Вы не можете управлять командой, так как вы не капитан команды!'
        return render(request, 'tasks/kick_user.html', {'title': 'Исключение из команды', 'team': team, 'error': err, 'form': form})
    form = ChooseUserFromTeam(user_id=request.user.id)

    if request.method == 'POST':
        try:
            user = request.POST['user']
        except KeyError:
            pass

        form = ChooseUserFromTeam(user_id=request.user.id)
        user_profile = Profile.objects.get(user_id=user)

        def has_error():
            err = False
            if request.user.id != cpt.id:
                err = 'Вы не можете управлять командой, так как вы не капитан команды!'
            if user_profile.team_id != team.id:
                err = 'Вы не можете исключить участника чужой команды!'
            return err

        if has_error():
            err = has_error()
            return render(request, 'tasks/kick_user.html',
                          {'title': 'Исключение из команды', 'team': team, 'error': err, 'form': form})
        else:
            user_profile.team_id = DEFAULT_TEAM_ID
            user_profile.save()
            return redirect('team', team_id=team.id)
    return render(request, 'tasks/kick_user.html',
                  {'title': 'Исключение из команды', 'team': team, 'form': form})


def change_cpt_team(request):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=profile.team_id)
    cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)
    form = ChooseUserFromTeam(user_id=request.user.id)

    if request.user.id != cpt.id:
        err = 'Вы не можете управлять командой, так как вы не капитан команды!'
        return render(request, 'tasks/change_cpt.html', {'title': 'Передача капитанского титула', 'team': team, 'error': err, 'form': form})

    if request.method == 'POST':
        try:
            user = request.POST['user']
        except KeyError:
            pass

        form = ChooseUserFromTeam(user_id=request.user.id)
        user_profile = Profile.objects.get(user_id=user)

        def has_error():
            err = False
            if request.user.id != cpt.id:
                err = 'Вы не можете управлять командой, так как вы не капитан команды!'
            if user_profile.team_id != team.id:
                err = 'Вы не можете передать статус капитана участнику чужой команды!'
            return err

        if has_error():
            err = has_error()
            return render(request, 'tasks/change_cpt.html',
                          {'title': 'Передача капитанского титула', 'team': team, 'error': err, 'form': form})
        else:
            team.cpt_id = user
            team.save()
            return redirect('team', team_id=team.id)
    return render(request, 'tasks/change_cpt.html',
                  {'title': 'Передача капитанского титула', 'team': team, 'form': form})


def open_team(request):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=profile.team_id)
    if team.id == DEFAULT_TEAM_ID:
        return redirect('teams')
    cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)

    def has_error():
        err = False
        if request.user.id != cpt.id:
            err = 'Вы не можете управлять командой, так как вы не капитан команды!'
        return err

    if has_error():
        return redirect('team', team_id=team.id)

    else:
        if team.is_open:
            team.is_open = False
        else:
            team.is_open = True
        team.save()
        return redirect('team', team_id=team.id)


def delete_team(request):
    if not request.user.is_authenticated:
        return render(request, 'tasks/unauthorized.html', {'title': 'Необходимо войти!'})
    profile = Profile.objects.get(user_id=request.user.id)
    team = get_object_or_404(Teams, pk=profile.team_id)
    cpt = User.objects.get(pk=Teams.objects.get(pk=team.id).cpt_id)
    error = False
    if request.user.id != cpt.id:
        err = 'Вы не можете управлять командой, так как вы не капитан команды!'
        return render(request, 'tasks/delete_team.html', {'title': 'Подтвердите действие', 'team': team, 'error': err, 'username': request.user.username })
    if request.method == 'POST':
        def has_error():
            err = False
            if request.user.id != cpt.id:
                err = 'Вы не можете управлять командой, так как вы не капитан команды!'
            return err

        error = has_error()
        if error:
            return render(request, 'tasks/delete_team.html', {'title': 'Подтвердите действие', 'team': team, 'error': error, 'username': request.user.username })
        else:
            members = Profile.objects.filter(team_id=team.id)
            for member in members:
                member.team_id = DEFAULT_TEAM_ID
                member.save()

            team.cpt_id = 1
            team.is_hidden = True
            team.is_open = False
            team.save()

            return redirect('team', team_id=team.id)

    return render(request, 'tasks/delete_team.html', {'title': 'Подтвердите действие', 'team': team, 'error': error, 'username': request.user.username })


def stats_ctf(request, slug):
    ctf = get_object_or_404(Competition, slug=slug)
    #ctf = Competition.objects.get(slug=slug)

    def format_time(date):
        return datetime.datetime.strftime(date + datetime.timedelta(hours=2), '%d/%m/%Y %H:%M:%S')

    start = format_time(ctf.start_date)
    end = format_time(ctf.end_date)
    if ctf.compete_type_id == 1: # team
        score = Stats.objects.values('team_id').filter(is_correct=True, compete=ctf.id).exclude(team_id=DEFAULT_TEAM_ID).order_by('team_id').annotate(total_points=Sum('points')).order_by('-total_points')
        for team in score:
            team['name'] = Teams.objects.get(pk=team['team_id']).name
        teams_stats = Stats.objects.filter(is_correct=True, compete=ctf.id).exclude(team_id=DEFAULT_TEAM_ID)
        teams_list = teams_stats.values('team_id').distinct()
        stats = []
        for team in teams_list:
            team_stat = {'name': Teams.objects.get(pk=team['team_id']).name, 'stats': []}
            db_stats = teams_stats.filter(team_id=team['team_id'])
            prev = 0
            for stat in db_stats:
                prev += stat.points
                stat.score = prev
                time = format_time(stat.time)
                statline = {'time': time, 'score': prev}
                team_stat['stats'].append(statline)
            stats.append(team_stat)
    else: # solo
        score = Stats.objects.values('user_id').filter(is_correct=True, compete=ctf.id).order_by('user_id').annotate(total_points=Sum('points')).order_by('-total_points')
        for user in score:
            user['name'] = User.objects.get(pk=user['user_id']).username
        user_stats = Stats.objects.filter(is_correct=True, compete=ctf.id)
        user_list = user_stats.values('user_id').distinct()
        stats = []
        for user in user_list:
            user_stat = {'name': User.objects.get(pk=user['user_id']).username, 'stats': []}
            db_stats = user_stats.filter(user_id=user['user_id'])
            prev = 0
            for stat in db_stats:
                prev += stat.points
                stat.score = prev
                time = format_time(stat.time)
                statline = {'time': time, 'score': prev}
                user_stat['stats'].append(statline)
            stats.append(user_stat)
    return render(request, 'tasks/ctf_stat.html', {'title': 'Статистика '+ ctf.name, 'ctf': ctf, 'score_list': score, 'stats': stats, 'start': start, 'end': end})

