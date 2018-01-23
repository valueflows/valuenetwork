#
# Graphene schema for exposing EconomicAgent and related models
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

import graphene
from valuenetwork.valueaccounting.models import EconomicAgent, AgentUser, Location
from valuenetwork.api.models import formatAgent, formatAgentList, Person
from valuenetwork.api.types.Agent import Agent, Person
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied, ValidationError

class Query(graphene.AbstractType):

    my_agent = graphene.Field(Agent)

    agent = graphene.Field(Agent,
                           id=graphene.Int())

    all_agents = graphene.List(Agent)

    user_is_authorized_to_create = graphene.Boolean(scope_id=graphene.Int())


    def resolve_my_agent(self, args, *rargs):
        agentUser = AgentUser.objects.filter(user=self.user).first()
        agent = agentUser.agent
        if agent:
            return formatAgent(agent)
        raise PermissionDenied("Cannot find requested agent")

    def resolve_agent(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return formatAgent(agent)
        raise PermissionDenied("Cannot find requested agent")

    def resolve_all_agents(self, args, context, info):
        return formatAgentList(EconomicAgent.objects.all())

    def resolve_user_is_authorized_to_create(self, args, context, info):
        context_agent_id = args.get('contest_agent_id')
        user_agent = AgentUser.objects.filter(user=self.user).first().agent
        return user_agent.is_authorized(context_agent_id=context_agent_id)

'''
class CreateAgent(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        action = graphene.String(required=True)
        note = graphene.String(required=False)


    agent = graphene.Field(lambda: Agent)

    @classmethod
    def mutate(cls, root, args, context, info):
        action = args.get('action')
        input_of_id = args.get('input_of_id')
        output_of_id = args.get('output_of_id')
        provider_id = args.get('provider_id')
        receiver_id = args.get('receiver_id')
        scope_id = args.get('scope_id')
        committed_resource_classified_as_id = args.get('committed_resource_classified_as_id')
        involves_id = args.get('involves_id')
        committed_numeric_value = args.get('committed_numeric_value')
        committed_unit_id = args.get('committed_unit_id')
        planned_start = args.get('planned_start')
        due = args.get('due')
        note = args.get('note')
        plan_id = args.get('plan_id')
        is_plan_deliverable = args.get('is_plan_deliverable')
        #for_plan_deliverable_id = args.get('for_plan_deliverable_id')

        if output_of_id or input_of_id:
            if not plan_id:
                raise ValidationError("Process related commitments must be part of a plan.")
        event_type = EventType.objects.convert_action_to_event_type(action)
        if not note:
            note = ""
        due = datetime.datetime.strptime(due, '%Y-%m-%d').date()
        if planned_start:
            planned_start = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
        if scope_id:
            scope = EconomicAgent.objects.get(pk=scope_id)
        else:
            scope = None
        if provider_id:
            provider = EconomicAgent.objects.get(pk=provider_id)
        else:
            provider = None

        agent = CommitmentProxy(
            event_type = event_type,
            process = process,
            from_agent = provider,
            to_agent = receiver,
            resource_type = resource_classified_as,
            resource = committed_resource,
            quantity = Decimal(committed_numeric_value),
            unit_of_quantity = committed_unit,
            start_date = planned_start,
            due_date = due,
            description=note,
            context_agent=scope,
            order=deliverable_for,
            independent_demand=plan,
            order_item=None, #order_item,
            created_by=context.user,
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = user_agent.is_authorized(object_to_mutate=agent)
        if is_authorized:
            agent.save_api()
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreateAgent(agent=agent)
'''

class UpdatePerson(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        image = graphene.String(required=False)
        primary_location_id = graphene.Int(required=False)
        note = graphene.String(required=False)

    person = graphene.Field(lambda: Person)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')

        agent = EconomicAgent.objects.get(pk=id)
        if agent:
            if note:
                agent.description = note
            if image:
                agent.photo_url = image
            if name:
                agent.name = name
            if primary_location_id:
                agent.primary_location = Location.objects.get(pk=primary_location_id)

            user_agent = AgentUser.objects.get(user=context.user).agent
            is_authorized = user_agent.is_authorized(object_to_mutate=agent)
            if is_authorized:
                agent.save()
            else:
                raise PermissionDenied('User not authorized to perform this action.')

        return UpdatePerson(person=formatAgent(agent))

'''
class DeleteAgent(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    agent = graphene.Field(lambda: Commitment)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        agent = EconomicAgent.objects.get(pk=id)
        if agent:
            if agent.is_deletable():
                user_agent = AgentUser.objects.get(user=context.user).agent
                is_authorized = user_agent.is_authorized(object_to_mutate=commitment)
                if is_authorized:
                    agent.delete()
                else:
                    raise PermissionDenied('User not authorized to perform this action.')
            else:
                raise PermissionDenied("Commitment has fulfilling events so cannot be deleted.")

        return DeleteAgent(agent=agent)
'''