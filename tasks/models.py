import os.path

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ctf import settings

DEFAULT_TEAM_ID = 1


class Tasks(models.Model):
    # task id
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    cat = models.ForeignKey('Categories', on_delete=models.PROTECT)
    score_type = models.ForeignKey('Score', on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    desc = models.TextField()
    score = models.IntegerField()
    answer = models.CharField(max_length=255)
    create_date = models.DateTimeField(auto_now_add=True)
    edit_date = models.DateTimeField(auto_now=True)
    is_hidden = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Competition(models.Model):
    # compete id
    name = models.CharField(max_length=150)
    desc = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    compete_type = models.ForeignKey('CompeteType', on_delete=models.PROTECT) # FOREIGN KEY --> CompeteType ID
    is_paused = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return self.name


class CompeteTasks(models.Model):
    compete = models.ForeignKey('Competition', on_delete=models.PROTECT) # FOREIGN KEY --> competition / compete_id
    task = models.ForeignKey('Tasks', on_delete=models.PROTECT) # FOREIGN KEY --> tasks / task_id


class CompeteType(models.Model):
    #type_id
    name = models.CharField(max_length=4)

    def __str__(self):
        return self.name


class Teams(models.Model):
    #team_id
    name = models.CharField(max_length=100, unique=True)
    cpt = models.ForeignKey('auth.User', on_delete=models.PROTECT) # FOREIGN KEY --> Users / user_id
    url = models.CharField(max_length=255, default='')
    is_hidden = models.BooleanField(default=False)
    is_open = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Profile(models.Model):
    #user_id
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey('Teams', on_delete=models.PROTECT, default=DEFAULT_TEAM_ID) # FOREIGN KEY --> Teams / team_id
    url = models.CharField(max_length=255, null=True)
    is_hidden = models.BooleanField(default=False)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


class Stats(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT) # FOREIGN KEY --> Users / user_id
    task = models.ForeignKey('Tasks', on_delete=models.PROTECT) # FOREIGN KEY --> Tasks / task_id
    compete = models.ForeignKey('Competition', on_delete=models.PROTECT, null=True) # FOREIGN KEY --> Compete / compete_id
    team = models.ForeignKey('Teams', on_delete=models.PROTECT, null=True)# FOREIGN KEY --> Teams / team_id
    is_correct = models.BooleanField()
    points = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)


class Score(models.Model):
    #score_id
    name = models.CharField(max_length=255)
    desc = models.TextField()

    def __str__(self):
        return self.name

def images_path():
    return os.path.join(settings.STATIC_ROOT, 'images\\cat_logo\\')


class Categories(models.Model):
    #cat_id
    name = models.CharField(max_length=255)
    desc = models.TextField()
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    cat_logo = models.FilePathField(path=r"E:\diploma\firstAttempt\ctf\tasks\static\tasks\images\cat_logo")

    def __str__(self):
        return self.name


class Attach(models.Model):
    #attach_id
    name = models.CharField(max_length=255)
    task = models.ForeignKey('Tasks', on_delete=models.SET_NULL, null=True) # FOREIGN KEY --> Users / user_id
    url = models.URLField()

    def __str__(self):
        return self.name


class CompeteRegistration(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT) # FOREIGN KEY --> Users / user_id
    ctf = models.ForeignKey('Competition', on_delete=models.PROTECT)
