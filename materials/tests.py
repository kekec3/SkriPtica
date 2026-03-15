from django.test import TestCase, Client
from django.urls import reverse

from materials.models import Skripta, Kategorija, Sacuvano, Komentar
from accounts.models import Korisnik, Role


class MaterialsViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Role
        self.role = Role.objects.create(opis="student")

        # User
        self.user = Korisnik.objects.create(
            idrol=self.role,
            kor_ime="testuser",
            lozinka="123",
            email="test@test.com"
        )

        # Category
        self.category = Kategorija.objects.create(
            naziv="ETF",
            tip="Fakultet"
        )

        # Script
        self.script = Skripta.objects.create(
            idkor=self.user,
            idkat=self.category,
            naziv="Test Skripta",
            opis="Opis skripte",
            fajl="skripte/test.pdf",
            odobrena=1
        )


    # ------------------------------
    # TEST READ SCRIPT PAGE
    # ------------------------------
    def test_read_script_page_loads(self):

        url = reverse('materials:read_script', args=[self.script.idskr])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Skripta")


    # ------------------------------
    # TEST SAVE SCRIPT
    # ------------------------------
    def test_save_script(self):

        url = reverse('materials:read_script', args=[self.script.idskr])

        response = self.client.post(url, {
            "action": "sacuvaj"
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Sacuvano.objects.filter(idskr=self.script).exists()
        )


    # ------------------------------
    # TEST DELETE SAVED SCRIPT
    # ------------------------------
    def test_delete_saved_script(self):

        Sacuvano.objects.create(
            idkor=self.user,
            idskr=self.script
        )

        url = reverse('materials:read_script', args=[self.script.idskr])

        self.client.post(url, {
            "action": "zaboravi"
        })

        self.assertFalse(
            Sacuvano.objects.filter(idskr=self.script).exists()
        )


    # ------------------------------
    # TEST ADD COMMENT
    # ------------------------------
    def test_add_comment(self):

        url = reverse('materials:read_script', args=[self.script.idskr])

        self.client.post(url, {
            "action": "komentar",
            "komentar": "Odlicna skripta"
        })

        self.assertTrue(
            Komentar.objects.filter(idskr=self.script).exists()
        )


    # ------------------------------
    # TEST SEARCH PAGE
    # ------------------------------
    def test_search_page(self):

        url = reverse('materials:search_page')

        response = self.client.get(url, {
            "q": "Test"
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Skripta")


    # ------------------------------
    # TEST CATEGORY AUTOCOMPLETE
    # ------------------------------
    def test_category_autocomplete(self):

        url = reverse('materials:category_autocomplete')

        response = self.client.get(url, {
            "q": "ETF"
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ETF")


    # ------------------------------
    # TEST SAVED SCRIPTS PAGE
    # ------------------------------
    def test_saved_scripts_page(self):

        Sacuvano.objects.create(
            idkor=self.user,
            idskr=self.script,
            kolekcija="focus"
        )

        url = reverse('materials:saved_scripts')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)