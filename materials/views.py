'''
Authors: Andrej Praizović 0300/2022, Jaksa Jezdić 0543/2022
'''

from django.db.models import Q, Avg
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
    """
    Opis: Vraća JSON listu kategorija čiji naziv odgovara prosleđenom query parametru 'q'.
          Koristi se za autocomplete polje pri pretrazi ili dodavanju skripte.
          Vraća maksimalno 6 rezultata.

    Tabele baze: :model:`materials.Kategorija`

    Template: (nema — vraća JsonResponse)
    """
    query = request.GET.get('q', '')
    categories = Kategorija.objects.filter(naziv__icontains=query)[:6]
    data = [{'id': c.pk, 'name': c.naziv} for c in categories]
    return JsonResponse(data, safe=False)


def add_script(request):
    """
    Opis: Prikazuje formu za dodavanje nove skripte i obrađuje njeno slanje.
          Po uspješnom čuvanju, skripta se vezuje za trenutno prijavljenog korisnika
          i postavlja u status "nije odobrena" (odobrena=0), nakon čega se korisnik
          preusmjerava na stranicu pretrage.

    Tabele baze: :model:`materials.Skripta`
                 :model:`accounts.Korisnik`

    Template: :template:`materials/add_script.html`
    """
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
            return redirect('/materials/search/')
        else:
            # DEBUG: This will show you in the terminal WHY the form is invalid
            print(form.errors)
            return render(request, 'add_script.html', {'form': form, 'error': form.errors})

    return render(request, 'add_script.html')

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def summarize_pdf(pdf_path):
    """
    Opis: Prima putanju do PDF fajla, čita njegov tekst i putem Groq API-ja
          (model llama-3.3-70b-versatile) generiše kratak rezime skripte od 3 do 5 rečenica
          na srpskom jeziku. Koristi se unutar read_script view-a.

    Tabele baze: (nema direktnog pristupa)
    """
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
    """
    Opis: Prima putanju do PDF fajla, čita njegov tekst i putem Groq API-ja
          (model llama-3.3-70b-versatile) generiše tačno 5 pitanja za provjeru znanja
          vezanih za sadržaj skripte. Pitanja su na srpskom jeziku i numerisana od 1 do 5.

    Tabele baze: (nema direktnog pristupa)
    """
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
    """
    Opis: Prikazuje detalje odabrane skripte zajedno sa komentarima, ocjenom
          korisnika i statusom čuvanja. Omogućava prijavljenim korisnicima da:
          ostave ili ažuriraju komentar, sačuvaju ili uklone skriptu iz liste,
          ocijene skriptu, te generišu AI rezime ili pitanja za provjeru znanja.
          Gostima je dostupan samo pregled sadržaja.

    Tabele baze: :model:`materials.Skripta`
                 :model:`materials.Komentar`
                 :model:`materials.Sacuvano`
                 :model:`materials.Ocena`
                 :model:`accounts.Korisnik`

    Template: :template:`materials/read_script.html`
    """
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
                updated = Ocena.objects.filter(
                    idkor=korisnik,
                    idskr=script
                ).update(ocena=rating_value)
                if not updated:
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
        'questions': questions
    }
    return render(request, 'read_script.html', context)

def get_all_subcategories(category_id):
    """
    Opis: Rekurzivna pomoćna funkcija koja vraća listu ID-jeva zadate kategorije
          i svih njenih podkategorija (na svim nivoima hijerarhije).
          Koristi se pri filtriranju skripti po kategoriji ili fakultetu.

    Tabele baze: :model:`materials.KategorijaNad`
    """
    all_ids = [category_id]

    children = KategorijaNad.objects.filter(
        idkatnad_id=category_id
    ).values_list('idkatpod_id', flat=True)

    for child_id in children:
        all_ids.extend(get_all_subcategories(child_id))

    return list(set(all_ids))


def search_page(request):
    """
    Opis: Prikazuje stranicu za pretragu odobrenih skripti sa mogućnošću filtriranja
          po ključnoj reči (naziv ili opis), tagu (kategoriji) i fakultetu.
          Svaka skripta je anotirana prosječnom ocjenom. Pretraga po kategoriji
          uključuje sve podkategorije rekurzivno.

    Tabele baze: :model:`materials.Skripta`
                 :model:`materials.Kategorija`
                 :model:`materials.KategorijaNad`
                 :model:`materials.Ocena`

    Template: :template:`materials/Search.html`
    """
    fakulteti = Kategorija.objects.filter(tip='Fakultet')
    skripte = Skripta.objects.filter(odobrena=1).annotate(
        avg_rating=Avg('ocena__ocena')
    )

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
    """
    Opis: Prikazuje listu skripti koje je prijavljeni korisnik sačuvao.
          Za svaku skriptu označava da li pripada kolekciji "focus".

    Tabele baze: :model:`materials.Sacuvano`
                 :model:`materials.Skripta`
                 :model:`accounts.Korisnik`

    Template: :template:`materials/saved_scripts.html`
    """
    user_id = request.session.get('user_id')
    korisnik = Korisnik.objects.get(idkor=user_id)

    sacuvane = Sacuvano.objects.filter(idkor=korisnik).select_related("idskr")

    skripte = []

    for s in sacuvane:
        skripta = s.idskr
        skripta.is_focus = (s.kolekcija == "focus")
        skripte.append(skripta)

    return render(request, "saved_scripts.html", {"skripte": skripte})
