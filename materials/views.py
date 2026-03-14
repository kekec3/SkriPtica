from django.http import JsonResponse
from django.shortcuts import render, redirect

from accounts.models import Korisnik
from materials.forms import MaterialForm
from materials.models import Komentar, Skripta, Kategorija


def category_autocomplete(request):
    query = request.GET.get('q', '')
    categories = Kategorija.objects.filter(naziv__icontains=query)[:6]
    data = [{'id': c.pk, 'name': c.naziv} for c in categories]
    return JsonResponse(data, safe=False)

def add_script(request):
    if request.method == 'POST':
        data = {
            'naziv': request.POST.get('naslov'),
            'opis': request.POST.get('opis'),
            'idkat': request.POST.get('idKat'),
        }
        form = MaterialForm(data, request.FILES)

        if form.is_valid():
            skripta = form.save(commit=False)
            if request.user.is_authenticated:
                skripta.idkor = request.user.korisnik
            else:
                # If you have a default user with ID 1
                from accounts.models import Korisnik
                skripta.idkor = Korisnik.objects.get(pk=9)

            skripta.odobrena = 0
            skripta.save()
            return redirect('/accounts/index/')
        else:
            # DEBUG: This will show you in the terminal WHY the form is invalid
            print(form.errors)
            return render(request, 'add_script.html', {'form': form, 'error': form.errors})
    return render(request, 'add_script.html')


def read_script(request, script_id):
    if request.method == 'POST':
        komentar = request.POST.get('komentar').strip()
        korisnik_id = Korisnik.objects.filter(idkor=2)
        skripta_id = Skripta.objects.filter(idskr=script_id)
        Komentar.objects.create(
            idkor=korisnik_id[0],
            idskr=skripta_id[0],
            tekst=komentar
        )
        return redirect('read_script', script_id=script_id)
    script = Skripta.objects.get(idskr=script_id)
    commentsForScript = Komentar.objects.filter(idskr=script_id)

    context = {
        'commentsForScript': commentsForScript,
        'script': script,
    }
    return render(request, 'read_script.html', context)