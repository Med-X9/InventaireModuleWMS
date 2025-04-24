import logging
import json
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger('actions')

class ActionLoggingMiddleware:
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

                # Ajouter les données de la requête si c'est une méthode POST/PUT
                if request.method in ['POST', 'PUT']:
                    try:
                        action_info['data'] = json.loads(request.body.decode('utf-8'))
                    except:
                        action_info['data'] = dict(request.POST)

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