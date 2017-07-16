from django.db import models, connection
from django.contrib.auth.models import User
from django.conf import settings

from django.utils.translation import ugettext_lazy as _

from easy_thumbnails.fields import ThumbnailerImageField

from valuenetwork.valueaccounting.models import *
from fobi.models import FormEntry

from mptt.fields import TreeForeignKey

MEMBERSHIP_TYPE_CHOICES = (
    #('participant', _('project participant (no membership)')),
    ('individual', _('individual membership (min 1 share)')),
    ('collective', _('collective membership (min 2 shares)')),
)

REQUEST_STATE_CHOICES = (
    ('new', _('new')),
    ('accepted', _('accepted')),
    ('declined', _('declined')),
)

class MembershipRequest(models.Model):
    request_date = models.DateField(auto_now_add=True, blank=True, null=True, editable=False)
    name = models.CharField(_('Name'), max_length=255)
    surname = models.CharField(_('Surname (for individual memberships)'), max_length=255, blank=True)
    requested_username = models.CharField(_('Requested username'), max_length=32)
    email_address = models.EmailField(_('Email address'), max_length=96,)
    #    help_text=_("this field is optional, but we can't contact you via email without it"))
    phone_number = models.CharField(_('Phone number'), max_length=32, blank=True, null=True)
    address = models.CharField(_('Where do you live?'), max_length=255, blank=True)
    native_language = models.CharField(_('Languages'), max_length=255, blank=True)
    type_of_membership = models.CharField(_('Type of membership'),
        max_length=12, choices=MEMBERSHIP_TYPE_CHOICES,
        default="individual")
    #membership_for_services = models.BooleanField(_('Membership for services'), default=False,
    #    help_text=_('you have legal entity and want to offer services or products to the cooperative'))
    #autonomous_membership = models.BooleanField(_('Autonomous membership'), default=False,
    #    help_text=_("you don't have legal entity and want to use the cooperative to make invoices either from inside and to outside the cooperative"))
    #ocp_user_membership = models.BooleanField(_('OCP user membership'), default=False,
    #    help_text=_('for those that only want to use the OCP platform'))
    #consumer_membership = models.BooleanField(_('Consumer membership'), default=False,
    #    help_text=_("you don't offer any product or service but want to consume through it and support the cooperative"))
    number_of_shares = models.IntegerField(_('Number of shares'),
        default=1,
        help_text=_("How many shares would you like to underwrite? Each share is worth 30 Euros"))
    #work_for_shares = models.BooleanField(_('work for one share'), default=False,
    #    help_text=_("You can get 1 share for 6 hours of work. If you choose this option, we will send you a list of tasks and the deadline. You won't have full access before the tasks are accomplished."))
    description = models.TextField(_('Description'),
        help_text=_("Describe your project or collective and the skills or abilities you can offer the cooperative"))
    website = models.CharField(_('Website'), max_length=255, blank=True)
    fairnetwork = models.CharField(_('FairNetwork username'), max_length=255, blank=True,
        help_text = _("The username you use in the FairNetwork at <a href='https://fair.coop' target='_blank'>fair.coop</a>"))
    usefaircoin = models.CharField(_('UseFaircoin profile'), max_length=255, blank=True,
        help_text = _("If you are in the directory at <a href='https://use.fair-coin.org' target='_blank'>use.fair-coin.org</a> please add the URL to your profile."))
    fairmarket = models.CharField(_('FairMarket shop'), max_length=255, blank=True,
        help_text = _("If you have an online shop at <a href='https://market.fair.coop' target='_blank'>market.fair.coop</a> please add the URL to your fair shop."))
    #how_do_you_know_fc = models.TextField(_('How do you know Freedom Coop?'), blank=True,)
    known_member = models.CharField(_('Are there any FairCoop participant(s) who can give references about you? If so, who?'), max_length=255, blank=True)
    comments_and_questions = models.TextField(_('Comments and questions'), blank=True,)

    agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('agent'), related_name='membership_requests',
        blank=True, null=True,
        help_text=_("this membership request became this EconomicAgent"))
    state = models.CharField(_('state'),
        max_length=12, choices=REQUEST_STATE_CHOICES,
        default='new', editable=False)

    def __unicode__(self):
        return self.name


JOINING_STYLE_CHOICES = (
    ('moderated', _('moderated')),
    ('autojoin', _('autojoin')),
)

VISIBILITY_CHOICES = (
    ('private', _('private')),
    ('FCmembers', _('only FC members')),
    ('public', _('public')),
)

SELECTION_CHOICES = (
    ('project', _('your project')),
    #('related', _('all related projects')),
    ('all', _('all platform')),
)

