from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AccountsConfig(AppConfig):
    name = "game_portal.accounts"
    verbose_name = _("accounts")

    def ready(self):
        import game_portal.accounts.signals
