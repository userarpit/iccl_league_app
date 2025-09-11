from django import forms


class PlayerImageForm(forms.Form):
    image = forms.ImageField(label="Upload Profile Picture")