class Project(models.Model):
    agent = models.OneToOneField(EconomicAgent,
        verbose_name=_('agent'), related_name='project')
    joining_style = models.CharField(_('joining style'),
        max_length=12, choices=JOINING_STYLE_CHOICES,
        default="autojoin")
    visibility = models.CharField(_('visibility'),
        max_length=12, choices=VISIBILITY_CHOICES,
        default="FCmembers")
    resource_type_selection = models.CharField(_('resource type selection'),
        max_length=12, choices=SELECTION_CHOICES,
        default="all")
    fobi_slug = models.CharField(_('custom form slug'),
        max_length=255, blank=True)

    #fobi_form = models.OneToOneField(FormEntry,
    #    verbose_name=_('custom form'), related_name='project',
    #    blank=True, null=True,
    #    help_text=_("this Project use this custom form (fobi FormEntry)"))
    #join_request = models.ForeignKey(JoinRequest,
    #    verbose_name=_('join request'), related_name='project',
    #    blank=True, null=True,
    #    help_text=_("this Project is using this JoinRequest form"))

    def __unicode__(self):
        return _('Project: ') + self.agent.name

    def is_moderated(self):
        return self.joining_style == 'moderated'

    def is_public(self):
        return self.visibility == 'public'

    def fobi_form(self):
        if self.fobi_slug:
            entry = FormEntry.objects.get(slug=self.fobi_slug)
            return entry
        return False

    def rts_with_clas(self, clas=None):
        rts_with_clas = []
        rts = list(set([arr.resource.resource_type for arr in self.agent.resource_relationships()]))
        for rt in rts:
            if hasattr(rt, 'ocp_artwork_type') and rt.ocp_artwork_type and rt.ocp_artwork_type.clas:
                if clas:
                    if clas == rt.ocp_artwork_type.clas:
                        rts_with_clas = rt
                else:
                    rts_with_clas.append(rt)
        return rts_with_clas

    def share_types(self):
        shr_ts = []
        if self.is_moderated() and self.fobi_slug:
            form = self.fobi_form()
            fields = form.formelemententry_set.all()
            for fi in fields:
                data = json.loads(fi.plugin_data)
                name = data.get('name')
                for rt in self.rts_with_clas():
                    if rt.ocp_artwork_type.clas == name: # matches the rt clas identifier with the fobi field name
                        choi = data.get('choices')
                        if choi:
                            opts = choi.split('\r\n')
                            for op in opts:
                                opa = op.split(',')
                                shr_ts.append(opa[1].strip())
                        else:
                            #import pdb; pdb.set_trace()
                            text = data.get('help_text')
                            opts = text.split('\r\n')
                            for op in opts:
                                shr_ts.append(op.strip(' /'))

            if len(shr_ts):
                return shr_ts
        return False

    def share_totals(self):
        shr_ts = self.share_types()
        shares_res = None
        total = 0
        self.holders = 0
        if shr_ts:
            rts = self.rts_with_clas()
            shr_rt = None
            for rt in rts:
                if rt.ocp_artwork_type.ocpArtworkType_unit_type:
                    if rt.ocp_artwork_type.ocpArtworkType_unit_type.clas == 'share':
                        shr_rt = rt
            if shr_rt:
                shares_res = EconomicResource.objects.filter(resource_type=shr_rt)
        if shares_res:
            for res in shares_res:
                if res.price_per_unit:
                    total += res.price_per_unit
                    self.holders += 1
        return total

    def share_holders(self):
        if self.share_totals():
            return self.holders

    def payment_options(self):
        pay_opts = []
        if self.is_moderated() and self.fobi_slug:
            form = self.fobi_form()
            fields = form.formelemententry_set.all()
            for fi in fields:
                data = json.loads(fi.plugin_data)
                name = data.get('name')
                if name == "payment_mode": # name of the fobi field
                    choi = data.get('choices')
                    if choi:
                        opts = choi.split('\r\n')
                        for op in opts:
                            opa = op.split(',')
                            key = opa[0].strip()
                            val = opa[1].strip()
                            ok = '<span class="error">config pending!</span>'
                            gates = self.payment_gateways()
                            if gates:
                                try:
                                    gate = gates[key]
                                except:
                                    gate = None
                                if gate is not None:
                                    ok = '<span style="color:#090">ok:</span>'
                                    if gate['html']:
                                        ok += ' <ul><li>'+str(gate['html'])+'</li></ul>'
                            pay_opts.append(val+' &nbsp;'+ok)
            return pay_opts
        return False

    def background_url(self):
        back = False
        if settings.PROJECTS_LOGIN and self.fobi_slug:
            try:
                back = settings.PROJECTS_LOGIN[self.fobi_slug]['background_url']
            except:
                pass
        return back

    def custom_css(self):
        css = False
        if settings.PROJECTS_LOGIN and self.fobi_slug:
            try:
                css = settings.PROJECTS_LOGIN[self.fobi_slug]['css']
            except:
                pass
        return css

    def custom_html(self):
        html = False
        if settings.PROJECTS_LOGIN and self.fobi_slug:
            try:
                html = settings.PROJECTS_LOGIN[self.fobi_slug]['html']
            except:
                pass
        return html

    def services(self):
        serv = False
        if settings.PROJECTS_LOGIN and self.fobi_slug:
            try:
                serv = settings.PROJECTS_LOGIN[self.fobi_slug]['services']
            except:
                pass
        return serv

    def custom_login(self):
        resp = False
        if settings.PROJECTS_LOGIN and self.fobi_slug:
            try:
                resp = settings.PROJECTS_LOGIN[self.fobi_slug]
            except:
                pass
        return resp

    def payment_gateways(self):
        gates = False
        if settings.PAYMENT_GATEWAYS and self.fobi_slug:
            try:
                gates = settings.PAYMENT_GATEWAYS[self.fobi_slug]
            except:
                pass
        return gates



