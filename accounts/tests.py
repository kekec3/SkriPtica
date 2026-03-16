"""
TESTOVI ZA ACCOUNTS APP — Skriptica projekat
=============================================
Pokreni sa: python manage.py test accounts

Obuhvata:
  - Modele (Role, Korisnik)
  - View-ove (login, logout, moderator_dashboard, approve_script,
               delete_script, admin_dashboard, promote_to_moderator,
               demote_to_user)
  - Permisije (ko sme šta da vidi/radi)
"""
from django.db import connection
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import Korisnik, Role
from materials.models import Kategorija, Skripta


# ──────────────────────────────────────────────────────────────
# POMOĆNA KLASA — sve zajedničke setUp metode na jednom mestu
# Svaka test klasa koja nasledi BaseTestCase dobija već kreirane
# objekte: role_korisnik, role_moderator, role_admin, i metodu
# make_user() koja pravi par (User, Korisnik) u jednoj liniji.
# ──────────────────────────────────────────────────────────────

class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS sacuvano
                           (
                               IdKor
                               INT
                               NOT
                               NULL,
                               IdSkr
                               INT
                               NOT
                               NULL,
                               Kolekcija
                               VARCHAR
                           (
                               18
                           ),
                               PRIMARY KEY
                           (
                               IdKor,
                               IdSkr
                           ),
                               FOREIGN KEY
                           (
                               IdKor
                           ) REFERENCES korisnik
                           (
                               IdKor
                           ),
                               FOREIGN KEY
                           (
                               IdSkr
                           ) REFERENCES skripta
                           (
                               IdSkr
                           )
                               )
                           """)

    @classmethod
    def tearDownClass(cls):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS sacuvano")
        super().tearDownClass()
    def setUp(self):
        # Kreiramo tri uloge koje aplikacija koristi
        self.role_korisnik = Role.objects.create(idrol=1, opis='korisnik')
        self.role_moderator = Role.objects.create(idrol=2, opis='moderator')
        self.role_admin = Role.objects.create(idrol=3, opis='admin')

        # Kategorija je potrebna da bismo mogli da napravimo skriptu
        self.kategorija = Kategorija.objects.create(naziv='Matematika', tip='Predmet')

    def make_user(self, username, role, password='testpass123'):
        """Pravi Django User + odgovarajući Korisnik i vraća oba."""
        auth_user = User.objects.create_user(username=username, password=password)
        korisnik  = Korisnik.objects.create(
            kor_ime=username,
            lozinka=password,
            email=f'{username}@test.com',
            idrol=role,
        )
        return auth_user, korisnik

    def login_user(self, client, auth_user, korisnik, password='testpass123'):
        """Loguje korisnika i postavlja session['user_id'] kao što views rade."""
        client.login(username=auth_user.username, password=password)
        session = client.session
        session['user_id'] = korisnik.idkor
        session.save()

    def make_skripta(self, korisnik, odobrena=0):
        """Pravi skriptu vezanu za dati Korisnik objekat."""
        return Skripta.objects.create(
            idkor=korisnik,
            idkat=self.kategorija,
            naziv='Test skripta',
            opis='Opis test skripte',
            fajl='skripte/dummy.pdf',
            odobrena=odobrena,
        )


# ══════════════════════════════════════════════════════════════
#  1. TESTOVI MODELA
# ══════════════════════════════════════════════════════════════

class RoleModelTest(BaseTestCase):
    """Proveravamo da Role model ispravno čuva podatke."""

    def test_role_se_kreira(self):
        """Role sa opisom 'korisnik' treba da postoji u bazi."""
        role = Role.objects.get(opis='korisnik')
        self.assertEqual(role.opis, 'korisnik')

    def test_sve_tri_role_postoje(self):
        """Aplikacija zavisi od tačno tri uloge — sve moraju postojati."""
        opisi = list(Role.objects.values_list('opis', flat=True))
        self.assertIn('korisnik',  opisi)
        self.assertIn('moderator', opisi)
        self.assertIn('admin',     opisi)


class KorisnikModelTest(BaseTestCase):
    """Proveravamo da Korisnik model ispravno čuva podatke."""

    def test_korisnik_se_kreira(self):
        """Kreiran korisnik treba da se može naći u bazi."""
        _, korisnik = self.make_user('pera', self.role_korisnik)
        iz_baze = Korisnik.objects.get(kor_ime='pera')
        self.assertEqual(iz_baze.email, 'pera@test.com')

    def test_podrazumevana_rola_je_korisnik(self):
        """Novi korisnik treba da ima ulogu 'korisnik'."""
        _, korisnik = self.make_user('mika', self.role_korisnik)
        self.assertEqual(korisnik.idrol.opis, 'korisnik')

    def test_korisnik_moze_dobiti_moderator_ulogu(self):
        """Promenom idrol polja Korisnik treba da postane moderator."""
        _, korisnik = self.make_user('zika', self.role_korisnik)
        korisnik.idrol = self.role_moderator
        korisnik.save()
        iz_baze = Korisnik.objects.get(pk=korisnik.pk)
        self.assertEqual(iz_baze.idrol.opis, 'moderator')


# ══════════════════════════════════════════════════════════════
#  2. TESTOVI LOGIN / LOGOUT VIEW-OVA
# ══════════════════════════════════════════════════════════════

class LoginViewTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('login')  # prilagodi ako je url drugačiji
        self.auth_user, self.korisnik = self.make_user('pera', self.role_korisnik)

    def test_login_stranica_se_ucitava(self):
        """GET /login/ treba da vrati status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ulogovan_korisnik_se_preusmerava_sa_login(self):
        self.client.login(username='pera', password='testpass123')
        response = self.client.get(self.url)
        # View preusmerava na 'index', ne na search_page
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)

    def test_uspesna_prijava(self):
        response = self.client.post(self.url, {
            'action': 'login',
            'username': 'pera',
            'password': 'testpass123',
        }, follow=True)  # ← dodaj follow=True
        self.assertEqual(response.status_code, 200)

    def test_pogresna_lozinka(self):
        """POST sa pogrešnom lozinkom treba da vrati grešku."""
        response = self.client.post(self.url, {
            'action':   'login',
            'username': 'pera',
            'password': 'pogresna',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pogrešna lozinka')

    def test_nepostojeci_korisnik(self):
        """POST sa nepostojećim username treba da vrati grešku."""
        response = self.client.post(self.url, {
            'action':   'login',
            'username': 'nepostoji',
            'password': 'bilo_sta',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ne postoji korisnik')

    def test_registracija_novog_korisnika(self):
        response = self.client.post(self.url, {
            'action': 'register',
            'username': 'novi_user',
            'password1': 'JakaLozinka123!',
            'password2': 'JakaLozinka123!',
            'email': 'novi@test.com',
        }, follow=True)  # ← dodaj follow=True
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='novi_user').exists())


class LogoutViewTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_user, self.korisnik = self.make_user('pera', self.role_korisnik)

    def test_logout_preusmerava(self):
        """Nakon odjave korisnik treba da bude preusmeren."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        response = self.client.get(reverse('logout'))
        # Proveravamo samo da je redirect (3xx)
        self.assertIn(response.status_code, [301, 302])

    def test_logout_brise_sesiju(self):
        """Nakon odjave user_id ne sme biti u sesiji."""
        self.login_user(self.client, self.auth_user, self.korisnik)
        self.client.get(reverse('logout'))
        self.assertNotIn('user_id', self.client.session)


# ══════════════════════════════════════════════════════════════
#  3. TESTOVI MODERATOR DASHBOARD-a
# ══════════════════════════════════════════════════════════════

class ModeratorDashboardTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('moderator_dashboard')

        self.auth_mod, self.moderator   = self.make_user('mod1', self.role_moderator)
        self.auth_user, self.obican     = self.make_user('user1', self.role_korisnik)

        # Skripta koja čeka odobrenje
        self.skripta = self.make_skripta(self.obican, odobrena=0)

    def test_moderator_vidi_dashboard(self):
        """Moderator treba da dobije 200 na dashboard stranici."""
        self.login_user(self.client, self.auth_mod, self.moderator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_obican_korisnik_ne_moze_dashboard(self):
        """Običan korisnik ne sme da pristupi moderator dashboardu."""
        self.login_user(self.client, self.auth_user, self.obican)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # redirect

    def test_nelogovan_ne_moze_dashboard(self):
        """Nelogovani korisnik ne sme pristupiti dashboardu."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_prikazuje_neodbrane_skripte(self):
        """Dashboard treba da prikaže skripte koje čekaju odobrenje."""
        self.login_user(self.client, self.auth_mod, self.moderator)
        response = self.client.get(self.url)
        self.assertIn(self.skripta, response.context['skripte'])


class ApproveScriptTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_mod, self.moderator = self.make_user('mod1', self.role_moderator)
        self.auth_user, self.obican   = self.make_user('user1', self.role_korisnik)
        self.skripta = self.make_skripta(self.obican, odobrena=0)

    def test_moderator_moze_odobriti_skriptu(self):
        """POST od moderatora treba da postavi odobrena=1."""
        self.login_user(self.client, self.auth_mod, self.moderator)
        self.client.post(reverse('approve_script', args=[self.skripta.pk]))
        self.skripta.refresh_from_db()
        self.assertEqual(self.skripta.odobrena, 1)

    def test_obican_korisnik_ne_moze_odobriti(self):
        """Običan korisnik ne sme odobriti skriptu."""
        self.login_user(self.client, self.auth_user, self.obican)
        self.client.post(reverse('approve_script', args=[self.skripta.pk]))
        self.skripta.refresh_from_db()
        # Skripta i dalje nije odobrena
        self.assertEqual(self.skripta.odobrena, 0)


class DeleteScriptTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_mod, self.moderator = self.make_user('mod1', self.role_moderator)
        self.auth_user, self.obican   = self.make_user('user1', self.role_korisnik)

    def test_moderator_moze_brisati_skriptu(self):
        """POST od moderatora treba da obriše skriptu iz baze."""
        skripta = self.make_skripta(self.obican)
        self.login_user(self.client, self.auth_mod, self.moderator)
        self.client.post(reverse('delete_script', args=[skripta.pk]))
        self.assertFalse(Skripta.objects.filter(pk=skripta.pk).exists())

    def test_obican_korisnik_ne_moze_brisati(self):
        """Običan korisnik ne sme brisati skriptu."""
        skripta = self.make_skripta(self.obican)
        self.login_user(self.client, self.auth_user, self.obican)
        self.client.post(reverse('delete_script', args=[skripta.pk]))
        # Skripta i dalje postoji
        self.assertTrue(Skripta.objects.filter(pk=skripta.pk).exists())


# ══════════════════════════════════════════════════════════════
#  4. TESTOVI ADMIN DASHBOARD-a
# ══════════════════════════════════════════════════════════════

class AdminDashboardTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_admin, self.admin   = self.make_user('admin1', self.role_admin)
        self.auth_mod, self.moderator = self.make_user('mod1',   self.role_moderator)
        self.auth_user, self.obican   = self.make_user('user1',  self.role_korisnik)
        self.url = reverse('admin_dashboard')

    def test_admin_vidi_dashboard(self):
        """Admin treba da dobije 200 na admin dashboardu."""
        self.login_user(self.client, self.auth_admin, self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_moderator_ne_moze_admin_dashboard(self):
        """Moderator ne sme pristupiti admin dashboardu."""
        self.login_user(self.client, self.auth_mod, self.moderator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_obican_korisnik_ne_moze_admin_dashboard(self):
        """Običan korisnik ne sme pristupiti admin dashboardu."""
        self.login_user(self.client, self.auth_user, self.obican)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class PromoteDemoteTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.auth_admin, self.admin = self.make_user('admin1', self.role_admin)
        self.auth_user, self.obican = self.make_user('user1',  self.role_korisnik)

    def test_admin_moze_promovisati_u_moderatora(self):
        """Admin POST treba da promeni ulogu korisnika u moderatora."""
        self.login_user(self.client, self.auth_admin, self.admin)
        self.client.post(reverse('promote_to_moderator', args=[self.obican.pk]))
        self.obican.refresh_from_db()
        self.assertEqual(self.obican.idrol.opis, 'moderator')

    def test_admin_moze_degradirati_moderatora(self):
        """Admin POST treba da vrati moderatora na ulogu korisnika."""
        self.obican.idrol = self.role_moderator
        self.obican.save()
        self.login_user(self.client, self.auth_admin, self.admin)
        self.client.post(reverse('demote_to_user', args=[self.obican.pk]))
        self.obican.refresh_from_db()
        self.assertEqual(self.obican.idrol.opis, 'korisnik')

    def test_admin_ne_moze_promeniti_drugog_admina(self):
        """Admin ne sme menjati ulogu drugog admina."""
        _, drugi_admin = self.make_user('admin2', self.role_admin)
        self.login_user(self.client, self.auth_admin, self.admin)
        self.client.post(reverse('promote_to_moderator', args=[drugi_admin.pk]))
        drugi_admin.refresh_from_db()
        # Uloga treba da ostane admin
        self.assertEqual(drugi_admin.idrol.opis, 'admin')

    def test_obican_korisnik_ne_moze_promovisati(self):
        """Običan korisnik ne sme koristiti promote endpoint."""
        _, drugi = self.make_user('user2', self.role_korisnik)
        self.login_user(self.client, self.auth_user, self.obican)
        self.client.post(reverse('promote_to_moderator', args=[drugi.pk]))
        drugi.refresh_from_db()
        # Uloga se ne sme promeniti
        self.assertEqual(drugi.idrol.opis, 'korisnik')