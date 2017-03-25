from django.contrib import admin
from work.models import *
from valuenetwork.valueaccounting.actions import export_as_csv
#from django_mptt_admin.admin import DjangoMpttAdmin

admin.site.add_action(export_as_csv, 'export_selected objects')

class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'agent', )

admin.site.register(MembershipRequest, MembershipRequestAdmin)

class SkillSuggestionAdmin(admin.ModelAdmin):
    list_display = ('skill', 'suggested_by', 'suggestion_date', 'state', 'resource_type', )

admin.site.register(SkillSuggestion, SkillSuggestionAdmin)

class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'project', 'agent',)
    #fields = ('name', 'state', 'project', 'agent',)
    #list_editable = ['state',]

admin.site.register(JoinRequest, JoinRequestAdmin)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('agent', 'visibility', 'joining_style', 'fobi_slug',)

admin.site.register(Project, ProjectAdmin)

class NewFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'deployment_date', 'description', 'url',)

admin.site.register(NewFeature, NewFeatureAdmin)

#this won't work unless I can set the created_by field from django admin
#class InvoiceNumberAdmin(admin.ModelAdmin):
#    list_display = ('invoice_number', 'member', 'description', 'created_by',)

#admin.site.register(InvoiceNumber, InvoiceNumberAdmin)

from mptt.admin import MPTTModelAdmin
#from mptt.fields import TreeForeignKey, TreeManyToManyField

class Ocp_Type_RecordAdmin(MPTTModelAdmin):
  model = Ocp_Record_Type
  list_display = ['name', 'clas', 'exchange_type', 'context_agent', 'ocp_artwork_type', 'ocp_skill_type']
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == 'parent':
      try:
        typ = Record_Type.objects.get(clas='ocp_record')
        kwargs['queryset'] = Record_Type.objects.filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      except:
        pass
    return super(Ocp_Type_RecordAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Ocp_Record_Type, Ocp_Type_RecordAdmin)



from general.models import Artwork_Type

class Ocp_Type_Artwork_Admin(MPTTModelAdmin):
  model = Ocp_Artwork_Type
  list_display = ['name', 'clas', 'facet', 'facet_value', 'resource_type', 'context_agent', 'unit_type']
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == 'parent':
      try:
        typ = Artwork_Type.objects.get(clas='Resource')
        kwargs['queryset'] = Artwork_Type.objects.filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      except:
        pass
    return super(Ocp_Type_Artwork_Admin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Ocp_Artwork_Type, Ocp_Type_Artwork_Admin)


class Ocp_Type_Skill_Admin(MPTTModelAdmin):
  model = Ocp_Skill_Type
  list_display = ['name', 'verb', 'gerund', 'clas', 'facet', 'facet_value', 'resource_type']

admin.site.register(Ocp_Skill_Type, Ocp_Type_Skill_Admin)


class Ocp_Type_Unit_Admin(MPTTModelAdmin):
  model = Ocp_Unit_Type
  list_display = ['name', 'clas', 'unit', 'ocpUnitType_ocp_unit']
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == 'parent':
      try:
        typ = Artwork_Type.objects.get(clas='Unit')
        kwargs['queryset'] = Artwork_Type.objects.filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      except:
        pass
    return super(Ocp_Type_Unit_Admin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Ocp_Unit_Type, Ocp_Type_Unit_Admin)