class SkillSuggestion(models.Model):
    skill = models.CharField(_('skill'), max_length=128,
        help_text=_("A new skill that you want to offer that is not already listed"))
    suggested_by = models.ForeignKey(User, verbose_name=_('suggested by'),
        related_name='skill_suggestion', blank=True, null=True, editable=False)
    suggestion_date = models.DateField(auto_now_add=True, blank=True, null=True, editable=False)
    resource_type = models.ForeignKey(EconomicResourceType,
        verbose_name=_('resource_type'), related_name='skill_suggestions',
        blank=True, null=True,
        help_text=_("this skill suggestion became this ResourceType"))
    state = models.CharField(_('state'),
        max_length=12, choices=REQUEST_STATE_CHOICES,
        default='new', editable=False)


    def __unicode__(self):
        return self.skill

    def form_prefix(self):
        return "".join(["SS", str(self.id)])

    def resource_type_form(self):
        from valuenetwork.valueaccounting.forms import SkillSuggestionResourceTypeForm
        init = {
            "name": self.skill,
            }
        return SkillSuggestionResourceTypeForm(initial=init, prefix=self.form_prefix())


from nine.versions import DJANGO_LTE_1_5
from fobi.contrib.plugins.form_handlers.db_store.models import SavedFormDataEntry
import simplejson as json
import hashlib

USER_TYPE_CHOICES = (
    #('participant', _('project participant (no membership)')),
    ('individual', _('individual')),
    ('collective', _('collective')),
)

