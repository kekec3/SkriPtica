from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db.models import Case, When, Value, IntegerField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from accounts.context_check import user_role_processor
from accounts.models import Korisnik
from materials.models import Kategorija, Skripta, KategorijaNad


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
                    user = Korisnik.objects.get(kor_ime=username)
                    request.session['user_id'] = user.idkor
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
                user = Korisnik.objects.get(kor_ime=user.get_username())
                request.session['user_id'] = user.idkor
                return redirect('index')

    context = {
        'form': form,
        'mess': mess,
        'action': action
    }

    return render(request, 'login.html', context)


def logout_view(request):
    auth_logout(request) # Clears the Django auth session
    if 'user_id' in request.session:
        del request.session['user_id'] # Clears your custom session ID
    return redirect('materials:search_page')


def moderator_dashboard(request):
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        # ... (Keep your existing POST logic for creating categories) ...
        pass

    # Define the custom sort order
    kategorije = Kategorija.objects.annotate(
        sort_order=Case(
            When(tip='Fakultet', then=Value(1)),
            When(tip='Godina', then=Value(2)),
            When(tip='Predmet', then=Value(3)),
            When(tip='Ostalo', then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    ).order_by('sort_order', 'naziv') # Sort by type order, then alphabetically

    pending_scripts = Skripta.objects.filter(odobrena=0).select_related('idkat')

    context = {
        'kategorije': kategorije,
        'skripte': pending_scripts,
    }
    return render(request, 'Moderator.html', context)

def approve_script(request, script_id):
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        skripta = get_object_or_404(Skripta, pk=script_id)
        skripta.odobrena = 1
        skripta.save()

    return redirect('moderator_dashboard')


def delete_script(request, script_id):
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        skripta = get_object_or_404(Skripta, pk=script_id)
        if skripta.fajl:
            skripta.fajl.delete()
        skripta.delete()

    return redirect('moderator_dashboard')