"""Gestionnaire d'exceptions unifié de l'API (`REST_FRAMEWORK['EXCEPTION_HANDLER']`).

Toute réponse d'erreur (4xx/5xx) a le même corps :

    {"code": "validation_error", "message": "...", "champs": {"lines[1].quantity": ["..."]}}

- `code` : valeur stable de `ErrorCode` — c'est le contrat, le front décide
  sur lui, jamais sur le texte.
- `message` : français, destiné à l'utilisateur final.
- `champs` : toujours présent ; chemins en notation TanStack Form (liste →
  `[i]`, objet → `.clé`) pour que le front rattache l'erreur au bon champ
  sans conversion. `non_field_errors` va dans `message`, pas ici.
"""

import logging

from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.core.errors import DEFAULT_MESSAGES, ErrorCode
from apps.core.exceptions import ApiError

logger = logging.getLogger(__name__)

# Ordre significatif : la première classe qui correspond gagne.
_CODE_BY_EXCEPTION = [
    (ValidationError, ErrorCode.VALIDATION_ERROR),
    (ParseError, ErrorCode.PARSE_ERROR),
    (NotAuthenticated, ErrorCode.NOT_AUTHENTICATED),
    (PermissionDenied, ErrorCode.PERMISSION_DENIED),
    ((NotFound, Http404), ErrorCode.NOT_FOUND),
    (MethodNotAllowed, ErrorCode.METHOD_NOT_ALLOWED),
    (Throttled, ErrorCode.THROTTLED),
]


def _is_login_view(view):
    # Import local : `apps.accounts.views` importe des modèles, ce module est
    # chargé tôt (settings) et ne doit pas en dépendre à l'import.
    from apps.accounts.views import LoggingTokenObtainPairView

    return isinstance(view, LoggingTokenObtainPairView)


def _error_code(exc, view):
    if isinstance(exc, ApiError):
        return exc.code
    if isinstance(exc, AuthenticationFailed):
        # simplejwt lève `AuthenticationFailed` pour des identifiants refusés
        # à la connexion comme pour un jeton invalide ailleurs : seule la vue
        # permet de les distinguer.
        return ErrorCode.INVALID_CREDENTIALS if _is_login_view(view) else ErrorCode.TOKEN_INVALID
    for exc_class, code in _CODE_BY_EXCEPTION:
        if isinstance(exc, exc_class):
            return code
    return ErrorCode.BAD_REQUEST  # autre 4xx DRF (406, 415...), statut d'origine conservé


def _flatten(detail, path, champs):
    """`{'lines': [{}, {'quantity': ['x']}]}` → `{'lines[1].quantity': ['x']}`."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            # `ListField`/`DictField` indexent leurs erreurs par position (`{0: [...]}`).
            if isinstance(key, int) or str(key).isdigit():
                child = f'{path}[{key}]'
            else:
                child = f'{path}.{key}' if path else str(key)
            _flatten(value, child, champs)
    elif isinstance(detail, list) and detail and all(isinstance(d, (dict, list)) for d in detail):
        for index, value in enumerate(detail):
            _flatten(value, f'{path}[{index}]', champs)
    elif isinstance(detail, list):
        if detail:
            champs[path] = [str(d) for d in detail]
    else:
        champs[path] = [str(detail)]


def _validation_body(detail):
    """`(message, champs)` d'une `ValidationError` : les erreurs globales
    (liste racine, `non_field_errors`) deviennent le message."""
    if isinstance(detail, list):
        return ' '.join(str(d) for d in detail), {}
    detail = dict(detail)
    global_errors = detail.pop('non_field_errors', [])
    champs = {}
    _flatten(detail, '', champs)
    message = ' '.join(str(d) for d in global_errors)
    return message or DEFAULT_MESSAGES[ErrorCode.VALIDATION_ERROR], champs


def _message(data, code):
    if isinstance(data, dict) and 'detail' in data:
        return str(data['detail'])
    if isinstance(data, list) and data:
        return ' '.join(str(d) for d in data)
    if isinstance(data, str) and data:
        return data
    return DEFAULT_MESSAGES[code]


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        # Exception Python non prévue : trace dans les logs, jamais dans la
        # réponse (même en DEBUG).
        logger.exception("Exception non gérée dans l'API", exc_info=exc)
        transaction.set_rollback(True)
        return Response(
            {
                'code': ErrorCode.SERVER_ERROR,
                'message': DEFAULT_MESSAGES[ErrorCode.SERVER_ERROR],
                'champs': {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _error_code(exc, context.get('view'))
    if isinstance(exc, ValidationError):
        message, champs = _validation_body(response.data)
    else:
        message, champs = _message(response.data, code), {}

    # On garde la réponse de DRF (statut, `Retry-After`, `WWW-Authenticate`)
    # et on ne remplace que le corps.
    response.data = {'code': code, 'message': message, 'champs': champs}
    return response
