"""Codes d'erreur stables et messages par défaut en français.

Une valeur publiée ne change plus de sens. Chaque code correspond à un
statut HTTP précis (voir `exception_handler.py`).
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Codes d'erreur stables pour le contrat API.

    - 4xx : erreurs client (validation, auth, permissions, pas trouvé, etc.)
    - 5xx : erreurs serveur
    """

    # 400
    VALIDATION_ERROR = 'validation_error'
    PARSE_ERROR = 'parse_error'
    BAD_REQUEST = 'bad_request'

    # 401
    NOT_AUTHENTICATED = 'not_authenticated'
    TOKEN_INVALID = 'token_invalid'
    INVALID_CREDENTIALS = 'invalid_credentials'

    # 403
    PERMISSION_DENIED = 'permission_denied'

    # 404
    NOT_FOUND = 'not_found'
    UNKNOWN_STEP = 'unknown_step'

    # 405
    METHOD_NOT_ALLOWED = 'method_not_allowed'

    # 409
    INVALID_TRANSITION = 'invalid_transition'
    IDEMPOTENCY_IN_PROGRESS = 'idempotency_in_progress'

    # 422
    IDEMPOTENCY_KEY_REUSED = 'idempotency_key_reused'

    # 429
    THROTTLED = 'throttled'

    # 500
    SERVER_ERROR = 'server_error'


# Messages par défaut en français (avec accents).
# Ils sont utilisés quand l'exception ne fournit pas de message explicite.
DEFAULT_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: 'Les données envoyées sont invalides.',
    ErrorCode.PARSE_ERROR: 'Le corps de la requête est illisible.',
    ErrorCode.BAD_REQUEST: 'Requête invalide.',
    ErrorCode.NOT_AUTHENTICATED: 'Authentification requise.',
    ErrorCode.TOKEN_INVALID: 'Jeton invalide ou expiré.',
    ErrorCode.INVALID_CREDENTIALS: 'Identifiants invalides.',
    ErrorCode.PERMISSION_DENIED: "Vous n'avez pas la permission nécessaire pour cette action.",
    ErrorCode.NOT_FOUND: 'Ressource introuvable.',
    ErrorCode.UNKNOWN_STEP: 'Étape de workflow inconnue.',
    ErrorCode.METHOD_NOT_ALLOWED: 'Méthode HTTP non autorisée.',
    ErrorCode.INVALID_TRANSITION: "Cette étape n'est pas possible depuis l'état actuel.",
    ErrorCode.IDEMPOTENCY_IN_PROGRESS: 'Une requête avec cette clé est déjà en cours.',
    ErrorCode.IDEMPOTENCY_KEY_REUSED: (
        "Cette clé d'idempotence a déjà été utilisée avec un corps différent."
    ),
    ErrorCode.THROTTLED: 'Trop de requêtes. Réessayez plus tard.',
    ErrorCode.SERVER_ERROR: 'Une erreur inattendue est survenue.',
}