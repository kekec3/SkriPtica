from django import forms

from materials.models import Skripta


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Skripta
        fields = ['idkat', 'naziv', 'opis', 'fajl']

