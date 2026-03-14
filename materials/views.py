from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from pypdf import PdfReader
from groq import Groq
import os

from accounts.models import Korisnik
from materials.forms import MaterialForm
from materials.models import Komentar, Skripta, Kategorija, KategorijaNad, Sacuvano


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


client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def summarize_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages[:3]:
        t = page.extract_text()
        if t:
            text += t

    prompt = f"""
            Napravi kratak rezime ove skripte (3-5 recenica):
            
            {text[:4000]}
            """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def read_script(request, script_id):
<<<<<<< HEAD
=======
    if request.method == 'POST':
        komentar = request.POST.get('komentar').strip()
        korisnik_id = Korisnik.objects.filter(idkor=9)
        skripta_id = Skripta.objects.filter(idskr=script_id)
        Komentar.objects.create(
            idkor=korisnik_id[0],
            idskr=skripta_id[0],
            tekst=komentar
        )
        return redirect('read_script', script_id=script_id)
>>>>>>> 3164fb3 (Final Working Search Page)
    script = Skripta.objects.get(idskr=script_id)
    korisnik = Korisnik.objects.get(idkor=2)
    is_saved = Sacuvano.objects.filter(
        idkor=korisnik,
        idskr=script
    ).exists()
    summary = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'komentar':
            tekst_komentara = request.POST.get('komentar', '').strip()
            if tekst_komentara:
                Komentar.objects.update_or_create(
                    idkor=korisnik,
                    idskr=script,
                    tekst=tekst_komentara
                )
            return redirect('materials:read_script', script_id=script_id)

        elif action == 'sacuvaj':
            focus = request.POST.get('focus')
            if focus:
                focus_str = "focus"
            else:
                focus_str = ""
            Sacuvano.objects.update_or_create(
                idkor=korisnik,
                idskr=script,
                kolekcija= focus_str
            )
            return redirect('materials:read_script', script_id=script_id)

        elif action == 'zaboravi':
            Sacuvano.objects.filter(
                idkor=korisnik,
                idskr=script
            ).delete()
            return redirect('materials:read_script', script_id=script_id)

        elif action == 'rezimiraj':
            pdf_path = script.fajl.path
            summary = summarize_pdf(pdf_path)


    commentsForScript = Komentar.objects.filter(idskr=script_id)

    context = {
        'commentsForScript': commentsForScript,
        'script': script,
        'is_saved': is_saved,
        'summary': summary,
    }
    return render(request, 'read_script.html', context)

def get_all_subcategories(category_id):
    """Recursive helper to find all child category IDs."""
    # Start with the current category
    all_ids = [category_id]

    # Find immediate children using the KategorijaNad bridge
    children = KategorijaNad.objects.filter(idkatnad_id=category_id).values_list('idkatpod_id', flat=True)

    # Recursively find children of children
    for child_id in children:
        all_ids.extend(get_all_subcategories(child_id))

    return list(set(all_ids))  # Use set to avoid duplicates

def search_page(request):
    fakulteti = Kategorija.objects.filter(tip='Fakultet')
    skripte = Skripta.objects.filter(odobrena=1)

    query = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag_id', '') # From hidden input
    tag_text = request.GET.get('kategorija', '').strip() # From visible input
    fakultet_id = request.GET.get('fakultet', '')

    if query:
        skripte = skripte.filter(Q(naziv__icontains=query) | Q(opis__icontains=query))

    final_tag_id = None
    if tag_id:
        final_tag_id = tag_id
    elif tag_text:
        try:
            cat = Kategorija.objects.filter(naziv__icontains=tag_text).first()
            if cat:
                final_tag_id = cat.idkat
        except Kategorija.DoesNotExist:
            pass

    if final_tag_id:
        related_ids = get_all_subcategories(final_tag_id)
        skripte = skripte.filter(idkat_id__in=related_ids)

    if fakultet_id:
        faculty_tree_ids = get_all_subcategories(fakultet_id)
        skripte = skripte.filter(idkat_id__in=faculty_tree_ids)

    context = {
        'skripte': skripte.select_related('idkat'),
        'fakulteti': fakulteti,
    }
    return render(request, 'Search.html', context)



def saved_scripts(request):
    korisnik = Korisnik.objects.get(idkor=2)

    sacuvane = Sacuvano.objects.filter(idkor=korisnik).select_related("idskr")

    skripte = []

    for s in sacuvane:
        skripta = s.idskr
        skripta.is_focus = (s.kolekcija == "focus")
        skripte.append(skripta)

    return render(request, "saved_scripts.html", {"skripte": skripte})