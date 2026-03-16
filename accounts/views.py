'''
Authors: Milutin Jovanović 0385/2022, Andrej Praizović 0300/2022, Jaksa Jezdić 0543/2022
'''
from django.db.models import Case, When, Value, IntegerField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from accounts.context_check import user_role_processor
from materials.forms import MaterialForm
from materials.models import Kategorija, Skripta, KategorijaNad


# Create your views here.


def index(request):
    return render(request, 'index.html')

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from accounts.models import Korisnik, Role


def login(request):
    """
    Opis: Obrađuje prijavu i registraciju korisnika.
          Akcija 'login' autentifikuje korisnika po korisničkom imenu i lozinci
          i čuva njegov ID u sesiji. Akcija 'register' kreira novog Django User-a
          i odgovarajući Korisnik objekat, a zatim ga prijavljuje i preusmjerava
          na stranicu pretrage.

    Tabele baze: :model:`accounts.Korisnik`

    Template: :template:`accounts/login.html`
    """
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
                    return redirect('/materials/search')
                else:
                    mess = "Pogrešna lozinka"

        elif action == 'register':
            username1 = request.POST.get('username')
            password1 = request.POST.get('password1')
            form = UserCreationForm(request.POST)

            if form.is_valid():
                user = form.save()
                korisnik = Korisnik.objects.create(kor_ime=username1, lozinka=password1, email = request.POST.get("email"))
                korisnik.save()
                auth_login(request, user)
                user = Korisnik.objects.get(kor_ime=user.get_username())
                request.session['user_id'] = user.idkor
                return redirect('/materials/search')

    context = {
        'form': form,
        'mess': mess,
        'action': action
    }

    return render(request, 'login.html', context)

def profile(request):
    """
    Opis: Prikazuje profil trenutno prijavljenog korisnika zajedno sa
          listom skripti koje je postavio.

    Tabele baze: :model:`accounts.Korisnik`
                 :model:`materials.Skripta`

    Template: :template:`accounts/profile.html`
    """
    user = Korisnik.objects.get(kor_ime=request.user.username)
    username = user.kor_ime
    id = user.idkor
    skripte = Skripta.objects.filter(idkor=id)
    context = {'username': username, 'id': id, 'skripte': skripte}
    return render(request, 'profile.html', context)


def logout_view(request):
    """
    Opis: Odjavljuje korisnika — briše Django auth sesiju i prilagođeni
          session ključ 'user_id', te preusmjerava na stranicu pretrage.

    Tabele baze: (nema direktnog pristupa)

    Template: (nema — vrši redirect)
    """
    auth_logout(request) # Clears the Django auth session
    if 'user_id' in request.session:
        del request.session['user_id'] # Clears your custom session ID
    return redirect('materials:search_page')


def moderator_dashboard(request):
    """
    Opis: Prikazuje moderatorsku kontrolnu tablu dostupnu samo moderatorima.
          Omogućava dodavanje novih kategorija (sa opcionim roditeljom i tipom)
          i pregled skripti koje čekaju odobrenje. Kategorije su sortirane
          po tipu: Fakultet → Godina → Predmet → Ostalo.

    Tabele baze: :model:`materials.Kategorija`
                 :model:`materials.KategorijaNad`
                 :model:`materials.Skripta`

    Template: :template:`accounts/Moderator.html`
    """
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        naziv = request.POST.get('naziv', '').strip()
        parent_id = request.POST.get('parent_id')
        tip = request.POST.get('tip', 'Ostalo')

        if naziv:
            # Check if category already exists (Case-insensitive)
            if Kategorija.objects.filter(naziv__iexact=naziv).exists():
                messages.error(request, f'Greška: Kategorija sa nazivom "{naziv}" već postoji.')
            else:
                nova_kat = Kategorija.objects.create(naziv=naziv, tip=tip)
                if parent_id:
                    try:
                        parent_kat = Kategorija.objects.get(pk=parent_id)
                        KategorijaNad.objects.create(idkatnad=parent_kat, idkatpod=nova_kat)
                    except Kategorija.DoesNotExist:
                        pass
                messages.success(request, f'Uspešno dodata kategorija: {naziv}')

            return redirect('moderator_dashboard')

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
    ).order_by('sort_order', 'naziv')

    pending_scripts = Skripta.objects.filter(odobrena=0).select_related('idkat')

    context = {
        'kategorije': kategorije,
        'skripte': pending_scripts,
    }
    return render(request, 'Moderator.html', context)

def approve_script(request, script_id):
    """
    Opis: Prima POST zahtjev i postavlja status skripte na odobrenu (odobrena=1).
          Dostupno samo moderatorima. Nakon akcije preusmjerava na moderatorsku tablu.

    Tabele baze: :model:`materials.Skripta`

    Template: (nema — vrši redirect)
    """
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        skripta = get_object_or_404(Skripta, pk=script_id)
        skripta.odobrena = 1
        skripta.save()

    return redirect('moderator_dashboard')


