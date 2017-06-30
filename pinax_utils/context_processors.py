from django.conf import settings

from django.contrib.sites.models import Site


def settings(request):
    ctx = {}
    if Site._meta.installed:
        site = Site.objects.get_current()
        name = site.name
        domain = site.domain
        try:
            domain = request.get_host()
            if settings.PROJECTS_LOGIN:
                obj = settings.PROJECTS_LOGIN
                for pro in obj:
                    if domain in obj[pro]['domains']:
                        proj = get_object_or_404(Project, fobi_slug=pro)
                        name = proj.agent.name
        except:
            pass
        ctx.update({
            "SITE_NAME": name,
            "SITE_DOMAIN": domain
        })
    return ctx
