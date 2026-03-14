from django.shortcuts import render

from materials.models import Komentar, Skripta


# Create your views here.

def add_script(request):
    if request.method == 'POST':
        naslov = request.POST.get('naslov')
        opis = request.POST.get('opis')
        fakultet = request.POST.get('fakultet')
        godina = request.POST.get('godina')
        predmet = request.POST.get('predmet')
        fajl = request.FILES.get('fajl')

        print("Naslov:", naslov)
        print("Opis:", opis)
        print("Fakultet:", fakultet)
        print("Godina:", godina)
        print("Predmet:", predmet)
        print("Fajl:", fajl)

        """skripta = Skripta.objects.create(
            idkor=request.user,
            idkat=0,
            naziv=naslov,
            opis=opis,
            fajl=fajl,
            odobrena=0
        )"""

        # privremeno samo test da vidiš da POST radi
        return render(request, 'add_script.html')

    return render(request, 'add_script.html')

def read_script(request, script_id):
    #script = Skripta.objects.get(id=script_id)
    #commentsForScript = Komentar.objects.filter(idskr=script_id)

    """context = {
        'commentsForScript': commentsForScript,
        'script': script,
    }"""

    return render(request, 'read_script.html')#context