from django.conf.urls import url
import multicurrency.views

urlpatterns = [
    url(r'^auth/(?P<agent_id>\d+)/$', multicurrency.views.auth, name="multicurrency_auth"),
    url(r'^createauth/(?P<agent_id>\d+)/$', multicurrency.views.createauth, name="multicurrency_createauth"),
    url(r'^deleteauth/(?P<agent_id>\d+)/(?P<oauth_id>\d+)/$', multicurrency.views.deleteauth, name="multicurrency_deleteauth"),
    url(r'^history/(?P<agent_id>\d+)/(?P<oauth_id>\d+)/$', multicurrency.views.history, name="multicurrency_history"),
]
