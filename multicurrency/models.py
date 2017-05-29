from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from valuenetwork.valueaccounting.models import EconomicAgent

class MulticurrencyAuth(models.Model):
    agent = models.ForeignKey(EconomicAgent, on_delete=models.CASCADE)
    auth_user = models.CharField(max_length=100, editable=False)
    access_key = models.CharField(max_length=100, editable=False)
    access_secret = models.CharField(max_length=100, editable=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
