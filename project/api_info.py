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
    - `/web/api/` - Gestion des inventaires (Web)
    - `/mobile/api/` - APIs mobiles (Authentification, Synchronisation, Comptage)
    - `/masterdata/api/` - Données de référence (Entrepôts, Emplacements, Produits)
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
        {
            'url': 'https://api.smatch.com',
            'description': 'Serveur de production'
        },
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
        },
        {
            'name': 'Authentification Mobile',
            'description': 'APIs d\'authentification pour l\'application mobile'
        },
        {
            'name': 'Synchronisation Mobile',
            'description': 'APIs de synchronisation des données pour l\'application mobile'
        },
        {
            'name': 'Comptage Mobile',
            'description': 'APIs de gestion des comptages pour l\'application mobile'
        },
        {
            'name': 'Utilisateur Mobile',
            'description': 'APIs de gestion des utilisateurs et données utilisateur pour mobile'
        },
        {
            'name': 'Assignment Mobile',
            'description': 'APIs de gestion des assignments pour l\'application mobile'
        }
    ]
} 