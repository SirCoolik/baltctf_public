from django.contrib import admin

# Register your models here.

from .models import *


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'compete_type', 'is_paused', 'is_hidden')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


class CompeteTasksAdmin(admin.ModelAdmin):
    list_display = ('id', 'compete', 'task_id')
    list_display_links = ('id', 'compete', 'task_id')


class CompeteTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')


class CompeteRegAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ctf')
    list_display_links = ('id', 'user', 'ctf')


class TasksAdmin(admin.ModelAdmin):
    list_display = ('is_hidden', 'id', 'name', 'author', 'cat', 'score_type', 'score', 'answer')
    list_display_links = ('id', 'name', 'author', 'cat', 'score_type', 'score', 'answer')


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpt', 'url', 'is_hidden', 'is_open')


class StatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'compete', 'team', 'is_correct', 'points', 'time')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'url', 'is_hidden')


class AttachAdmin(admin.ModelAdmin):
    list_display = ('name', 'task', 'url')


class ScoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc')


admin.site.register(Tasks, TasksAdmin)
admin.site.register(Categories, CategoryAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(CompeteType, CompeteTypesAdmin)
admin.site.register(CompeteTasks, CompeteTasksAdmin)
admin.site.register(CompeteRegistration, CompeteRegAdmin)
admin.site.register(Teams, TeamAdmin)
admin.site.register(Stats, StatsAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Attach, AttachAdmin)
admin.site.register(Score, ScoreAdmin)