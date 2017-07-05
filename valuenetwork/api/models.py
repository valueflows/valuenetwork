from django.db import models

from valuenetwork.valueaccounting.models import Unit
from decimal import *

# Helpers for dealing with Agent polymorphism

def formatAgent(agent):
    if agent:
        if agent.agent_type.party_type == "individual":
            return Person(
                id=agent.id,
                name = agent.name,
                note = agent.description,
                image = agent.image)
        else:
            return Organization(
                id=agent.id,
                name = agent.name,
                note = agent.description,
                image = agent.image,
                is_context = agent.is_context,
                type = agent.agent_type)

def formatAgentList(agent_list):
    mixed_list = []
    for agent in agent_list:
        mixed_list.append(formatAgent(agent))
    return mixed_list

# Django model extensions for exposing OO type layer in Graphene (core doesn't really use inheritance)

class QuantityValue(models.Model):
    numeric_value = models.DecimalField(max_digits=8, decimal_places=2,
        default=Decimal("0.00"))
    unit = models.ForeignKey(Unit, blank=True, null=True,
        related_name="quantity_value_units")

    class Meta:
        managed = False


class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True)
    is_context = models.BooleanField(default=False)
    type = models.CharField(max_length=255)

    class Meta:
        managed = False


class Person(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True)
    is_context = models.BooleanField(default=False)
    type = models.CharField(max_length=255, default="Person")

    class Meta:
        managed = False
