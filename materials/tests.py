from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from unittest.mock import patch

from accounts.models import Korisnik, Role
from accounts.views import login


class LoginViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.role = Role.objects.create(opis="student")

        self.user = User.objects.create_user(
            username="jaksa",
            password="test12345",
            email="jaksa@test.com"
        )

        self.korisnik = Korisnik.objects.create(
            idrol=self.role,
            kor_ime="jaksa",
            lozinka="test12345",
            email="jaksa@test.com"
        )

    def fake_render(self, request, template_name, context=None, *args, **kwargs):
        response = HttpResponse("OK")
        response.template_name = template_name
        response.context_data = context or {}
        return response

    @patch("accounts.views.render")
    def test_login_page_loads(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.get(reverse("login"))
        request.user = type("Anon", (), {"is_authenticated": False})()

        response = login(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "login.html")

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.login(username="jaksa", password="test12345")

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))

    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "action": "login",
            "username": "jaksa",
            "password": "test12345"
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))
        self.assertIn("_auth_user_id", self.client.session)

    @patch("accounts.views.render")
    def test_login_nonexistent_user(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.post(reverse("login"), {
            "action": "login",
            "username": "nepostoji",
            "password": "test12345"
        })
        request.user = type("Anon", (), {"is_authenticated": False})()

        response = login(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["mess"], "Ne postoji korisnik")

    @patch("accounts.views.render")
    def test_login_wrong_password(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.post(reverse("login"), {
            "action": "login",
            "username": "jaksa",
            "password": "pogresna"
        })
        request.user = type("Anon", (), {"is_authenticated": False})()

        response = login(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["mess"], "Pogrešna lozinka")

    def test_register_success(self):
        response = self.client.post(reverse("login"), {
            "action": "register",
            "username": "pera",
            "email": "pera@test.com",
            "password1": "jakalozinka123",
            "password2": "jakalozinka123"
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="pera").exists())
        self.assertTrue(Korisnik.objects.filter(kor_ime="pera").exists())

    @patch("accounts.views.render")
    def test_register_password_mismatch(self, mock_render):
        mock_render.side_effect = self.fake_render

        request = self.factory.post(reverse("login"), {
            "action": "register",
            "username": "mika",
            "email": "mika@test.com",
            "password1": "lozinka123",
            "password2": "drugalink123"
        })
        request.user = type("Anon", (), {"is_authenticated": False})()

        response = login(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "login.html")
        self.assertFalse(User.objects.filter(username="mika").exists())