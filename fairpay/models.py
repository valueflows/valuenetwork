from __future__ import unicode_literals

from django.db import models

from valueaccounting.models import EconomicAgent

class FairpayOauth2(models.Model):
    agent = models.ForeignKey(EconomicAgent, on_delete=models.CASCADE)
    fairpay_user = models.CharField(max_length=100, editable=False)
    access_token = models.CharField(max_length=100, editable=False)
    refresh_token = models.CharField(max_length=100, editable=False)
    expires_token = models.TimeField(null=True, editable=False)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
