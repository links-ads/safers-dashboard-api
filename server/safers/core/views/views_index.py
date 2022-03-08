from django.contrib.auth import get_user_model

from django.views.generic import TemplateView

User = get_user_model()

class IndexView(TemplateView):

    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["n_users"] = User.objects.count()
        return context_data