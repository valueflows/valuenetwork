from django.conf.urls import url
import faircoin.views

urlpatterns = [
    url(r"^manage-faircoin-account/(?P<resource_id>\d+)/$", faircoin.views.manage_faircoin_account,
        name="manage_faircoin_account"),
    url(r"^transfer-faircoins/(?P<resource_id>\d+)/$", faircoin.views.transfer_faircoins,
        name="transfer_faircoins"),
    url(r"^faircoin-history/(?P<resource_id>\d+)/$", faircoin.views.faircoin_history,
        name="faircoin_history"),
    url(r"^change-faircoin-account/(?P<resource_id>\d+)/$", faircoin.views.change_faircoin_account,
        name="change_faircoin_account"),
    url(r"^validate-faircoin-address-for-worker/$", faircoin.views.validate_faircoin_address_for_worker,
        name="validate_faircoin_address_for_worker"),
    url(r"^edit_event_notes/(?P<resource_id>\d+)/$", faircoin.views.edit_faircoin_event_description,
        name="edit_faircoin_event_description"),
]
