from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from materials.views import (
    category_autocomplete,
    read_script,
    search_page,
    saved_scripts,
    get_all_subcategories, add_script,
)
from materials.models import Kategorija, KategorijaNad, Skripta, Komentar
from accounts.models import Korisnik, Role


class MaterialsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.role = Role.objects.create(opis="student")

        # Bitno: view hardkoduje idkor=2
        self.korisnik = Korisnik.objects.create(
            idkor=2,
            idrol=self.role,
            kor_ime="jaksa",
            lozinka="123",
            email="jaksa@test.com"
        )

        self.kat_fak = Kategorija.objects.create(
            naziv="ETF",
            tip="Fakultet"
        )

        self.kat_predmet = Kategorija.objects.create(
            naziv="PSI",
            tip="Predmet"
        )

        self.skripta = Skripta.objects.create(
            idkor=self.korisnik,
            idkat=self.kat_predmet,
            naziv="Test Skripta",
            opis="Opis test skripte",
            fajl="skripte/test.pdf",
            odobrena=1
        )

    def fake_render(self, request, template_name, context=None, *args, **kwargs):
        response = HttpResponse("OK")
        response.template_name = template_name
        response.context_data = context or {}
        return response

    def test_category_autocomplete_returns_matching_categories(self):
        request = self.factory.get("/materials/api/categories/", {"q": "ET"})
        response = category_autocomplete(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("ETF", response.content.decode())

    def test_get_all_subcategories_returns_parent_and_children(self):
        child = Kategorija.objects.create(naziv="Softversko", tip="Smer")
        grandchild = Kategorija.objects.create(naziv="PSI Lab", tip="Predmet")

        KategorijaNad.objects.create(idkatnad=self.kat_fak, idkatpod=child)
        KategorijaNad.objects.create(idkatnad=child, idkatpod=grandchild)

        result = get_all_subcategories(self.kat_fak.idkat)

        self.assertIn(self.kat_fak.idkat, result)
        self.assertIn(child.idkat, result)
        self.assertIn(grandchild.idkat, result)

    @patch("materials.views.render")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_read_script_get_loads_page(self, mock_sacuvano_filter, mock_render):
        mock_sacuvano_filter.return_value.exists.return_value = False
        mock_render.side_effect = self.fake_render

        request = self.factory.get(f"/materials/read_script/{self.skripta.idskr}/")
        response = read_script(request, self.skripta.idskr)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "read_script.html")
        self.assertEqual(response.context_data["script"].naziv, "Test Skripta")
        self.assertFalse(response.context_data["is_saved"])

    @patch("materials.views.redirect")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_read_script_post_zaboravi_deletes_saved(self, mock_sacuvano_filter, mock_redirect):
        mock_redirect.return_value = HttpResponse("REDIRECT")

        request = self.factory.post(
            f"/materials/read_script/{self.skripta.idskr}/",
            {"action": "zaboravi"}
        )
        response = read_script(request, self.skripta.idskr)

        mock_sacuvano_filter.return_value.delete.assert_called_once()
        mock_redirect.assert_called_once_with("materials:read_script", script_id=self.skripta.idskr)
        self.assertEqual(response.status_code, 200)

    @patch("materials.views.redirect")
    @patch("materials.views.Sacuvano.objects.update_or_create")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_read_script_post_sacuvaj_calls_update_or_create(self, mock_sacuvano_filter, mock_update_or_create, mock_redirect):
        mock_sacuvano_filter.return_value.exists.return_value = False
        mock_redirect.return_value = HttpResponse("REDIRECT")

        request = self.factory.post(
            f"/materials/read_script/{self.skripta.idskr}/",
            {"action": "sacuvaj", "focus": "on"}
        )
        response = read_script(request, self.skripta.idskr)

        mock_update_or_create.assert_called_once()
        _, kwargs = mock_update_or_create.call_args
        self.assertEqual(kwargs["idkor"], self.korisnik)
        self.assertEqual(kwargs["idskr"], self.skripta)
        self.assertEqual(kwargs["kolekcija"], "focus")
        mock_redirect.assert_called_once_with("materials:read_script", script_id=self.skripta.idskr)
        self.assertEqual(response.status_code, 200)

    @patch("materials.views.redirect")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_read_script_post_komentar_creates_or_updates_comment(self, mock_sacuvano_filter, mock_redirect):
        mock_sacuvano_filter.return_value.exists.return_value = False
        mock_redirect.return_value = HttpResponse("REDIRECT")

        request = self.factory.post(
            f"/materials/read_script/{self.skripta.idskr}/",
            {"action": "komentar", "komentar": "Odlicna skripta"}
        )
        response = read_script(request, self.skripta.idskr)

        self.assertTrue(
            Komentar.objects.filter(idkor=self.korisnik, idskr=self.skripta).exists()
        )
        komentar = Komentar.objects.get(idkor=self.korisnik, idskr=self.skripta)
        self.assertEqual(komentar.tekst, "Odlicna skripta")
        mock_redirect.assert_called_once_with("materials:read_script", script_id=self.skripta.idskr)
        self.assertEqual(response.status_code, 200)

    @patch("materials.views.render")
    @patch("materials.views.summarize_pdf")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_read_script_post_rezimiraj_sets_summary(self, mock_sacuvano_filter, mock_summarize_pdf, mock_render):
        mock_sacuvano_filter.return_value.exists.return_value = False
        mock_summarize_pdf.return_value = "Ovo je AI rezime."
        mock_render.side_effect = self.fake_render

        request = self.factory.post(
            f"/materials/read_script/{self.skripta.idskr}/",
            {"action": "rezimiraj"}
        )
        response = read_script(request, self.skripta.idskr)

        mock_summarize_pdf.assert_called_once_with(self.skripta.fajl.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["summary"], "Ovo je AI rezime.")

    @patch("materials.views.render")
    def test_search_page_filters_by_query(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.get("/materials/search/", {"q": "Test"})
        response = search_page(request)

        self.assertEqual(response.status_code, 200)
        skripte = list(response.context_data["skripte"])
        self.assertEqual(len(skripte), 1)
        self.assertEqual(skripte[0].naziv, "Test Skripta")

    @patch("materials.views.render")
    @patch("materials.views.Sacuvano.objects.filter")
    def test_saved_scripts_marks_focus_scripts(self, mock_sacuvano_filter, mock_render):
        mock_render.side_effect = self.fake_render

        fake_saved = MagicMock()
        fake_saved.idskr = self.skripta
        fake_saved.kolekcija = "focus"

        mock_sacuvano_filter.return_value.select_related.return_value = [fake_saved]

        request = self.factory.get("/materials/saved_scripts/")
        response = saved_scripts(request)

        self.assertEqual(response.status_code, 200)
        skripte = response.context_data["skripte"]
        self.assertEqual(len(skripte), 1)
        self.assertTrue(skripte[0].is_focus)

    @patch("materials.views.render")
    def test_add_script_get_loads_page(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.get("/materials/add_script/")
        request.user = AnonymousUser()

        response = add_script(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "add_script.html")

    def test_add_script_post_valid_creates_script_and_redirects(self):
        # add_script fallback koristi Korisnik.objects.get(pk=9)
        fallback_user = Korisnik.objects.create(
            idkor=9,
            idrol=self.role,
            kor_ime="fallback",
            lozinka="123",
            email="fallback@test.com"
        )

        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 test pdf content",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse("materials:add_script"),
            {
                "naslov": "Nova skripta",
                "opis": "Opis nove skripte",
                "idKat": self.kat_predmet.idkat,
                "fajl": pdf_file,
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/index/")

        self.assertTrue(
            Skripta.objects.filter(naziv="Nova skripta").exists()
        )

        skripta = Skripta.objects.get(naziv="Nova skripta")
        self.assertEqual(skripta.opis, "Opis nove skripte")
        self.assertEqual(skripta.idkat, self.kat_predmet)
        self.assertEqual(skripta.idkor, fallback_user)
        self.assertEqual(skripta.odobrena, 0)

    @patch("materials.views.render")
    def test_add_script_post_invalid_returns_form_errors(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.post(
            "/materials/add_script/",
            {
                "naslov": "",   # invalid: naziv missing
                "opis": "Opis",
                "idKat": "",    # invalid: category missing
            }
        )
        request.user = AnonymousUser()

        response = add_script(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "add_script.html")
        self.assertIn("form", response.context_data)
        self.assertIn("error", response.context_data)