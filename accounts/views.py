from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.shortcuts import render, redirect

from accounts.models import Korisnik


# Create your views here.


def index(request):
    return render(request, 'index.html')
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect


def login(request):
    form = UserCreationForm()
    mess = None
    action = None

    if request.user.is_authenticated:
        return redirect('index')

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')

            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                mess = "Ne postoji korisnik"

            if mess is None:
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    auth_login(request, user)
                    return redirect('index')
                else:
                    mess = "Pogrešna lozinka"

        elif action == 'register':
            form = UserCreationForm(request.POST)

            if form.is_valid():
                user = form.save()
                korisnik = Korisnik.objects.create(kor_ime=user.get_username(), lozinka=user.password, email=user.get_email_field_name())
                korisnik.save()
                auth_login(request, user)
                return redirect('index')

    context = {
        'form': form,
        'mess': mess,
        'action': action
    }

    return render(request, 'login.html', context)