from django import forms

class MulticurrencyAuthForm(forms.Form):
    name = forms.CharField(max_length=32,
        widget=forms.TextInput(attrs={'class': 'required-field input-xxlarge',}))
    password = forms.CharField(max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'required-field input-xxlarge',}))

class MulticurrencyAuthDeleteForm(forms.Form):
    hidden_delete = forms.CharField(widget=forms.HiddenInput(), initial='delete')

class MulticurrencyAuthCreateForm(forms.Form):
    hidden_create = forms.CharField(widget=forms.HiddenInput(), initial='create')
