from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.views.generic import TemplateView
from account.views import LoginView
from django.http import HttpResponse

from django.contrib import admin
admin.autodiscover()

import valuenetwork.valueaccounting.views

urlpatterns = [
    #url(r"^$", LoginView.as_view(template_name='account/login.html'), name='home'),
    url(r"^$", valuenetwork.valueaccounting.views.home, name="home"),
    url(r"^signup/$", valuenetwork.valueaccounting.views.signup, name="signup"),
    url(r'^signup/confirm/$', valuenetwork.valueaccounting.views.signup_confirm, name='signup_confirm'),
    url(r'^signup/complete/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', valuenetwork.valueaccounting.views.signup_complete, name='signup_complete'),
    url(r"^accounting/", include("valuenetwork.valueaccounting.urls")),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^account/", include("account.urls")),
    url(r"^notification/", include("pinax.notifications.urls")),
    url(r"^equipment/", include("valuenetwork.equipment.urls")),
    url(r"^board/", include("valuenetwork.board.urls")),
    url(r"^api/", include("valuenetwork.api.urls")),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nAllow: /$\nDisallow: /", content_type="text/plain")),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()

if 'multicurrency' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^multicurrency/', include('multicurrency.urls')),]

if 'faircoin' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^faircoin/', include('faircoin.urls')),]


