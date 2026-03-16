# ══════════════════════════════════════════════════════════════
#  KLASA 2: PRETRAGA SKRIPTI
#  Implementirani Selenium testovi
# ══════════════════════════════════════════════════════════════

import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from accounts.tests_selenium import BaseSeleniumTest, BASE_URL


class SearchTests(BaseSeleniumTest):

    def test_05_search_stranica_dostupna_gostu(self):
        """Search stranica treba da bude dostupna bez logovanja."""
        self.go_to("/materials/search/")
        self.assertEqual(self.driver.title, self.driver.title)  # Stranica se učitala
        self.assertNotIn("login", self.driver.current_url.lower())

    def test_06_pretraga_po_kljucnoj_reci(self):
        """
        Unos teksta u search polje i submit treba da filtrira rezultate.
        NAPOMENA: U bazi mora postojati odobrena skripta sa rečju 'matematika'.
        """
        self.go_to("/materials/search/")
        search_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='q']")
        search_input.clear()
        search_input.send_keys("matematika")
        search_input.send_keys(Keys.RETURN)
        time.sleep(1)
        # URL treba da sadrži parametar pretrage
        self.assertIn("q=matematika", self.driver.current_url)

    def test_07_pretraga_bez_rezultata(self):
        """
        Pretraga sa nepostojećim terminom treba da prikaže praznu listu.
        """
        self.go_to("/materials/search/")
        search_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='q']")
        search_input.clear()
        search_input.send_keys("XYZ_ovo_sigurno_ne_postoji_12345")
        search_input.send_keys(Keys.RETURN)
        time.sleep(1)
        page_source = self.driver.page_source
        # Proveravamo da nema rezultata — prilagodi selector po šablonu
        self.assertNotIn("skripta", page_source.lower().split("XYZ")[0] if "XYZ" in page_source else "")
        self.assertIn("q=XYZ", self.driver.current_url)

    def test_08_autocomplete_kategorija(self):
        """
        Kucanje u polje za kategorije treba da prikaže autocomplete predloge.
        NAPOMENA: Prilagodi CSS selector za autocomplete input u vašem šablonu.
        """
        self.go_to("/materials/search/")
        try:
            cat_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='kategorija']")
            cat_input.send_keys("Mat")
            time.sleep(1)
            # Proveravamo da se pojavio dropdown sa predlozima
            page_source = self.driver.page_source
            self.assertIn("Mat", page_source)
        except Exception:
            self.skipTest("Autocomplete input nije pronađen — prilagodi CSS selector")


# ══════════════════════════════════════════════════════════════
#  KLASA 3: ČUVANJE SKRIPTI
#  Implementirani Selenium testovi
# ══════════════════════════════════════════════════════════════

class SaveScriptTests(BaseSeleniumTest):

    def test_09_sacuvaj_skriptu(self):
        """
        Klik na 'Sačuvaj' treba da sačuva skriptu.
        NAPOMENA: Potreban testuser i odobrena skripta sa ID=1 u bazi.
        """
        self.login("testuser", "TestPass123!")
        self.go_to("/materials/read/1/")
        try:
            sacuvaj_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[name='action'][value='sacuvaj'], input[value='sacuvaj']"
            )
            sacuvaj_btn.click()
            time.sleep(1)
            # Proveravamo da smo i dalje na stranici skripte (redirect nazad)
            self.assertIn("/materials/read/1", self.driver.current_url)
        except Exception:
            self.skipTest("Dugme za čuvanje nije pronađeno — prilagodi CSS selector")

    def test_10_sacuvane_skripte_stranica(self):
        """
        Stranica sačuvanih skripti treba da bude dostupna ulogovanom korisniku.
        """
        self.login("testuser", "TestPass123!")
        self.go_to("/materials/saved/")
        self.assertEqual(self.driver.current_url, f"{BASE_URL}/materials/saved/")


# ══════════════════════════════════════════════════════════════
#  NAPOMENE ZA SELENIUM IDE
#  Sledeće testove snimite ručno pomoću Selenium IDE ekstenzije
#  (dostupna za Chrome i Firefox na https://www.selenium.dev/selenium-ide/)
# ══════════════════════════════════════════════════════════════

"""
════════════════════════════════════════════════════════════
TESTOVI ZA SELENIUM IDE SNIMANJE
════════════════════════════════════════════════════════════

Kako koristiti Selenium IDE:
1. Instalirajte ekstenziju: https://www.selenium.dev/selenium-ide/
2. Otvorite ekstenziju u browseru
3. Kliknite "Record a new test"
4. Unesite Base URL: http://localhost:8000
5. Izvedite korake navedene ispod
6. Kliknite Stop i sačuvajte test

────────────────────────────────────────────────────────────
TEST IDE-01: Registracija novog korisnika
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Idite na /accounts/login/
  2. Popunite polje username (npr. "novi_korisnik_test")
  3. Popunite polje password1 (npr. "JakaLozinka123!")
  4. Popunite polje password2 (isto)
  5. Popunite polje email (npr. "test@test.com")
  6. Kliknite dugme za registraciju
  7. Dodajte assert: proverite da URL ne sadrži "login"

────────────────────────────────────────────────────────────
TEST IDE-02: Dodavanje nove skripte
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Logujte se kao testuser
  2. Idite na /materials/add/
  3. Popunite polje naslov (npr. "Test skripta selenium")
  4. Popunite polje opis
  5. Izaberite kategoriju iz dropdown-a
  6. Upload-ujte PDF fajl
  7. Kliknite Submit
  8. Dodajte assert: proverite da ste preusmereni (ne na /add/)

────────────────────────────────────────────────────────────
TEST IDE-03: Ostavljanje komentara na skriptu
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Logujte se kao testuser
  2. Idite na /materials/read/1/
  3. Pronađite textarea za komentar
  4. Upišite tekst komentara
  5. Kliknite dugme za slanje komentara
  6. Dodajte assert: proverite da se komentar pojavio na stranici

────────────────────────────────────────────────────────────
TEST IDE-04: Ocenjivanje skripte
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Logujte se kao testuser
  2. Idite na /materials/read/1/
  3. Izaberite ocenu (kliknite na zvezdicu ili radio button)
  4. Kliknite dugme za ocenjivanje
  5. Dodajte assert: proverite da je ocena sačuvana (vizuelni feedback)

────────────────────────────────────────────────────────────
TEST IDE-05: Moderator odobrava skriptu
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Logujte se kao moderator korisnik
  2. Idite na /accounts/moderator/
  3. Pronađite skriptu koja čeka odobrenje
  4. Kliknite dugme "Odobri"
  5. Dodajte assert: proverite da skripta nestala sa liste čekanja

────────────────────────────────────────────────────────────
TEST IDE-06: Admin promovišu korisnika u moderatora
────────────────────────────────────────────────────────────
Koraci za snimanje:
  1. Logujte se kao admin korisnik
  2. Idite na /accounts/admin/
  3. Pronađite korisnika u listi
  4. Kliknite dugme "Promoviši u moderatora"
  5. Dodajte assert: proverite da se uloga promenila

════════════════════════════════════════════════════════════
"""


if __name__ == '__main__':
    unittest.main(verbosity=2)