class JoinRequest(models.Model):
    # common fields for all projects
    project = models.ForeignKey(Project,
        verbose_name=_('project'), related_name='join_requests',
        #blank=True, null=True,
        help_text=_("this join request is for joining this Project"))

    request_date = models.DateField(auto_now_add=True, blank=True, null=True, editable=False)
    type_of_user = models.CharField(_('Type of user'),
        max_length=12, choices=USER_TYPE_CHOICES,
        default="individual")
    name = models.CharField(_('Name'), max_length=255)
    surname = models.CharField(_('Surname (for individual join requests)'), max_length=255, blank=True)
    requested_username = models.CharField(_('Requested username'), max_length=32, help_text=_("If you have already an account in OCP, you can put the same username to have this project in the same account, or you can choose another username to have it separate."))
    email_address = models.EmailField(_('Email address'), max_length=96,)
    #    help_text=_("this field is optional, but we can't contact you via email without it"))
    phone_number = models.CharField(_('Phone number'), max_length=32, blank=True, null=True)
    address = models.CharField(_('Town/Region where you are based'), max_length=255, blank=True, null=True)
    #native_language = models.CharField(_('Languages'), max_length=255, blank=True)

    #description = models.TextField(_('Description'),
    #    help_text=_("Describe your collective or the personal skills you can offer to the project"))

    agent = models.ForeignKey(EconomicAgent,
        verbose_name=_('agent'), related_name='project_join_requests',
        blank=True, null=True,
        help_text=_("this join request became this EconomicAgent"))

    fobi_data = models.OneToOneField(SavedFormDataEntry,
        verbose_name=_('custom fobi entry'), related_name='join_request',
        blank=True, null=True, on_delete=models.CASCADE,
        help_text=_("this join request is linked to this custom form (fobi SavedFormDataEntry)"))

    state = models.CharField(_('state'),
        max_length=12, choices=REQUEST_STATE_CHOICES,
        default='new', editable=False)

    def fobi_slug(self):
      if self.project.fobi_slug:
        return self.project.fobi_slug
      return False

    def __unicode__(self):
        return self.name

    def form_prefix(self):
        return "".join(["JR", str(self.id)])

    def full_name(self):
        if self.surname:
            answer = " ".join([self.name, self.surname])
        else:
            answer = self.name
        return answer

    def agent_type(self):
        if self.type_of_user == "individual":
            answer = AgentType.objects.individual_type()
        else:
            answer = None
        return answer

    def agent_form(self):
        from work.forms import ProjectAgentCreateForm
        init = {
            "name": self.full_name(),
            "nick": self.requested_username,
            "email": self.email_address,
            }
        agent_type = self.agent_type()
        if agent_type:
            init["agent_type"] = agent_type
        return ProjectAgentCreateForm(initial=init, prefix=self.form_prefix())

    def fobi_items_keys(self):
        fobi_headers = []
        fobi_keys = []
        if self.fobi_data and self.fobi_data.pk:
            self.entries = SavedFormDataEntry.objects.filter(pk=self.fobi_data.pk).select_related('form_entry')
            entry = self.entries[0]
            self.form_headers = json.loads(entry.form_data_headers)
            for val in self.form_headers:
                fobi_headers.append(self.form_headers[val])
                fobi_keys.append(val)
        return fobi_keys

    def fobi_items_data(self):
        self.items_data = None
        if self.fobi_data and self.fobi_data.pk:
            self.entries = SavedFormDataEntry.objects.filter(pk=self.fobi_data.pk).select_related('form_entry')
            entry = self.entries[0]
            self.data = json.loads(entry.saved_data)
            self.items = self.data.items()
            self.items_data = []
            for key in self.fobi_items_keys():
                self.items_data.append(self.data.get(key))
        return self.items_data

    def pending_shares(self):
        answer = ''
        account_type = None
        balance = 0
        amount = 0
        if self.project.joining_style == "moderated" and self.fobi_data:
            rts = list(set([arr.resource.resource_type for arr in self.project.agent.resource_relationships()]))
            for rt in rts:
                if rt.ocp_artwork_type:
                    for key in self.fobi_items_keys():
                        if key == rt.ocp_artwork_type.clas: # fieldname is the artwork type clas, project has shares of this type
                            self.entries = SavedFormDataEntry.objects.filter(pk=self.fobi_data.pk).select_related('form_entry')
                            entry = self.entries[0]
                            self.data = json.loads(entry.saved_data)
                            val = self.data.get(key)
                            account_type = rt
                            for elem in self.fobi_data.form_entry.formelemententry_set.all():
                                data = json.loads(elem.plugin_data)
                                choi = data.get('choices')
                                if choi:
                                    opts = choi.split('\r\n')
                                    for op in opts:
                                      opa = op.split(',')
                                      #import pdb; pdb.set_trace()
                                      if type(val) is str and opa[1].encode('utf-8').strip() == val.encode('utf-8').strip():
                                        amount = int(opa[0])
                                        break
                                elif type(val) is int and val:
                                    amount = val
                                    break


        if self.agent:
            user_rts = list(set([arr.resource.resource_type for arr in self.agent.resource_relationships()]))
            for rt in user_rts:
                if rt == account_type: #.ocp_artwork_type:
                    rss = list(set([arr.resource for arr in self.agent.resource_relationships()]))
                    for rs in rss:
                        if rs.resource_type == rt:
                            balance = rs.price_per_unit # TODO: update the price_per_unit with wallet balance

        if amount:
            answer = amount - balance
            if answer > 0:
                return int(answer)
            else:
                #import pdb; pdb.set_trace()
                return 0

        return False #'??'

    def total_shares(self):
        account_type = None
        balance = 0
        if self.project.joining_style == "moderated" and self.fobi_data:
            rts = list(set([arr.resource.resource_type for arr in self.project.agent.resource_relationships()]))
            for rt in rts:
                if rt.ocp_artwork_type:
                    for key in self.fobi_items_keys():
                        if key == rt.ocp_artwork_type.clas: # fieldname is the artwork type clas, project has shares of this type
                            self.entries = SavedFormDataEntry.objects.filter(pk=self.fobi_data.pk).select_related('form_entry')
                            entry = self.entries[0]
                            self.data = json.loads(entry.saved_data)
                            val = self.data.get(key)
                            account_type = rt

        if self.agent:
            user_rts = list(set([arr.resource.resource_type for arr in self.agent.resource_relationships()]))
            for rt in user_rts:
                if rt == account_type: #.ocp_artwork_type:
                    rss = list(set([arr.resource for arr in self.agent.resource_relationships()]))
                    for rs in rss:
                        if rs.resource_type == rt:
                            balance = rs.price_per_unit # TODO: update the price_per_unit with wallet balance
        return balance

    def payment_option(self):
        answer = {}
        if self.project.joining_style == "moderated" and self.fobi_data:
            for key in self.fobi_items_keys():
                if key == "payment_mode": # fieldname specially defined in the fobi form
                    self.entries = SavedFormDataEntry.objects.filter(pk=self.fobi_data.pk).select_related('form_entry')
                    entry = self.entries[0]
                    self.data = json.loads(entry.saved_data)
                    val = self.data.get(key)
                    answer['val'] = val
                    for elem in self.fobi_data.form_entry.formelemententry_set.all():
                        data = json.loads(elem.plugin_data)
                        choi = data.get('choices') # works with radio or select
                        if choi:
                            opts = choi.split('\r\n')
                            for op in opts:
                                opa = op.split(',')
                                #import pdb; pdb.set_trace()
                                if val.strip() == opa[1].strip():
                                    answer['key'] = opa[0]
        return answer

    def payment_url(self):
        payopt = self.payment_option()
        obj = None
        if settings.PAYMENT_GATEWAYS and payopt:
            gates = settings.PAYMENT_GATEWAYS
            if self.project.fobi_slug and gates[self.project.fobi_slug]:
                try:
                    obj = gates[self.project.fobi_slug][payopt['key']]
                except:
                    pass
            if obj:
                return obj['url']
        return False

    def payment_html(self):
        payopt = self.payment_option()
        obj = None
        if settings.PAYMENT_GATEWAYS and payopt:
            gates = settings.PAYMENT_GATEWAYS
            if self.project.fobi_slug and gates[self.project.fobi_slug]:
                try:
                    obj = gates[self.project.fobi_slug][payopt['key']]
                except:
                    pass
            if obj and obj['html']:
                return obj['html']
        return False

    def payment_salt(self):
        payopt = self.payment_option()
        obj = None
        if settings.PAYMENT_GATEWAYS and payopt:
            gates = settings.PAYMENT_GATEWAYS
            if self.project.fobi_slug and gates[self.project.fobi_slug]:
                try:
                    obj = gates[self.project.fobi_slug][payopt['key']]
                except:
                    pass
            if obj and obj['salt']:
                return obj['salt']
        return False

    def payment_token(self):
        salt = self.payment_salt()
        email = self.email_address
        amount = self.pending_shares()
        strin = salt+str(amount)+email
        token_obj = hashlib.sha1(strin)
        return token_obj.hexdigest()


