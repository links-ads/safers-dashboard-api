from django import forms


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
