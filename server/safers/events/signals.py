from django.db.models.signals import m2m_changed

from safers.events.models import Event


def event_alerts_changed_handler(sender, *args, **kwargs):
    """
    If an alert has been added/removed from an event then the event's geometry, etc. should be updated
    """
    action = kwargs["action"]
    instance = kwargs["instance"]
    reverse = kwargs["reverse"]
    if action in ["post_add", "post_remove", "post_clear"]:
        if not reverse:  # (event.alerts was changed)
            instance.recalculate_geometries(force_save=False)
            instance.recalculate_dates(force_save=True)
        else:  # (alert.events was changed)
            for event in instance.events.all():
                event.recalculate_geometries(force_save=False)
                event.recalculate_dates(force_save=True)


m2m_changed.connect(
    event_alerts_changed_handler,
    sender=Event.alerts.through,
    dispatch_uid="event_alerts_changed_handler",
)
