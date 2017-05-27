from django.conf.urls import url
import fairpay.views

urlpatterns = [
    url(r'^auth/(?P<agent_id>\d+)/$', fairpay.views.auth, name="fairpay_auth"),
    url(r'^deleteauth/(?P<agent_id>\d+)/(?P<oauth_id>\d+)/$', fairpay.views.deleteauth, name="fairpay_deleteauth"),
    url(r'^history/(?P<agent_id>\d+)/(?P<oauth_id>\d+)/$', fairpay.views.history, name="fairpay_history"),
]
