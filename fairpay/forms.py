from django import forms
from django.forms import ValidationError
from fairpay.utils import FairpayOauth2Connection, FairpayOauth2Error

class FairpayOauth2Form(forms.Form):
    name = forms.CharField(max_length=32,
        widget=forms.TextInput(attrs={'class': 'required-field input-xxlarge',}))
    password = forms.CharField(max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'required-field input-xxlarge',}))
