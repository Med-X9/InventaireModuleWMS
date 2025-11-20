import logging
import json
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger('actions')


class ActionLoggingMiddleware:
    """
    Middleware qui journalise les actions des utilisateurs authentifiés.

    - Logge l'utilisateur, le path, la méthode HTTP, le code de statut
    - Filtre les champs sensibles (password, token, etc.) dans le body
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code exécuté avant la vue
        response = self.get_response(request)

        # Code exécuté après la vue
        if request.user.is_authenticated:
            try:
                # Récupérer les informations de la requête
                action_info = {
                    'user': request.user.username,
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'timestamp': timezone.now().isoformat(),
                }

                # Ajouter les données de la requête si c'est une méthode POST/PUT/PATCH
                # ⚠️ Ne pas logger les données sensibles (mots de passe, tokens, etc.)
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        data = json.loads(request.body.decode('utf-8') or '{}')
                        # Filtrer les champs sensibles
                        sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key', 'refresh']
                        cleaned_data = {}
                        for key, value in data.items():
                            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                                cleaned_data[key] = '***REDACTED***'
                            else:
                                cleaned_data[key] = value
                        action_info['data'] = cleaned_data
                    except Exception:
                        # Pour les données de formulaire, filtrer aussi
                        form_data = dict(request.POST)
                        sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key', 'refresh']
                        cleaned_data = {}
                        for key, value in form_data.items():
                            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                                cleaned_data[key] = '***REDACTED***'
                            else:
                                cleaned_data[key] = value
                        action_info['data'] = cleaned_data

                # Logger l'action
                logger.info(
                    'Action effectuée',
                    extra={
                        'user': request.user.username,
                        'action': f'{request.method} {request.path}',
                        'details': json.dumps(action_info, cls=DjangoJSONEncoder)
                    }
                )
            except Exception as e:
                logger.error(f'Erreur lors du logging: {str(e)}')

        return response


