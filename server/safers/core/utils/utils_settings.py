from django.apps import apps
from django.conf import LazySettings
from django.core.exceptions import AppRegistryNotReady, ImproperlyConfigured
from django.utils.functional import LazyObject, empty


class DynamicSetting(object):
    """
    Allows a variable in DJANGO_SETTINGS_MODULE to be defined by a field in a SingletonMixin.
    Therefore, it can be used before any apps have been loaded.
    """
    def __init__(self, source, default_value):
        """
        Defines a settings variable as dynamic.  Usage is:
        >>> MY_SETTING = DynamicSetting("my_app.MyModel.my_setting", default=False)
        This will try to assign the value of my_app.MyModel.my_setting (which must be a singleton) to MY_SETTING.
        If anything goes wrong, it will fall back to the default value.
        """
        if len(source.split(".")) != 3:
            msg = f"Invalid DynamicSetting value; format is <app>.<model>.<attr>"
            raise ImproperlyConfigured(msg)
        self.source = source
        self.default_value = default_value

    @property
    def value(self):
        app_name, model_name, attr_name = self.source.split(".")
        try:
            model = apps.get_model(app_label=app_name, model_name=model_name)
            # model is a SingletonMixin, so pk will always equal 1
            instance, created = model.objects.get_or_create(pk=1)
            attr = getattr(instance, attr_name)
            if created and attr != self.default_value:
                attr = self.default_value
                setattr(instance, attr_name, attr)
                instance.save()
            return attr
        except AppRegistryNotReady:
            return self.default_value

    @classmethod
    def configure(cls):
        """
        Called once this app (and therefore, the django.conf app) is loaded.
        Patches the LazySettings.__getattr__ w/ a custom fn which checks to
        see if the attr is an instance of a DynamicSetting; if so, it returns
        the current value from the db.
        """
        def _new_getattr(instance, name):
            if instance._wrapped is empty:
                instance._setup(name)
            attr = getattr(instance._wrapped, name)
            if isinstance(attr, DynamicSetting):
                # if the attr is dynamic, return its computed value
                return attr.value
            instance.__dict__[name] = attr
            return attr

        # TODO: NOT SURE WHY USING TYPES DOESN'T WORK
        # setattr(LazySettings, "__getattr__", types.MethodType(_new_getattr, LazySettings))
        setattr(LazySettings, "__getattr__", _new_getattr)
