#
# Graphene schema for exposing EconomicAgent and related models
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

import graphene
from valuenetwork.valueaccounting.models import EconomicAgent, AgentUser, Location, AgentType
from django.contrib.auth.models import User
from valuenetwork.api.models import formatAgent, formatAgentList, Person, Organization
from valuenetwork.api.types.Agent import Agent, Person, Organization
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

    ################## shameless hack for user registration ######################

    username_exists = graphene.Boolean(username=graphene.String())

    email_exists = graphene.Boolean(email=graphene.String())

    create_inactive_user = graphene.String(username=graphene.String(), 
                                           email=graphene.String(), 
                                           pswd=graphene.String())

    activate_user_create_person = graphene.String(username=graphene.String(),
                                                  name=graphene.String(),
                                                  image=graphene.String(),
                                                  phone=graphene.String(),
                                                  user_token=graphene.String())

    def resolve_username_exists(self, args, *rargs):
        username = args.get('username')
        usernames = User.objects.filter(username=username)
        if usernames:
            return True
        else:
            return False

    def resolve_email_exists(self, args, *rargs):
        email = args.get('email')
        emails = User.objects.filter(email=email)
        if emails:
            return True
        else:
            # may want to check here for the agent.email?
            return False

    def resolve_create_inactive_user(self, args, *rargs):
        username = args.get('username', None)
        email = args.get('email', None)
        pswd = args.get('pswd', None)
        if username and email and pswd:
            user = User.objects.create_user(username=username, email=email, password=pswd)
            user.is_active = False
            user.save()
            from django.template.loader import render_to_string
            from django.contrib.sites.models import Site
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from valuenetwork.tokens import signup_confirmation_token
            subject = 'Activate Your LearnDeep NRP Account'
            token = signup_confirmation_token.make_token(user)
            message = render_to_string('valueaccounting/signup/confirm_email.html', {
                'user': user,
                'domain': Site.objects.get_current().domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token,
                } )
            user.email_user(subject, message) #comment out to test without email set up, use returned token
            return token
        return None

    def resolve_activate_user_create_person(self, args, *rargs):
        token = args.get('user_token', None)
        username = args.get('username', None)
        name = args.get('name', None)
        image = args.get('image', None)
        phone = args.get('phone', None)
        if token is None:
            raise ValidationError("Invalid token.")
        if username is None:
            raise ValidationError("Invalid username.")
        if name is None:
            raise ValidationError("Name is required.")
        user = User.objects.get(username=username)
        if user is None:
            raise ValidationError("Invalid username.")
        from valuenetwork.tokens import signup_confirmation_token
        if signup_confirmation_token.check_token(user, token):
            user.is_active = True
            user.save()
        else:
            raise ValidationError("Invalid token.")
        at_person = AgentType.objects.get(party_type="individual")
        agent = EconomicAgent(
            nick = name,
            name = name,
            photo_url = image,
            phone_primary = phone,
            agent_type = at_person,
            email = user.email,
            created_by = user,
        )
        agent.save()
        au = AgentUser(
            agent = agent,
            user = user)
        au.save()
        return "User " + username + " activated, Agent and AgentUser created."

    ##################################################################

