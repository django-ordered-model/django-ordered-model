from django.db.models.signals import post_delete
from django.dispatch import receiver
from ordered_model.models import OrderedModelBase
from django.db.models import F


@receiver(post_delete, dispatch_uid="on_ordered_model_delete")
def on_ordered_model_delete(sender, instance, **kwargs):
    """
    This signal makes sure that when an OrderedModelBase is deleted via cascade database deletes, the models
    keep order.
    """

    """
    We're only interested in subclasses of OrderedModelBase.
    We want to be able to support 'extra_kwargs' on the delete()
    method, which we can't do if we do all our work in the signal. We add a property to signal whether or not
    the model's .delete() method was called, because if so - we don't need to do any more work.
    """
    if not issubclass(sender, OrderedModelBase):
        return
    if getattr(instance, "_was_deleted_via_delete_method", False):
        return

    extra_update = kwargs.get("extra_update", None)

    # Copy of upshuffle logic from OrderedModelBase.delete
    qs = instance.get_ordering_queryset()
    extra_update = {} if extra_update is None else extra_update
    qs.above_instance(instance).decrease_order(**extra_update)
