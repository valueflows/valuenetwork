#
# Graphene schema for exposing Notification models

import graphene

from pinax.notifications.models import NoticeSetting, NoticeType
from valuenetwork.api.types.NotificationSetting import NotificationSetting, NotificationType


class Query(graphene.AbstractType):

    notification_setting = graphene.Field(NotificationSetting,
                                          id=graphene.Int())

    all_notification_settings = graphene.List(NotificationSetting)

    notification_type = graphene.Field(NotificationType,
                                       id=graphene.Int())

    all_notification_types = graphene.List(NotificationType)

    def resolve_notification_setting(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            notice = NoticeSetting.objects.get(pk=id)
            if notice:
                return notice
        return None

    def resolve_all_notification_settings(self, args, context, info):
        return NoticeSetting.objects.all()

    def resolve_notification_type(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            notice = NoticeType.objects.get(pk=id)
            if notice:
                return notice
        return None

    def resolve_all_notification_types(self, args, context, info):
        return NoticeType.objects.all()
