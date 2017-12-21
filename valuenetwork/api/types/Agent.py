#
# EconomicAgent:A person or group or organization with economic agency.
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from django.db.models import Q
from valuenetwork.valueaccounting.models import EconomicAgent, EconomicResourceType
import valuenetwork.api.types as types
from valuenetwork.api.types.AgentRelationship import AgentRelationship, AgentRelationshipCategory, AgentRelationshipRole
from valuenetwork.api.models import Organization as OrganizationModel, Person as PersonModel, formatAgentList
import datetime


def _load_identified_agent(self):
    return EconomicAgent.objects.get(pk=self.id)

# Economic agent base type

class Agent(graphene.Interface):

    # fields common to all agent types

    id = graphene.String()
    name = graphene.String()
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    primary_location = graphene.Field(lambda: types.Place)

    owned_economic_resources = graphene.List(lambda: types.EconomicResource,
                                             category=types.EconomicResourceCategory(),
                                             resourceClassificationId=graphene.Int())

    agent_processes = graphene.List(lambda: types.Process,
                                    is_finished=graphene.Boolean())

    agent_plans = graphene.List(lambda: types.Plan,
                                is_finished=graphene.Boolean())

    agent_economic_events = graphene.List(lambda: types.EconomicEvent,
                                          latest_number_of_days=graphene.Int())

    agent_commitments = graphene.List(lambda: types.Commitment,
                                      latest_number_of_days=graphene.Int())

    agent_relationships = graphene.List(AgentRelationship,
                                        role_id=graphene.Int(),
                                        category=AgentRelationshipCategory())

    agent_roles = graphene.List(AgentRelationshipRole)

    agent_recipes = graphene.List(lambda: types.ResourceClassification)

    #agent_recipe_bundles = graphene.List(ResourceClassification)

    faircoin_address = graphene.String()


    def resolve_primary_location(self, args, *rargs):
        return self.primary_location

    def resolve_owned_economic_resources(self, args, context, info):
        type = args.get('category', types.EconomicResourceCategory.NONE)
        resource_class_id = args.get('resourceClassificationId', None)
        org = _load_identified_agent(self)
        resources = None
        if org:
            if type == types.EconomicResourceCategory.CURRENCY:
                resources = org.owned_currency_resources()
            elif type == types.EconomicResourceCategory.INVENTORY:
                resources = org.owned_inventory_resources()
            else:
                resources = org.owned_resources()
            if resource_class_id:
                rc = EconomicResourceType.objects.get(pk=resource_class_id)
                resources_temp = []
                for res in resources:
                    if res.resource_type == rc:
                        resources_temp.append(res)
                resources = resources_temp
        return resources

    # if an organization, this returns processes done in that context
    # if a person, this returns proceses the person has worked on
    def resolve_agent_processes(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            agent_processes = agent.all_processes()
            finished = args.get('is_finished', None)
            if finished != None:
                if not finished:
                    return agent_processes.filter(finished=False)
                else:
                    return agent_processes.filter(finished=True)
            else:
                return agent_processes
        return None

    # if an organization, this returns plans from that context
    # if a person, this returns plans the person has worked on
    def resolve_agent_plans(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            agent_plans = agent.all_plans()
            finished = args.get('is_finished', None)
            if finished != None:
                if not finished:
                    return agent_plans.filter(finished=False)
                else:
                    return agent_plans.filter(finished=True)
            else:
                return agent_plans
        return None

    # returns events where an agent is a provider, receiver, or scope agent, excluding exchange related events
    def resolve_agent_economic_events(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            days = args.get('latest_number_of_days', 0)
            if days > 0:
                events = agent.involved_in_events().filter(event_date__gte=(datetime.date.today() - datetime.timedelta(days=days)))
            else:
                events = agent.involved_in_events()
            events = events.exclude(event_type__name="Give").exclude(event_type__name="Receive")
            return events
        return None

    # returns commitments where an agent is a provider, receiver, or scope agent, excluding exchange related events
    def resolve_agent_commitments(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            days = args.get('latest_number_of_days', 0)
            if days > 0:
                commits = agent.involved_in_commitments().filter(
                    commitment_date__gte=(datetime.date.today() - datetime.timedelta(days=days)))
            else:
                commits = agent.involved_in_commitments()
            commits = commits.exclude(event_type__name="Give").exclude(event_type__name="Receive")
            return commits
        return None

    # returns relationships where an agent is a subject or object, optionally filtered by role category
    def resolve_agent_relationships(self, args, context, info):
        agent = _load_identified_agent(self)
        cat = args.get('category')
        role_id = args.get('role_id')
        if agent:
            assocs = agent.all_active_associations()
            filtered_assocs = []
            if role_id: #try the most specific first
                for assoc in assocs:
                    if assoc.association_type.id == role_id:
                        filtered_assocs.append(assoc)
                return filtered_assocs
            if cat:
                for assoc in assocs:
                    if assoc.association_type.category == cat:
                        filtered_assocs.append(assoc)
                return filtered_assocs
            else:
                return agent.all_active_associations()
        return None

    # returns relationships where an agent is a subject or object, optionally filtered by role category
    def resolve_agent_roles(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            return agent.active_association_types()
        return None

    def resolve_agent_recipes(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            return agent.recipes()
        return None

    def resolve_faircoin_address(self, args, *rargs):
        agent = _load_identified_agent(self)
        return agent.faircoin_address()

    # returns resource classifications that have a recipe, for this and parent agents
    #def resolve_agent_recipe_bundles(self, args, context, info):
    #    agent = _load_identified_agent(self)
    #    if agent:
    #        return agent.get_resource_type_lists()
    #    return None


# ValueFlows type for a Person (singular) Agent.
# In OCP there are no different properties, but some different behavior/filtering.

class Person(DjangoObjectType):
    class Meta:
        interfaces = (Agent, )
        model = PersonModel #EconomicAgent
        only_fields = ('id', 'name', 'image', 'primary_location')


# Organization - an Agent which is not a Person, and can be further classified from there

class Organization(DjangoObjectType):

    class Meta:
        interfaces = (Agent, )
        model = OrganizationModel #EconomicAgent
        only_fields = ('id', 'name', 'image', 'note', 'primary_location')
