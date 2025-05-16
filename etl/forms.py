from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Choisir un fichier")
    separator = forms.CharField(label="Séparateur", max_length=5, initial=",", required=False)