def delete_script(request, script_id):
    """
    Opis: Prima POST zahtjev i briše skriptu zajedno sa njenim fajlom sa servera.
          Dostupno samo moderatorima. Nakon brisanja preusmjerava na moderatorsku tablu.

    Tabele baze: :model:`materials.Skripta`

    Template: (nema — vrši redirect)
    """
    roles = user_role_processor(request)
    if not roles['is_moderator']:
        return redirect('materials:search_page')

    if request.method == 'POST':
        skripta = get_object_or_404(Skripta, pk=script_id)
        if skripta.fajl:
            skripta.fajl.delete()
        skripta.delete()

    return redirect('moderator_dashboard')

def delete_my_script(request, script_id):
    """
    Opis: Omogućava korisniku da obriše vlastitu skriptu.
          Briše i fizički fajl sa servera. Nakon brisanja preusmjerava na profil.

    Tabele baze: :model:`materials.Skripta`

    Template: (nema — vrši redirect)
    """
    if request.method == 'POST':
        skripta = get_object_or_404(Skripta, pk=script_id)
        if skripta.fajl:
            skripta.fajl.delete()
        skripta.delete()

    return redirect('profile')


def update_my_script(request, script_id):
    """
    Opis: Prikazuje formu za izmjenu postojeće skripte i obrađuje njeno slanje.
          Nakon izmjene, skripta se vraća u status "nije odobrena" (odobrena=0)
          i korisnik se preusmjerava na stranicu profila.

    Tabele baze: :model:`materials.Skripta`
                 :model:`accounts.Korisnik`

    Template: :template:`accounts/update_script.html`
    """
    skripta = Skripta.objects.get(idskr=script_id)
    tekst = skripta.opis
    form = MaterialForm(instance=skripta)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=skripta)

        if form.is_valid():
            skripta = form.save(commit=False)
            skripta.idkor = Korisnik.objects.get(pk=request.session.get('user_id'))

            skripta.odobrena = 0
            skripta.save()
            return redirect('/accounts/profile/')
        else:
            print(form.errors)

    return render(request, 'update_script.html',{'form': form, 'tekst': tekst})

def admin_dashboard(request):
    """
    Opis: Prikazuje administratorsku kontrolnu tablu dostupnu samo adminima.
          Prikazuje listu svih korisnika (osim trenutno prijavljenog admina)
          sa njihovim ulogama, sortirano po korisničkom imenu.

    Tabele baze: :model:`accounts.Korisnik`
                 :model:`accounts.Role`

    Template: :template:`accounts/admin.html`
    """
    roles = user_role_processor(request)

    if not roles.get('is_admin'):
        return redirect('materials:search_page')

    current_user_id = request.session.get('user_id')

    korisnici = Korisnik.objects.select_related('idrol') \
        .exclude(idkor=current_user_id) \
        .order_by('kor_ime')

    context = {
        'korisnici': korisnici
    }

    return render(request, 'admin.html', context)


def promote_to_moderator(request, user_id):
    """
    Opis: Prima POST zahtjev i dodjeljuje ulogu moderatora odabranom korisniku.
          Admin korisnici ne mogu biti promovisani. Dostupno samo adminima.

    Tabele baze: :model:`accounts.Korisnik`
                 :model:`accounts.Role`

    Template: (nema — vrši redirect)
    """
    roles = user_role_processor(request)

    if not roles.get('is_admin'):
        return redirect('materials:search_page')

    if request.method == 'POST':
        korisnik = get_object_or_404(Korisnik, pk=user_id)

        if korisnik.idrol.opis == 'admin':
            return redirect('admin_dashboard')

        moderator_role = get_object_or_404(Role, opis='moderator')
        korisnik.idrol = moderator_role
        korisnik.save()

    return redirect('admin_dashboard')

def demote_to_user(request, user_id):
    """
    Opis: Prima POST zahtjev i vraća moderatora na ulogu običnog korisnika.
          Admin korisnici ne mogu biti degradirani. Dostupno samo adminima.

    Tabele baze: :model:`accounts.Korisnik`
                 :model:`accounts.Role`

    Template: (nema — vrši redirect)
    """
    roles = user_role_processor(request)

    if not roles.get('is_admin'):
        return redirect('materials:search_page')

    if request.method == 'POST':
        korisnik = get_object_or_404(Korisnik, pk=user_id)

        if korisnik.idrol.opis == 'admin':
            return redirect('admin_dashboard')

        user_role = get_object_or_404(Role, opis='korisnik')
        korisnik.idrol = user_role
        korisnik.save()

    return redirect('admin_dashboard')