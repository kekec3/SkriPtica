from django import forms

from materials.models import Skripta, Kategorija


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Skripta
        fields = ['idkat', 'naziv', 'opis', 'fajl']


class SearchForm(forms.Form):
    # required=False means the user doesn't have to fill out every field to search
    q = forms.CharField(required=False, max_length=100)
    tag = forms.CharField(required=False, max_length=50)

    # This automatically creates a dropdown of faculties
    fakultet = forms.ModelChoiceField(
        queryset=Kategorija.objects.filter(tip='Fakultet'),
        required=False,
        empty_label="Svi fakulteti"
    )


