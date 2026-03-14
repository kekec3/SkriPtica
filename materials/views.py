from django.http import JsonResponse
from django.shortcuts import render, redirect

from materials.forms import MaterialForm
from materials.models import Komentar, Skripta, Kategorija


# Create your views here.

def category_autocomplete(request):
    query = request.GET.get('q', '')
    categories = Kategorija.objects.filter(naziv__icontains=query)[:6]
    data = [{'id': c.pk, 'name': c.naziv} for c in categories]
    return JsonResponse(data, safe=False)


def add_script(request):
    if request.method == 'POST':
        data = {
            'naziv' : request.POST.get('naslov'),
            'opis' : request.POST.get('opis'),
            'idkat' : request.POST.get('idKat'),
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
    #script = Skripta.objects.get(id=script_id)
    #commentsForScript = Komentar.objects.filter(idskr=script_id)

    """context = {
        'commentsForScript': commentsForScript,
        'script': script,
    }"""

    return render(request, 'read_script.html')#context