class NewFeature(models.Model):
    name = models.CharField(_('name'), max_length=24)
    deployment_date = models.DateField(_("deployment date"),)
    description = models.TextField(_('Description'),)
    permissions = models.TextField(_('permissions'), blank=True, null=True,)
    url = models.CharField(_('url'), max_length=255, blank=True,)
    screenshot = ThumbnailerImageField(_("screenshot"),
        upload_to='photos', blank=True, null=True,)

    class Meta:
        ordering = ('-deployment_date',)

    def __unicode__(self):
        return self.name


class InvoiceNumber(models.Model):
    invoice_number = models.CharField(_('invoice number'), max_length=128)
    invoice_date = models.DateField(_("invoice date"),)
    year = models.IntegerField(_("year"),)
    quarter = models.IntegerField(_("quarter"),)
    sequence = models.IntegerField(_("sequence"),)
    description = models.TextField(_('Description'), blank=True,null=True)
    member = models.ForeignKey(EconomicAgent, related_name="invoice_numbers",
        verbose_name=_('member'),)
    exchange = models.ForeignKey(Exchange,
        blank=True, null=True,
        verbose_name=_('exchange'), related_name='invoice_numbers')
    created_by = models.ForeignKey(User, verbose_name=_('created by'),
        related_name='invoice_numbers_created', editable=False)
    created_date = models.DateField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-invoice_date', "-sequence",)

    def __unicode__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        if self.year:
            year = self.year
        else:
            year = self.invoice_date.year
            self.year = year
        if self.quarter:
            quarter = self.quarter
        else:
            month = self.invoice_date.month
            quarter = (month-1)//3 + 1
            self.quarter = quarter
        if self.sequence:
            sequence = self.sequence
        else:
            prevs = InvoiceNumber.objects.filter(
                year=year,
                quarter=quarter).order_by("-sequence")
            if prevs:
                sequence = prevs[0].sequence + 1
            else:
                sequence = 1
            self.sequence = sequence
        self.invoice_number = "/".join([
            unicode(year),
            unicode(quarter),
            unicode(sequence),
            unicode(self.member.id),
            ])
        super(InvoiceNumber, self).save(*args, **kwargs)


