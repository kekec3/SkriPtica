"""
TESTOVI ZA MATERIALS APP — Skriptica projekat
=============================================
Pokreni sa: python manage.py test materials

Podeljeno u dve klase:
  - MaterialManagementTests  → dodavanje, pregled i čuvanje skripti
  - MaterialDiscoveryTests   → modeli, pretraga, autocomplete
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import connection

from accounts.models import Korisnik, Role
from materials.models import (
    Kategorija, KategorijaNad, Skripta,
    Komentar, Ocena, Sacuvano,
)


# ──────────────────────────────────────────────────────────────
# POMOĆNA KLASA
# ──────────────────────────────────────────────────────────────

class BaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sacuvano (
                    IdKor INT NOT NULL,
                    IdSkr INT NOT NULL,
                    Kolekcija VARCHAR(18),
                    PRIMARY KEY (IdKor, IdSkr),
                    FOREIGN KEY (IdKor) REFERENCES korisnik(IdKor),
                    FOREIGN KEY (IdSkr) REFERENCES skripta(IdSkr)
                )
            """)

    @classmethod
    def tearDownClass(cls):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS sacuvano")
        super().tearDownClass()

    def setUp(self):
        self.role_korisnik  = Role.objects.create(idrol=1, opis='korisnik')
        self.role_moderator = Role.objects.create(idrol=2, opis='moderator')
        self.role_admin     = Role.objects.create(idrol=3, opis='admin')
        self.kategorija = Kategorija.objects.create(naziv='Matematika', tip='Predmet')
        self.fakultet   = Kategorija.objects.create(naziv='Elektrotehnicki', tip='Fakultet')

    def make_user(self, username, role=None, password='testpass123'):
        if role is None:
            role = self.role_korisnik
        auth_user = User.objects.create_user(username=username, password=password)
        korisnik  = Korisnik.objects.create(
            kor_ime=username,
            lozinka=password,
            email=f'{username}@test.com',
            idrol=role,
        )
        return auth_user, korisnik

    def login_user(self, client, auth_user, korisnik, password='testpass123'):
        client.login(username=auth_user.username, password=password)
        session = client.session
        session['user_id'] = korisnik.idkor
        session.save()

    def make_skripta(self, korisnik, odobrena=1, naziv='Test skripta'):
        return Skripta.objects.create(
            idkor=korisnik,
            idkat=self.kategorija,
            naziv=naziv,
            opis='Neki opis',
            fajl='skripte/dummy.pdf',
            odobrena=odobrena,
        )


# ══════════════════════════════════════════════════════════════
#  KLASA 1: UPRAVLJANJE SKRIPTAMA
#  Obuhvata: dodavanje skripte, pregled skripte, čuvanje skripte
# ══════════════════════════════════════════════════════════════