class CreateOrganization(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        image = graphene.String(required=False)
        primary_location_id = graphene.Int(required=False)
        primary_phone = graphene.String(required=False)
        email = graphene.String(required=False)
        note = graphene.String(required=False)
        type = graphene.String(required=True)

    organization = graphene.Field(lambda: Organization)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')
        primary_phone = args.get('primary_phone')
        email = args.get('email')
        type = args.get('type')

        if not note:
            note = ""
        if not image:
            image = ""
        if primary_location_id:
            location = Location.objects.get(pk=primary_location_id)
        else:
            location = None
        get_type = None
        if type:
            get_type = AgentType.objects.get(name=type)
        if not type:
            get_types = AgentType.objects.get(party_type="org")
            if get_types:
                get_type = get_types[0]

        agent = EconomicAgent(
            name = name,
            nick = name,
            agent_type = get_type,
            photo_url = image,
            description = note,
            primary_location = location,
            phone_primary = primary_phone,
            email = email,
            created_by=context.user,
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = user_agent.is_authorized(object_to_mutate=agent)
        if is_authorized:
            agent.save()
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreateOrganization(organization=formatAgent(agent))

class CreatePerson(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        image = graphene.String(required=False)
        primary_location_id = graphene.Int(required=False)
        primary_phone = graphene.String(required=False)
        email = graphene.String(required=False)
        note = graphene.String(required=False)
        type = graphene.String(required=False)

    person = graphene.Field(lambda: Person)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')
        primary_phone = args.get('primary_phone')
        email = args.get('email')
        type = args.get('type')

        if not note:
            note = ""
        if not image:
            image = ""
        if primary_location_id:
            location = Location.objects.get(pk=primary_location_id)
        else:
            location = None
        if type:
            get_type = AgentType.objects.get(name=type)
        if not type:
            get_types = AgentType.objects.filter(party_type="individual")
            get_type = get_types[0]

        agent = EconomicAgent(
            name = name,
            nick = name,
            agent_type = get_type,
            photo_url = image,
            description = note,
            primary_location = location,
            phone_primary = primary_phone,
            email = email,
            created_by=context.user,
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = user_agent.is_authorized(object_to_mutate=agent)
        if is_authorized:
            agent.save()
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreatePerson(person=formatAgent(agent))

class UpdatePerson(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        image = graphene.String(required=False)
        primary_location_id = graphene.Int(required=False)
        email = graphene.String(required=False)
        note = graphene.String(required=False)

    person = graphene.Field(lambda: Person)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')
        email = args.get('email')

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
            if email:
                agent.email = email

            user_agent = AgentUser.objects.get(user=context.user).agent
            is_authorized = user_agent.is_authorized(object_to_mutate=agent)
            if is_authorized:
                agent.save()
            else:
                raise PermissionDenied('User not authorized to perform this action.')

        return UpdatePerson(person=formatAgent(agent))

class UpdateOrganization(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        image = graphene.String(required=False)
        primary_location_id = graphene.Int(required=False)
        email = graphene.String(required=False)
        note = graphene.String(required=False)

    organization = graphene.Field(lambda: Organization)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')
        email = args.get('email')

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
            if email:
                agent.email = email

            user_agent = AgentUser.objects.get(user=context.user).agent
            is_authorized = user_agent.is_authorized(object_to_mutate=agent)
            if is_authorized:
                agent.save()
            else:
                raise PermissionDenied('User not authorized to perform this action.')

        return UpdateOrganization(organization=formatAgent(agent))


class DeletePerson(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    person = graphene.Field(lambda: Person)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        agent = EconomicAgent.objects.get(pk=id)
        if agent:
            if agent.is_deletable():
                user_agent = AgentUser.objects.get(user=context.user).agent
                #is_authorized = user_agent.is_authorized(context_agent_id=agent.id) TODO: what should be the rule?
                #if is_authorized:
                agent.delete()
                #else:
                #    raise PermissionDenied('User not authorized to perform this action.')
            else:
                raise PermissionDenied("Person has activity or relationships and cannot be deleted.")

        return DeletePerson(person=formatAgent(agent))

class DeleteOrganization(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    organization = graphene.Field(lambda: Organization)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        agent = EconomicAgent.objects.get(pk=id)
        if agent:
            if agent.is_deletable():
                user_agent = AgentUser.objects.get(user=context.user).agent
                #is_authorized = user_agent.is_authorized(context_agent_id=agent.id) TODO: what should be the rule?
                #if is_authorized:
                agent.delete()
                #else:
                #    raise PermissionDenied('User not authorized to perform this action.')
            else:
                raise PermissionDenied("Organization has activity or relationships and cannot be deleted.")

        return DeleteOrganization(organization=formatAgent(agent))

'''
class CreateInactiveUser(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(lambda: Person)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        primary_location_id = args.get('primary_location_id')
        primary_phone = args.get('primary_phone')
        email = args.get('email')
        type = args.get('type')

        if not note:
            note = ""
        if not image:
            image = ""
        if primary_location_id:
            location = Location.objects.get(pk=primary_location_id)
        else:
            location = None
        if type:
            get_type = AgentType.objects.get(name=type)
        if not type:
            get_types = AgentType.objects.filter(party_type="individual")
            get_type = get_types[0]

        agent = EconomicAgent(
            name = name,
            nick = name,
            agent_type = get_type,
            photo_url = image,
            description = note,
            primary_location = location,
            phone_primary = primary_phone,
            email = email,
            created_by=context.user,
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = user_agent.is_authorized(object_to_mutate=agent)
        if is_authorized:
            agent.save()
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreatePerson(person=formatAgent(agent))
'''