from general.models import Record_Type, Artwork_Type, Material_Type, Nonmaterial_Type, Job, Unit_Type
from mptt.models import TreeManager


class Ocp_Artwork_TypeManager(TreeManager):

    def update_from_general(self): # TODO, if general.Artwork_Type (or Type) changes independently, update the subclass with new items
        return False

    def update_to_general(self, table=None, ide=None): # update material and non-material general tables if not matching
        if table and ide:
            if table == 'Material_Type':
                try:
                    genm = Material_Type.objects.get(id=ide)
                except:
                    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                        with connection.cursor() as cursor:
                            cursor.execute("PRAGMA foreign_keys=OFF")
                            cursor.execute("INSERT INTO general_material_type (materialType_artwork_type_id) VALUES (%s)", [ide])
                            cursor.execute("PRAGMA foreign_keys=ON")
                            return Material_Type.objects.get(id=ide)
            elif table == 'Nonmaterial_Type':
                try:
                    genm = Nonmaterial_Type.objects.get(id=ide)
                except:
                    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                        with connection.cursor() as cursor:
                            cursor.execute("PRAGMA foreign_keys=OFF")
                            cursor.execute("INSERT INTO general_nonmaterial_type (nonmaterialType_artwork_type_id) VALUES (%s)", [ide])
                            cursor.execute("PRAGMA foreign_keys=ON")
                            return Nonmaterial_Type.objects.get(id=ide)
            else:
                raise ValidationError("Unknown table for update_to_general ! "+table)

        else: # update all
            pass
            ocp_mat = Ocp_Artwork_Type.objects.get(clas='Material')
            ocp_mats_c = ocp_mat.get_descendant_count() # self not included, like at general_material_type
            gen_mats_c = Material_Type.objects.count()
            if not ocp_mats_c == gen_mats_c:
                ocp_mats = ocp_mat.get_descendants()
                gen_mats = Material_Type.objects.all()
                for ocpm in ocp_mats:
                    try:
                        genm = Material_Type.objects.get(id=ocpm.id)
                    except:
                        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                            with connection.cursor() as cursor:
                                cursor.execute("PRAGMA foreign_keys=OFF")
                                cursor.execute("INSERT INTO general_material_type (materialType_artwork_type_id) VALUES (%s)", [ocpm.id])
                                cursor.execute("PRAGMA foreign_keys=ON")


class Ocp_Artwork_Type(Artwork_Type):
    ocpArtworkType_artwork_type = models.OneToOneField(
      Artwork_Type,
      on_delete=models.CASCADE,
      primary_key=True,
      parent_link=True
    )
    ocpArtworkType_material_type = TreeForeignKey(
      Material_Type,
      on_delete=models.CASCADE,
      verbose_name=_('general material_type'),
      related_name='ocp_artwork_types',
      blank=True, null=True,
      help_text=_("a related General Material Type")
    )
    ocpArtworkType_nonmaterial_type = TreeForeignKey(
      Nonmaterial_Type,
      on_delete=models.CASCADE,
      verbose_name=_('general nonmaterial_type'),
      related_name='ocp_artwork_types',
      blank=True, null=True,
      help_text=_("a related General Non-material Type")
    )
    facet = models.OneToOneField(
      Facet,
      on_delete=models.CASCADE,
      verbose_name=_('ocp facet'),
      related_name='ocp_artwork_type',
      blank=True, null=True,
      help_text=_("a related OCP Facet")
    )
    facet_value = models.ForeignKey(
      FacetValue,
      on_delete=models.CASCADE,
      verbose_name=_('ocp facet_value'),
      related_name='ocp_artwork_type',
      blank=True, null=True,
      help_text=_("a related OCP FacetValue")
    )
    resource_type = models.OneToOneField(
      EconomicResourceType,
      on_delete=models.CASCADE,
      verbose_name=_('ocp resource_type'),
      related_name='ocp_artwork_type',
      blank=True, null=True,
      help_text=_("a related OCP ResourceType")
    )
    context_agent = models.ForeignKey(EconomicAgent, # this field should be used only if there's no resource_type
      verbose_name=_('context agent'),               # and is needed to hide the category name by context
      on_delete=models.CASCADE,
      related_name='ocp_artwork_types',
      blank=True, null=True,
      help_text=_("a related OCP context EconomicAgent")
    )
    ocpArtworkType_unit_type = TreeForeignKey(
        Unit_Type,
        on_delete=models.CASCADE,
        verbose_name=_('general unit_type'),
        related_name='ocp_artwork_types',
        blank=True, null=True,
        help_text=_("a related General Unit Type")
    )

    objects = Ocp_Artwork_TypeManager()

    class Meta:
      verbose_name= _(u'Type of General Artwork/Resource')
      verbose_name_plural= _(u'o-> Types of General Artworks/Resources')

    def __unicode__(self):
      try:
        if self.resource_type:
          return self.name+' <' #+'  ('+self.resource_type.name+')'
      except:
        return self.name+' !!'
      if self.facet_value:
          return self.name+':'#  ('+self.facet_value.value+')'
      elif self.facet:
          return self.name+'  ('+self.facet.name+')'
      else:
          return self.name




