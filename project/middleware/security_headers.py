"""
Middleware pour ajouter des headers de sécurité HTTP.
"""


class SecurityHeadersMiddleware:
    """
    Middleware qui ajoute des headers de sécurité HTTP à toutes les réponses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)
    
    def process_response(self, request, response):
        """
        Ajoute les headers de sécurité à la réponse.
        """
        # Content Security Policy (CSP) - à adapter selon vos besoins
        # response['Content-Security-Policy'] = "default-src 'self'"
        
        # Permissions Policy (anciennement Feature Policy)
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=()'
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # X-Content-Type-Options (déjà géré par SECURE_CONTENT_TYPE_NOSNIFF mais on l'ajoute explicitement)
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection (déjà géré par SECURE_BROWSER_XSS_FILTER mais on l'ajoute explicitement)
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response

