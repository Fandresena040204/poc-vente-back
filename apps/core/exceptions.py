"""Exceptions métier qui portent un code d'erreur stable (voir `errors.py`).

Le code métier lève (`raise InvalidTransition()`), il ne construit jamais une
`Response` d'erreur à la main : `exception_handler.py` met le corps au format
commun.
"""

from rest_framework.exceptions import APIException

from apps.core.errors import DEFAULT_MESSAGES, ErrorCode


class ApiError(APIException):
    code = ErrorCode.SERVER_ERROR
    status_code = 500

    def __init__(self, message=None):
        super().__init__(detail=message or DEFAULT_MESSAGES[self.code])


class InvalidTransition(ApiError):
    """Statut actuel hors du `from` de l'étape — souvent parce qu'un autre
    utilisateur a fait avancer l'entité entre-temps : 409, pas 400."""

    code = ErrorCode.INVALID_TRANSITION
    status_code = 409


class UnknownStep(ApiError):
    """Étape absente de la déclaration du workflow."""

    code = ErrorCode.UNKNOWN_STEP
    status_code = 404
