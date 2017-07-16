# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from faircoin.models import FaircoinAddress, FaircoinTransaction

class FaircoinAddressAdmin(admin.ModelAdmin):
    readonly_fields = ('address', 'resource',)
    fields = ('address', 'resource',)
    list_display = ('resource', 'address',)
    search_fields = ['address']

admin.site.register(FaircoinAddress, FaircoinAddressAdmin)

class FaircoinTransactionAdmin(admin.ModelAdmin):
    readonly_fields = ('tx_hash', 'to_address', 'event',)
    fields = ('tx_hash', 'tx_state', 'to_address', 'event',)
    list_display = ('event', 'tx_state', 'to_address',)
    list_filter = ['tx_state',]

admin.site.register(FaircoinTransaction, FaircoinTransactionAdmin)
