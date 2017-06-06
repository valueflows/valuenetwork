from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.views.generic import TemplateView
from account.views import LoginView
from django.http import HttpResponse

from django.contrib import admin
admin.autodiscover()

import work.views
#from valuenetwork.valueaccounting.models import *


urlpatterns = [
    url(r"^$", LoginView.as_view(template_name='account/login.html'), name='home'),
    #url(r"^$", valuenetwork.valueaccounting.views.home, name="home"),
    url(r"^accounting/", include("valuenetwork.valueaccounting.urls")),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^account/", include("account.urls")),
    url(r"^notification/", include("pinax.notifications.urls")),
    url(r"^equipment/", include("valuenetwork.equipment.urls")),
    url(r"^board/", include("valuenetwork.board.urls")),
    url(r"^work/", include("work.urls")),
    url(r"^api/", include("valuenetwork.api.urls")),
    #url(r'^report_builder/', include('report_builder.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^membership/$', work.views.membership_request, name="membership_request"),
    url(r'^membershipthanks/$', TemplateView.as_view(template_name='work/membership_thanks.html'), name='membership_thanks'),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nAllow: /$\nDisallow: /", content_type="text/plain")),

    url(r'^joinaproject/(?P<form_slug>.+)/$', work.views.joinaproject_request, name="joinaproject_request"),
    url(r'^join/(?P<form_slug>.+)/$', work.views.joinaproject_request, name="join_request"),
    #url(r'^joinaproject/(?P<form_slug>.+)/thanks/$', work.views.joinaproject_thanks, name='joinaproject_thanks'), # TemplateView.as_view(template_name='work/joinaproject_thanks.html')),
    url(r'^(?P<form_slug>.+)/$', work.views.project_login, name="project_login"),

    # View URLs
    url(r'^fobi/', include('fobi.urls.view')),

    # Edit URLs
    url(r'^fobi/', include('fobi.urls.edit')),

    # DB Store plugin URLs
    url(r'^fobi/plugins/form-handlers/db-store/',
        include('fobi.contrib.plugins.form_handlers.db_store.urls')),

]

if 'multicurrency' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^multicurrency/', include('multicurrency.urls')),]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
