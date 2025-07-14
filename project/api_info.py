"""
Informations de l'API pour Swagger
"""

api_info = {
    'title': 'Inventaire Module WMS API',
    'description': """
    API pour la gestion d'inventaire avec différents modes de comptage.
    
    ## Fonctionnalités principales :
    - Gestion des inventaires
    - Comptages en vrac, par article, et image stock
    - Gestion des entrepôts et emplacements
    - Authentification JWT
    
    ## Authentification :
    Utilisez un token Bearer dans l'en-tête Authorization.
    Format : `Bearer <votre_token_jwt>`
    
    ## Endpoints principaux :
    - `/api/inventory/` - Gestion des inventaires
    - `/api/counting/` - Gestion des comptages
    - `/api/warehouse/` - Gestion des entrepôts
    - `/api/auth/` - Authentification
    """,
    'version': '1.0.0',
    'contact': {
        'name': 'SM@TCH',
        'email': 'support@smatch.com',
    },
    'license': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT',
    },
    'termsOfService': '',
    'servers': [
        # {
        #     'url': 'https://api.smatch.com',
        #     'description': 'Serveur de production'
        # },
        {
            'url': 'http://localhost:8000',
            'description': 'Serveur de développement'
        }
    ],
    'tags': [
        {
            'name': 'inventory',
            'description': 'Gestion des inventaires'
        },
        {
            'name': 'counting',
            'description': 'Gestion des comptages'
        },
        {
            'name': 'warehouse',
            'description': 'Gestion des entrepôts'
        },
        {
            'name': 'auth',
            'description': 'Authentification et autorisation'
        }
    ]
} 