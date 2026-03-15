from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from dotenv import load_dotenv
from pypdf import PdfReader
from groq import Groq
import os

from accounts.models import Korisnik
from materials.forms import MaterialForm
from materials.models import Komentar, Skripta, Kategorija, KategorijaNad, Sacuvano, Ocena

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
            skripta.idkor = Korisnik.objects.get(pk=request.session.get('user_id'))

            skripta.odobrena = 0
            skripta.save()
            return redirect('/accounts/index/')
        else:
            # DEBUG: This will show you in the terminal WHY the form is invalid
            print(form.errors)
            return render(request, 'add_script.html', {'form': form, 'error': form.errors})

    return render(request, 'add_script.html')

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def summarize_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages:
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

def generate_questions_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t

    prompt = f"""
    Na osnovu sledeće skripte napravi tačno 5 pitanja za proveru znanja.

    Pravila:
    - pitanja neka budu jasna i konkretna
    - neka budu na srpskom jeziku
    - neka budu vezana direktno za gradivo iz teksta
    - vrati samo pitanja, bez odgovora
    - svako pitanje napiši u novom redu i numeriši od 1 do 5

    Tekst skripte:
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
    script = Skripta.objects.get(idskr=script_id)
    user_id = request.session.get('user_id')

    is_guest = user_id is None
    summary = None
    questions = None
    is_saved = False
    korisnik = None

    if not is_guest:
        korisnik = Korisnik.objects.get(idkor=user_id)
        is_saved = Sacuvano.objects.filter(idkor=korisnik, idskr=script).exists()

    user_rating_obj = Ocena.objects.filter(idkor=korisnik, idskr=script).first()
    user_rating = user_rating_obj.ocena if user_rating_obj else None

    if request.method == 'POST' and not is_guest:
        action = request.POST.get('action')

        if action == 'komentar':
            tekst_komentara = request.POST.get('komentar', '').strip()
            if tekst_komentara:
                Komentar.objects.update_or_create(
                    idkor=korisnik,
                    idskr=script,
                    defaults={"tekst": tekst_komentara}
                )
            return redirect('materials:read_script', script_id=script_id)

        elif action == 'sacuvaj':
            focus = request.POST.get('focus')
            focus_str = "focus" if focus else ""

            Sacuvano.objects.update_or_create(
                idkor=korisnik,
                idskr=script,
                defaults={"kolekcija": focus_str}
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

        elif action == 'pitanja':
            pdf_path = script.fajl.path
            questions = generate_questions_from_pdf(pdf_path)


        elif action == 'oceni':
            rating_value = request.POST.get("rating")
            if rating_value:
                rating_value = int(rating_value)
                postojeca_ocena = Ocena.objects.filter(
                    idkor=korisnik,
                    idskr=script
                ).first()
                if postojeca_ocena:
                    postojeca_ocena.ocena = rating_value
                    postojeca_ocena.save()
                else:
                    Ocena.objects.create(
                        idkor=korisnik,
                        idskr=script,
                        ocena=rating_value
                    )
            return redirect('materials:read_script', script_id=script_id)

    commentsForScript = Komentar.objects.filter(idskr=script_id)

    context = {
        'commentsForScript': commentsForScript,
        'script': script,
        'is_saved': is_saved,
        'summary': summary,
        'is_guest': is_guest,
        'user_rating': user_rating,
    }
    return render(request, 'read_script.html', context)

def get_all_subcategories(category_id):
    """Recursive helper to find all child category IDs."""
    # Start with the current category
    all_ids = [category_id]

    children = KategorijaNad.objects.filter(
        idkatnad_id=category_id
    ).values_list('idkatpod_id', flat=True)

    # Recursively find children of children
    for child_id in children:
        all_ids.extend(get_all_subcategories(child_id))

    return list(set(all_ids))


def search_page(request):
    fakulteti = Kategorija.objects.filter(tip='Fakultet')
    skripte = Skripta.objects.filter(odobrena=1)

    query = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag_id', '')
    tag_text = request.GET.get('kategorija', '').strip()
    fakultet_id = request.GET.get('fakultet', '')

    if query:
        skripte = skripte.filter(Q(naziv__icontains=query) | Q(opis__icontains=query))

    final_tag_id = None
    if tag_id:
        final_tag_id = tag_id
    elif tag_text:
        cat = Kategorija.objects.filter(naziv__icontains=tag_text).first()
        if cat:
            final_tag_id = cat.idkat

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
    korisnik = Korisnik.objects.get(kor_ime= request.user.get_username())

    sacuvane = Sacuvano.objects.filter(idkor=korisnik).select_related("idskr")

    skripte = []

    for s in sacuvane:
        skripta = s.idskr
        skripta.is_focus = (s.kolekcija == "focus")
        skripte.append(skripta)

    return render(request, "saved_scripts.html", {"skripte": skripte})