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

from materials import views
from materials.views import read_script, add_script

urlpatterns = [
    path('read_script/<int:script_id>/', read_script, name='read_script'),

    path('add_script/', views.add_script, name='add_script'),

    path('api/categories/', views.category_autocomplete, name='category_autocomplete'),
]
