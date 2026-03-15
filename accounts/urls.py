"""
URL configuration for Skriptica project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from accounts import views

urlpatterns = [
    path('index/', views.index, name='index'),

    path('login/', views.login, name='login'),

    path('moderator/', views.moderator_dashboard, name='moderator_dashboard'),

    path('moderator/approve/<int:script_id>/', views.approve_script, name='approve_script'),

    path('moderator/delete/<int:script_id>/', views.delete_script, name='delete_script'),

    path('logout/', views.logout_view, name='logout'),

    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('promote_to_moderator/<int:user_id>/', views.promote_to_moderator, name='promote_to_moderator'),

    path('demote_to_user/<int:user_id>/', views.demote_to_user, name='demote_to_user'),
]