class Ocp_Skill_TypeManager(TreeManager):

    def update_from_general(self): # TODO, if general.Job changes independently, update the subclass with new items
        return False


class Ocp_Skill_Type(Job):
    job = models.OneToOneField(
      Job,
      on_delete=models.CASCADE,
      primary_key=True,
      parent_link=True
    )
    resource_type = models.OneToOneField(
      EconomicResourceType,
      on_delete=models.CASCADE,
      verbose_name=_('ocp resource_type'),
      related_name='ocp_skill_type',
      blank=True, null=True,
      help_text=_("a related OCP ResourceType")
    )
    facet = models.OneToOneField( # only root nodes can have unique facets
      Facet,
      on_delete=models.CASCADE,
      verbose_name=_('ocp facet'),
      related_name='ocp_skill_type',
      blank=True, null=True,
      help_text=_("a related OCP Facet")
    )
    facet_value = models.OneToOneField( # only some tree folders can have unique facet_values
      FacetValue,
      on_delete=models.CASCADE,
      verbose_name=_('ocp facet_value'),
      related_name='ocp_skill_type',
      blank=True, null=True,
      help_text=_("a related OCP FacetValue")
    )
    ocp_artwork_type = TreeForeignKey(
      Ocp_Artwork_Type,
      on_delete=models.CASCADE,
      verbose_name=_('general artwork_type'),
      related_name='ocp_skill_types',
      blank=True, null=True,
      help_text=_("a related General Artwork Type")
    )

    objects = Ocp_Skill_TypeManager()

    class Meta:
      verbose_name= _(u'Type of General Skill Resources')
      verbose_name_plural= _(u'o-> Types of General Skill Resources')

    def __unicode__(self):
      if self.resource_type:
        if self.ocp_artwork_type and not self.ocp_artwork_type.name.lower() in self.get_gerund().lower():
          return self.get_gerund()+' - '+self.ocp_artwork_type.name.lower()+' <'
        else:
          return self.get_gerund()+' <' #name #+'  ('+self.resource_type.name+')'
      elif self.facet_value:
        return self.get_gerund() #+'  ('+self.facet_value.value+')'
      else:
        return self.get_gerund()

    def get_gerund(self):
      if self.gerund:
        return self.gerund.title()
      elif self.verb:
        return self.verb
      else:
        return self.name


class Ocp_Record_TypeManager(TreeManager):

    def update_from_general(self): # TODO, if general.Record_Type changes independently, update the subclass with new items
        return False


