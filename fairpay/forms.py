from django import forms

class FairpayOauth2Form(forms.Form):
    name = forms.CharField(max_length=32,
        widget=forms.TextInput(attrs={'class': 'required-field input-xxlarge',}))
    password = forms.CharField(max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'required-field input-xxlarge',}))

class FairpayOauth2DeleteForm(forms.Form):
    hidden_delete = forms.CharField(widget=forms.HiddenInput(), initial='delete')