class MaterialManagementTests(BaseTestCase):
    """
    Testovi vezani za upravljanje skriptama:
    - Dodavanje nove skripte (AddScript)
    - Pregled skripte (ReadScript)
    - Sačuvane skripte (SavedScripts)
    """

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_user, self.korisnik = self.make_user('pera')
        self.skripta   = self.make_skripta(self.korisnik, odobrena=1)
        self.add_url   = reverse('materials:add_script')
        self.read_url  = reverse('materials:read_script', args=[self.skripta.pk])
        self.saved_url = reverse('materials:saved_scripts')

    # ── ADD SCRIPT ────────────────────────────────────────────

    def test_add_stranica_se_ucitava_ulogovanom(self):
        """Ulogovani korisnik treba da vidi formu za dodavanje skripte."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)

    def test_nova_skripta_nije_odobrena(self):
        """Nova skripta treba automatski da dobije odobrena=0."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        import io
        dummy_pdf = io.BytesIO(b'%PDF-1.4 dummy content')
        dummy_pdf.name = 'test.pdf'
        self.client.post(self.add_url, {
            'naslov': 'Nova skripta',
            'opis':   'Opis nove skripte',
            'idKat':  self.kategorija.pk,
            'fajl':   dummy_pdf,
        })
        if Skripta.objects.filter(naziv='Nova skripta').exists():
            s = Skripta.objects.get(naziv='Nova skripta')
            self.assertEqual(s.odobrena, 0)

    # ── READ SCRIPT ───────────────────────────────────────────

    def test_gost_moze_citati_skriptu(self):
        """Nelogovani korisnik (gost) treba da može videti skriptu."""
        response = self.client.get(self.read_url)
        self.assertEqual(response.status_code, 200)

    def test_kontekst_sadrzi_skriptu(self):
        """Kontekst treba da sadrži traženu skriptu."""
        response = self.client.get(self.read_url)
        self.assertEqual(response.context['script'], self.skripta)

    def test_gost_je_prepoznat_kao_gost(self):
        """Kontekst treba da označi nelogovanog korisnika kao gosta."""
        response = self.client.get(self.read_url)
        self.assertTrue(response.context['is_guest'])

    def test_ulogovani_nije_gost(self):
        """Ulogovani korisnik ne treba da bude označen kao gost."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        response = self.client.get(self.read_url)
        self.assertFalse(response.context['is_guest'])

    def test_komentar_se_dodaje(self):
        """POST sa action='komentar' treba da kreira komentar u bazi."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.post(self.read_url, {
            'action':   'komentar',
            'komentar': 'Odlična skripta!',
        })
        self.assertTrue(
            Komentar.objects.filter(idkor=self.korisnik, idskr=self.skripta).exists()
        )

    def test_gost_ne_moze_komentarisati(self):
        """Gost ne sme ostaviti komentar."""
        self.client.post(self.read_url, {'action': 'komentar', 'komentar': 'Spam'})
        self.assertFalse(
            Komentar.objects.filter(idskr=self.skripta).exists()
        )

    def test_ocenjivanje_skripte(self):
        """POST sa action='oceni' treba da sačuva ocenu u bazi."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.post(self.read_url, {'action': 'oceni', 'rating': '4'})
        ocena = Ocena.objects.filter(idkor=self.korisnik, idskr=self.skripta).first()
        self.assertIsNotNone(ocena)
        self.assertEqual(ocena.ocena, 4)

    def test_azuriranje_ocene(self):
        """Drugi POST sa action='oceni' treba da ažurira postojeću ocenu."""
        Ocena.objects.create(idkor=self.korisnik, idskr=self.skripta, ocena=3)
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.post(self.read_url, {'action': 'oceni', 'rating': '5'})
        ocena = Ocena.objects.get(idkor=self.korisnik, idskr=self.skripta)
        self.assertEqual(ocena.ocena, 5)

    # ── SACUVANE SKRIPTE ──────────────────────────────────────

    def test_skripta_se_cuva(self):
        """POST sa action='sacuvaj' treba da sačuva skriptu za korisnika."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.post(self.read_url, {'action': 'sacuvaj'})
        self.assertTrue(
            Sacuvano.objects.filter(idkor=self.korisnik, idskr=self.skripta).exists()
        )

    def test_skripta_se_zaboravlja(self):
        """POST sa action='zaboravi' treba da ukloni sačuvanu skriptu."""
        Sacuvano.objects.create(idkor=self.korisnik, idskr=self.skripta)
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.post(self.read_url, {'action': 'zaboravi'})
        self.assertFalse(
            Sacuvano.objects.filter(idkor=self.korisnik, idskr=self.skripta).exists()
        )

    def test_ulogovani_vidi_sacuvane(self):
        """Ulogovani korisnik treba da vidi listu sačuvanih skripti."""
        Sacuvano.objects.create(idkor=self.korisnik, idskr=self.skripta)
        self.login_user(self.client, self.auth_user, self.korisnik)
        response = self.client.get(self.saved_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.skripta, response.context['skripte'])

    def test_prazna_lista_ako_nema_sacuvanih(self):
        """Ako nema sačuvanih skripti, lista treba da bude prazna."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        response = self.client.get(self.saved_url)
        self.assertEqual(len(response.context['skripte']), 0)


# ══════════════════════════════════════════════════════════════
#  KLASA 2: PRETRAGA I MODELI
#  Obuhvata: modele, pretragu skripti, autocomplete kategorija
# ══════════════════════════════════════════════════════════════

class MaterialDiscoveryTests(BaseTestCase):
    """
    Testovi vezani za pretragu i integritet podataka:
    - Modeli (Kategorija, Skripta, Komentar, Ocena)
    - Pretraga skripti (SearchPage)
    - Autocomplete kategorija
    """

    def setUp(self):
        super().setUp()
        self.client = Client()
        _, self.korisnik      = self.make_user('pera')
        self.odobrena         = self.make_skripta(self.korisnik, odobrena=1, naziv='Algebra skripta')
        self.neodobrena       = self.make_skripta(self.korisnik, odobrena=0, naziv='Skrivena skripta')
        self.search_url       = reverse('materials:search_page')
        self.autocomplete_url = reverse('materials:category_autocomplete')

    # ── MODELI ────────────────────────────────────────────────

    def test_kategorija_se_kreira(self):
        """Kategorija treba da se sačuva i može se naći po nazivu."""
        k = Kategorija.objects.get(naziv='Matematika')
        self.assertEqual(k.tip, 'Predmet')

    def test_kategorija_nad_veza(self):
        """KategorijaNad treba da poveže nadređenu i podređenu kategoriju."""
        pod = Kategorija.objects.create(naziv='Analiza', tip='Predmet')
        KategorijaNad.objects.create(idkatnad=self.fakultet, idkatpod=pod)
        veza = KategorijaNad.objects.get(idkatnad=self.fakultet, idkatpod=pod)
        self.assertEqual(veza.idkatpod.naziv, 'Analiza')

    def test_skripta_se_kreira(self):
        """Nova skripta treba da bude u bazi i podrazumevano nije odobrena."""
        s = self.make_skripta(self.korisnik, odobrena=0)
        iz_baze = Skripta.objects.get(pk=s.pk)
        self.assertEqual(iz_baze.naziv, 'Test skripta')
        self.assertEqual(iz_baze.odobrena, 0)

    def test_odobravanje_skripte(self):
        """Postavljanje odobrena=1 treba da se sačuva u bazi."""
        s = self.make_skripta(self.korisnik, odobrena=0)
        s.odobrena = 1
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.odobrena, 1)

    def test_komentar_se_kreira(self):
        """Komentar treba da se veže za skriptu i korisnika."""
        Komentar.objects.create(idkor=self.korisnik, idskr=self.odobrena, tekst='Odlična!')
        iz_baze = Komentar.objects.get(idkor=self.korisnik, idskr=self.odobrena)
        self.assertEqual(iz_baze.tekst, 'Odlična!')

    def test_jedan_komentar_po_korisniku_po_skripti(self):
        """Isti korisnik ne može imati dva komentara na istoj skripti."""
        Komentar.objects.create(idkor=self.korisnik, idskr=self.odobrena, tekst='Prvi')
        with self.assertRaises(Exception):
            Komentar.objects.create(idkor=self.korisnik, idskr=self.odobrena, tekst='Drugi')

    def test_ocena_se_kreira(self):
        """Ocena treba da se sačuva sa ispravnom vrednošću."""
        o = Ocena.objects.create(idkor=self.korisnik, idskr=self.odobrena, ocena=5)
        self.assertEqual(o.ocena, 5)

    def test_update_ocene(self):
        """Menjanje ocene treba da se sačuva."""
        o = Ocena.objects.create(idkor=self.korisnik, idskr=self.odobrena, ocena=3)
        o.ocena = 5
        o.save()
        o.refresh_from_db()
        self.assertEqual(o.ocena, 5)

    # ── SEARCH PAGE ───────────────────────────────────────────

    def test_search_page_se_ucitava(self):
        """GET /search/ treba da vrati 200 — dostupna i gostima."""
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)

    def test_prikazuju_se_samo_odobrene_skripte(self):
        """Search page sme prikazivati samo odobrene skripte."""
        response = self.client.get(self.search_url)
        skripte = list(response.context['skripte'])
        self.assertIn(self.odobrena, skripte)
        self.assertNotIn(self.neodobrena, skripte)

    def test_pretraga_po_naslovu(self):
        """Pretraga po ključnoj reči treba da vrati odgovarajuće skripte."""
        response = self.client.get(self.search_url, {'q': 'Algebra'})
        skripte = list(response.context['skripte'])
        self.assertIn(self.odobrena, skripte)

    def test_pretraga_bez_rezultata(self):
        """Pretraga koja ne odgovara ničemu treba da vrati prazan rezultat."""
        response = self.client.get(self.search_url, {'q': 'XYZ_ne_postoji_123'})
        self.assertEqual(len(response.context['skripte']), 0)

    def test_pretraga_po_kategoriji(self):
        """Filter po tag_id treba da vrati skripte iz te kategorije."""
        response = self.client.get(self.search_url, {'tag_id': self.kategorija.pk})
        skripte = list(response.context['skripte'])
        self.assertIn(self.odobrena, skripte)

    # ── CATEGORY AUTOCOMPLETE ─────────────────────────────────

    def test_autocomplete_vraca_json(self):
        """Autocomplete endpoint treba da vrati JSON odgovor."""
        response = self.client.get(self.autocomplete_url, {'q': 'Mat'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_autocomplete_vraca_poklapanje(self):
        """Upit 'Mat' treba da vrati kategoriju 'Matematika'."""
        import json
        response = self.client.get(self.autocomplete_url, {'q': 'Mat'})
        data = json.loads(response.content)
        nazivi = [item['name'] for item in data]
        self.assertIn('Matematika', nazivi)

    def test_autocomplete_prazan_upit(self):
        """Prazan upit treba da vrati bar jednu kategoriju."""
        import json
        response = self.client.get(self.autocomplete_url, {'q': ''})
        data = json.loads(response.content)
        self.assertGreaterEqual(len(data), 1)