class Ocp_Record_Type(Record_Type):
    ocpRecordType_record_type = models.OneToOneField(
        Record_Type,
        on_delete=models.CASCADE,
        primary_key=True,
        parent_link=True
    )
    exchange_type = models.OneToOneField(
        ExchangeType,
        on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_('ocp exchange type'),
        related_name='ocp_record_type'
    )
    ocpRecordType_ocp_artwork_type = TreeForeignKey(
        Ocp_Artwork_Type,
        on_delete=models.CASCADE,
        verbose_name=_('general artwork_type'),
        related_name='ocp_record_types',
        blank=True, null=True,
        help_text=_("a related General Artwork Type")
    )
    ocp_skill_type = TreeForeignKey(
        Ocp_Skill_Type,
        on_delete=models.CASCADE,
        verbose_name=_('general skill_type'),
        related_name='ocp_record_types',
        blank=True, null=True,
        help_text=_("a related General Skill Type")
    )

    objects = Ocp_Record_TypeManager()

    class Meta:
        verbose_name= _(u'Type of General Record')
        verbose_name_plural= _(u'o-> Types of General Records')

    def __unicode__(self):
      if self.exchange_type:
        return self.name+' <' #+'  ('+self.resource_type.name+')'
      else:
        return self.name

    def context_agent(self):
      if self.exchange_type:
        if self.exchange_type.context_agent:
          return self.exchange_type.context_agent
      return None

    def get_ocp_resource_types(self, transfer_type=None):
        answer = None
        if transfer_type:
          if transfer_type.inherit_types:
            answer = Ocp_Artwork_Type.objects.filter(lft__gte=self.ocpRecordType_ocp_artwork_type.lft, rght__lte=self.ocpRecordType_ocp_artwork_type.rght, tree_id=self.ocpRecordType_ocp_artwork_type.tree_id).order_by('lft')
          else:
            facetvalues = [ttfv.facet_value.value for ttfv in transfer_type.facet_values.all()]
            Mtyp = False
            Ntyp = False
            try:
                Mtyp = Artwork_Type.objects.get(clas="Material")
                Ntyp = Artwork_Type.objects.get(clas="Nonmaterial")
            except:
                pass

            Rids = []
            Sids = []
            for fv in facetvalues:
                try:
                    gtyps = Ocp_Artwork_Type.objects.filter(facet_value__value=fv)
                    for gtyp in gtyps:
                      subids = [typ.id for typ in Ocp_Artwork_Type.objects.filter(lft__gt=gtyp.lft, rght__lt=gtyp.rght, tree_id=gtyp.tree_id)]
                      Rids += subids+[gtyp.id]
                except:
                    pass

                try:
                    gtyp = Ocp_Skill_Type.objects.get(facet_value__value=fv)
                    subids = [typ.id for typ in Ocp_Skill_Type.objects.filter(lft__gt=gtyp.lft, rght__lt=gtyp.rght, tree_id=gtyp.tree_id)]
                    Sids += subids+[gtyp.id]
                except:
                    pass

            for facet in transfer_type.facets():
                if facet.clas == "Material_Type" or facet.clas == "Nonmaterial_Type" or facet.clas == "Currency_Type":
                    if Rids:
                        Rtys = Ocp_Artwork_Type.objects.filter(id__in=Rids)#.order_by('tree_id','lft')
                        #if Nids: # and Ntyp:
                        #    Mtys = Artwork_Type.objects.filter(id__in=Nids+Mids) #+[Ntyp.id, Mtyp.id])
                        answer = Rtys
                    else:
                        answer = Ocp_Artwork_Type.objects.all()

                elif facet.clas == "Skill_Type":
                    if Sids:
                        Stys = Ocp_Skill_Type.objects.filter(id__in=Sids)
                        #if Mids: # and Mtyp:
                        #    Ntys = Artwork_Type.objects.filter(id__in=Mids+Nids) #+[Ntyp.id, Mtyp.id])
                        answer = Stys
                    else:
                        answer = Ocp_Skill_Type.objects.all()

                #elif facet.clas == "Currency_Type":
                #    pass
                else:
                    pass

        if not answer:
          return Ocp_Artwork_Type.objects.none()

        return answer



from general.models import Unit as Gen_Unit

class Ocp_Unit_TypeManager(TreeManager):

    def update_from_general(self): # TODO, if general.Unit_Type changes independently, update the subclass with new items
        return False


class Ocp_Unit_Type(Unit_Type):
    ocpUnitType_unit_type = models.OneToOneField(
        Unit_Type,
        on_delete=models.CASCADE,
        primary_key=True,
        parent_link=True
    )
    ocpUnitType_ocp_unit =  models.OneToOneField(
        Unit,
        on_delete=models.CASCADE,
        verbose_name=_('ocp unit'),
        related_name='ocp_unit_type',
        blank=True, null=True,
        help_text=_("a related OCP Unit")
    )
    ocpUnitType_unit = models.OneToOneField(
        Gen_Unit,
        on_delete=models.CASCADE,
        verbose_name=_('general unit'),
        related_name='ocp_unit_type',
        blank=True, null=True,
        help_text=_("a related General Unit")
    )

    objects = Ocp_Unit_TypeManager()

    class Meta:
        verbose_name= _(u'Type of General Unit')
        verbose_name_plural= _(u'o-> Types of General Units')

    def __unicode__(self):
      if self.children.count():
        if self.ocpUnitType_ocp_unit:
          return self.name+': <' #+'  ('+self.resource_type.name+')'
        else:
          return self.name+': '
      else:
        if self.ocpUnitType_ocp_unit:
          return self.name+' <' #+'  ('+self.resource_type.name+')'
        else:
          return self.name


from django.db.models.signals import post_migrate

def create_unit_types(**kwargs):
    uts = Unit_Type.objects.all()
    outs = Ocp_Unit_Type.objects.all()
    if uts.count() > outs.count():
      for ut in uts:
        if not outs or not ut in outs:
          out = Ocp_Unit_Type(ut) # not works good, TODO ... now only via sqlite3 .read ocp_unit_types1.sql
          #out.save()
          print "created unit type: "+out.name
    else:
      print "error creating unit types: "+uts.count()

#post_migrate.connect(create_unit_types)

def rebuild_trees(**kwargs):
    uts = Unit_Type.objects.rebuild()
    print "rebuilded Unit_Type"

#post_migrate.connect(rebuild_trees)
