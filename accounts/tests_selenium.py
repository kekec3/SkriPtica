"""
SELENIUM TESTOVI ZA SKRIPTICA PROJEKAT
=======================================

INSTALACIJA:
    pip install selenium

POKRETANJE:
    python selenium_tests.py

NAPOMENA: Aplikacija mora biti pokrenuta na http://localhost:8000
    pre pokretanja testova (python manage.py runserver)

ChromeDriver se preuzima automatski uz selenium 4.6+
"""

import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:8000"

# ──────────────────────────────────────────────────────────────
# POMOĆNA KLASA
# ──────────────────────────────────────────────────────────────

class BaseSeleniumTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = Options()
        # Ukloni '--headless' ako želiš da vidiš browser tokom testiranja
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(5)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.driver.delete_all_cookies()

    def login(self, username, password):
        self.driver.get(f"{BASE_URL}/accounts/login/")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.execute_script(
            "document.querySelector('.flip-card__front form').submit();"
        )
        time.sleep(1)

    def go_to(self, path):
        self.driver.get(f"{BASE_URL}{path}")






# ══════════════════════════════════════════════════════════════
#  KLASA 1: AUTENTIKACIJA
#  Implementirani Selenium testovi
# ══════════════════════════════════════════════════════════════

class AuthenticationTests(BaseSeleniumTest):

    def test_01_login_stranica_se_ucitava(self):
        """Login stranica treba da se učita i prikaže formu."""
        self.go_to("/accounts/login/")
        self.assertIn("login", self.driver.current_url.lower())
        # Proveravamo da postoji polje za username
        username_field = self.driver.find_element(By.NAME, "username")
        self.assertTrue(username_field.is_displayed())

    def test_02_pogresna_lozinka_prikazuje_gresku(self):
        self.go_to("/accounts/login/")
        self.driver.find_element(By.NAME, "username").send_keys("nepostoji_xyz")
        self.driver.find_element(By.NAME, "password").send_keys("pogresna123")
        self.driver.execute_script(
            "document.querySelector('.flip-card__front form').submit();"
        )
        time.sleep(1)
        page_source = self.driver.page_source
        self.assertTrue(
            "Pogrešna" in page_source or
            "Ne postoji" in page_source or
            "Greška" in page_source
        )

    def test_03_uspesna_prijava_preusmerava_na_index(self):
        self.go_to("/accounts/login/")
        self.driver.find_element(By.NAME, "username").send_keys("Mitar")
        self.driver.find_element(By.NAME, "password").send_keys("mitarmaja123")
        self.driver.execute_script(
            "document.querySelector('.flip-card__front form').submit();"
        )
        time.sleep(2)
        self.assertNotIn("/login", self.driver.current_url)

    def test_04_logout_odjavljuje_korisnika(self):
        """Nakon odjave korisnik treba da bude odjavljen."""
        self.login("testuser_selenium", "TestPass123!")
        self.go_to("/accounts/logout/")
        time.sleep(1)
        # Proveravamo da korisnik više nije ulogovan tako što
        # pokušavamo da odemo na login stranicu — treba da se učita normalno
        # (ulogovan korisnik bi bio preusmeren sa nje)
        self.go_to("/accounts/login/")
        time.sleep(1)
        # Ulogovani korisnik bi bio preusmeren, odjavljen vidi login formu
        self.assertIn("login", self.driver.current_url.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)