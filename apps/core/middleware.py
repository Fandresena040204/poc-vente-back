import threading

_thread_locals = threading.local()


def get_current_request():
    """Le `HttpRequest` de la requête en cours, dans ce thread — ou `None`
    hors d'une requête (shell, commande de gestion, test sans client API).

    DRF authentifie paresseusement : `request.user` n'est résolu (JWT
    décodé) que la première fois qu'on y accède, typiquement dans
    `HasRolePermission.has_permission`. À ce moment-là, `rest_framework.
    request.Request` réécrit aussi `.user` sur le `HttpRequest` Django
    d'origine (même objet que celui stocké ici) — donc par le temps qu'un
    signal de sauvegarde se déclenche (après les vérifications de
    permission), `get_current_request().user` est le bon utilisateur."""

    return getattr(_thread_locals, 'request', None)


class CurrentRequestMiddleware:
    """Garde une référence à la requête en cours dans un thread-local, pour
    que le journal d'audit (apps/core/audit.py) puisse savoir qui a fait
    une modification sans que chaque save() ait besoin de le préciser."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            return self.get_response(request)
        finally:
            _thread_locals.request = None
