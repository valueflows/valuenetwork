#
# Base class for all EconomicAgent types
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene

#from valuenetwork.valueaccounting.models import EconomicAgent

class AgentBaseType(graphene.Interface):
    id = graphene.String()
    name = graphene.String()
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')
