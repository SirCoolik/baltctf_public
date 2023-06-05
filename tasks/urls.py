from django.urls import path

from .views import *


urlpatterns = [
    path('', index, name='home'),
    path('ctfs/', ctfs, name='ctfs'),
    path('ctfs/<slug:slug>/', show_ctf, name='ctf'),
    path('ctfs/<slug:slug>/stats/', stats_ctf, name='stats_ctf'),
    path('ctf_reg/<slug:slug>/', reg_ctf, name='reg_ctf'),
    path('categories/', CatList.as_view(), name='categories'),
    path('challenges/<slug:slug>/', show_challenges, name='challenges'),
    path('teams/', TeamsList.as_view(), name='teams'),
    path('team/<int:team_id>/', show_team, name='team'),
    path('team/', TeamsList.as_view(), name='teams'),
    path('add_team/', add_team, name='add_team'),
    path('leave_team/', leave_team, name='leave_team'),
    path('kick_team/', kick_team, name='kick_team'),
    path('change_cpt/', change_cpt_team, name='change_cpt'),
    path('open_team/', open_team, name='open_team'),
    path('join_team/<int:team_id>/', join_team, name='join_team'),
    path('delete_team/', delete_team, name='delete_team'),
    path('profile/<slug:username>', show_profile, name='profile'),
    path('login/', LoginUser.as_view(), name='login'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('changepass/', ChangePass.as_view(), name='change_pass'),
    path('changepass/done/', ChangePassDone.as_view(), name='change_pass_done'),
    #path('forgot/', forgot, name='forgot'),
    path('logout/', logout_user, name='logout'),
]
