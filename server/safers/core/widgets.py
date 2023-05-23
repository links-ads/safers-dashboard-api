import json
from collections import OrderedDict

from django import forms
from django.forms import widgets


class DataListWidget(forms.TextInput):
    """
    Renders a <datalist> element; a TextInput w/ an embedded dropdown.
    """
    def __init__(self, options, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        self._options = options
        self.attrs.update({
            "list": f"datalist-{self._name}",
            "size": 30,  # TODO: ALLOW SIZE TO HAVE A DEFAULT VALUE
        })

    def render(self, name, value, attrs=None, renderer=None):
        rendered_html = super().render(name, value, attrs=attrs)
        data_list = f"<datalist id='datalist-{self._name}'>"
        for option in self._options:
            data_list += f"<option value='{option}'>"
        data_list += "</datalist>"

        return rendered_html + data_list


class JSONWidget(widgets.Textarea):
    """
    renders JSON in a pretty (indented/sorted) way
    """
    def __init__(self, attrs=None):
        default_attrs = {
            # make things a bit bigger
            "cols": "80",
            "rows": "20",
            "class": "vLargeTextField",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value) -> str:
        try:
            value = json.dumps(
                json.loads(value, object_pairs_hook=OrderedDict),
                indent=2,
            )
        except Exception:
            pass
        return value